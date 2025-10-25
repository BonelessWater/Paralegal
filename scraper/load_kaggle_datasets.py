#!/usr/bin/env python3
"""
Download Kaggle datasets and load them into PostgreSQL database
Requires: kaggle API credentials in ~/.kaggle/kaggle.json
"""

import os
import sys
import subprocess
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import configparser
from pathlib import Path
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Kaggle datasets to download
DATASETS = [
    {
        'name': 'VHA Hospitals Timely Care Data',
        'kaggle_path': 'thedevastator/vha-hospitals-timely-care-data',
        'category': 'healthcare',
        'description': 'Performance on Clinical Measures and Processes of Care'
    },
    {
        'name': 'CMS Medicare',
        'kaggle_path': 'bigquery/cms-medicare',
        'category': 'healthcare',
        'description': 'Hospital General Information (List of hospitals registered with Medicare)'
    },
    {
        'name': 'Veteran Employment Outcomes',
        'kaggle_path': 'mpwolke/cusersmarildownloadsvetcsv',
        'category': 'veterans',
        'description': 'Veteran Employment Outcomes (age)'
    },
    {
        'name': 'Veterans Lung Cancer Clinical Trial',
        'kaggle_path': 'harivpatel/veterans-lung-cancer-clinical-trial-dataset',
        'category': 'medical',
        'description': 'Survival data from the Veterans Administration Lung Cancer Trial'
    },
    {
        'name': 'US Hospital Locations',
        'kaggle_path': 'andrewmvd/us-hospital-locations',
        'category': 'healthcare',
        'description': 'Location and general data for 7596 hospitals'
    },
    {
        'name': 'RVLCDIP',
        'kaggle_path': 'abdellatifsassioui/rvlcdip',
        'category': 'document_ocr',
        'description': 'Document image dataset for classification'
    },
    {
        'name': 'FUNSD',
        'kaggle_path': 'aravindram11/funsdform-understanding-noisy-scanned-documents',
        'category': 'document_ocr',
        'description': 'Form Understanding Noisy Scanned Documents Dataset'
    },
    {
        'name': 'SROIE Dataset v2',
        'kaggle_path': 'urbikn/sroie-datasetv2',
        'category': 'document_ocr',
        'description': 'ICDAR 2019 SROIE dataset - scanned receipts OCR'
    },
    {
        'name': 'PubLayNet',
        'kaggle_path': 'captaintushar/publaynet-dataset',
        'category': 'document_ocr',
        'description': 'Document Layout Generation dataset'
    },
    {
        'name': 'Common Voice',
        'kaggle_path': 'mozillaorg/common-voice',
        'category': 'audio',
        'description': '500 hours of speech recordings with speaker demographics'
    },
    {
        'name': 'ICDAR 2019 MLT OCR',
        'kaggle_path': 'zubairalibhutto/mlt-19-ocr-dataset',
        'category': 'document_ocr',
        'description': 'Multilingual Scene Text Dataset from ICDAR 2019'
    },
    {
        'name': 'Denoising Dirty Documents',
        'kaggle_path': 'c/denoising-dirty-documents',
        'category': 'document_ocr',
        'description': 'Remove noise from printed text'
    },
    {
        'name': 'Noisy and Rotated Scanned Documents',
        'kaggle_path': 'sthabile/noisy-and-rotated-scanned-documents',
        'category': 'document_ocr',
        'description': 'Predictive model for recognizing angles of scanned documents'
    }
]


class KaggleDatasetLoader:
    """Download Kaggle datasets and load into PostgreSQL"""
    
    def __init__(self, config_path='config.ini', max_workers=8):
        """Initialize with database config"""
        config = configparser.ConfigParser()
        config.read(config_path)
        
        self.db_config = dict(config['database'])
        self.download_dir = Path('kaggle_datasets')
        self.download_dir.mkdir(exist_ok=True)
        self.max_workers = max_workers  # Parallel download threads
        self.db_lock = Lock()  # Thread-safe database access
        
        # Check Kaggle API credentials
        kaggle_json = Path.home() / '.kaggle' / 'kaggle.json'
        if not kaggle_json.exists():
            logger.error("Kaggle API credentials not found!")
            logger.error("Please download kaggle.json from https://www.kaggle.com/settings")
            logger.error(f"and place it at: {kaggle_json}")
            sys.exit(1)
    
    def get_db_connection(self):
        """Create database connection"""
        return psycopg2.connect(
            host=self.db_config['host'],
            port=self.db_config['port'],
            database=self.db_config['database'],
            user=self.db_config['username'],
            password=self.db_config['password']
        )
    
    def create_dataset_tables(self):
        """Create tables for storing dataset metadata"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE SCHEMA IF NOT EXISTS datasets;
            
            CREATE TABLE IF NOT EXISTS datasets.kaggle_datasets (
                id SERIAL PRIMARY KEY,
                name VARCHAR(500) NOT NULL,
                kaggle_path VARCHAR(500) UNIQUE NOT NULL,
                category VARCHAR(100),
                description TEXT,
                download_path TEXT,
                downloaded_at TIMESTAMP,
                file_count INTEGER,
                total_size_mb DECIMAL(10,2),
                status VARCHAR(50) DEFAULT 'pending',
                notes TEXT
            );
            
            CREATE TABLE IF NOT EXISTS datasets.dataset_files (
                id SERIAL PRIMARY KEY,
                dataset_id INTEGER REFERENCES datasets.kaggle_datasets(id) ON DELETE CASCADE,
                file_name VARCHAR(500),
                file_path TEXT,
                file_type VARCHAR(50),
                size_mb DECIMAL(10,2),
                rows_count INTEGER,
                columns_count INTEGER,
                loaded_to_table VARCHAR(200),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_kaggle_datasets_category 
                ON datasets.kaggle_datasets(category);
            CREATE INDEX IF NOT EXISTS idx_dataset_files_dataset_id 
                ON datasets.dataset_files(dataset_id);
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("✓ Dataset tables created")
    
    def download_dataset(self, dataset_info):
        """Download a Kaggle dataset"""
        logger.info(f"Downloading: {dataset_info['name']}...")
        
        dataset_path = self.download_dir / dataset_info['kaggle_path'].replace('/', '_')
        dataset_path.mkdir(exist_ok=True)
        
        try:
            # Download using Kaggle API
            cmd = [
                'kaggle', 'datasets', 'download',
                '-d', dataset_info['kaggle_path'],
                '-p', str(dataset_path),
                '--unzip'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✓ Downloaded: {dataset_info['name']}")
                return str(dataset_path)
            else:
                logger.error(f"✗ Failed to download {dataset_info['name']}: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"✗ Error downloading {dataset_info['name']}: {e}")
            return None
    
    def insert_dataset_metadata(self, dataset_info, download_path):
        """Insert dataset metadata into database (thread-safe)"""
        # Use lock for thread-safe database access
        with self.db_lock:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            try:
                # Count files and calculate size
                if download_path:
                    files = list(Path(download_path).rglob('*'))
                    file_count = len([f for f in files if f.is_file()])
                    total_size = sum(f.stat().st_size for f in files if f.is_file())
                    total_size_mb = total_size / (1024 * 1024)
                    status = 'downloaded'
                else:
                    file_count = 0
                    total_size_mb = 0
                    status = 'failed'
                
                cursor.execute("""
                    INSERT INTO datasets.kaggle_datasets 
                    (name, kaggle_path, category, description, download_path, 
                     downloaded_at, file_count, total_size_mb, status)
                    VALUES (%s, %s, %s, %s, %s, NOW(), %s, %s, %s)
                    ON CONFLICT (kaggle_path) 
                    DO UPDATE SET 
                        downloaded_at = NOW(),
                        download_path = EXCLUDED.download_path,
                        file_count = EXCLUDED.file_count,
                        total_size_mb = EXCLUDED.total_size_mb,
                        status = EXCLUDED.status
                    RETURNING id
                """, (
                    dataset_info['name'],
                    dataset_info['kaggle_path'],
                    dataset_info['category'],
                    dataset_info['description'],
                    download_path,
                    file_count,
                    total_size_mb,
                    status
                ))
                
                dataset_id = cursor.fetchone()[0]
                
                # Insert file information
                if download_path:
                    for file_path in Path(download_path).rglob('*'):
                        if file_path.is_file():
                            file_type = file_path.suffix.lower()
                            size_mb = file_path.stat().st_size / (1024 * 1024)
                            
                            cursor.execute("""
                                INSERT INTO datasets.dataset_files
                                (dataset_id, file_name, file_path, file_type, size_mb)
                                VALUES (%s, %s, %s, %s, %s)
                                ON CONFLICT (dataset_id, file_name) 
                                DO UPDATE SET 
                                    file_path = EXCLUDED.file_path,
                                    size_mb = EXCLUDED.size_mb
                            """, (
                                dataset_id,
                                file_path.name,
                                str(file_path),
                                file_type,
                                size_mb
                            ))
                
                conn.commit()
                logger.info(f"✓ Metadata saved for: {dataset_info['name']}")
                
            except Exception as e:
                logger.error(f"✗ Error saving metadata: {e}")
                conn.rollback()
            
            cursor.close()
            conn.close()
    
    def process_dataset(self, dataset, index, total):
        """Process a single dataset (for parallel execution)"""
        logger.info(f"\n[{index}/{total}] Processing: {dataset['name']}")
        logger.info(f"Category: {dataset['category']}")
        logger.info(f"Description: {dataset['description']}")
        
        download_path = self.download_dataset(dataset)
        self.insert_dataset_metadata(dataset, download_path)
        
        return dataset['name'], download_path is not None
    
    def process_all_datasets(self):
        """Download and process all datasets in parallel"""
        logger.info("=" * 60)
        logger.info("Kaggle Dataset Downloader (Parallel Mode)")
        logger.info(f"Using {self.max_workers} parallel workers")
        logger.info("=" * 60)
        
        self.create_dataset_tables()
        
        start_time = time.time()
        completed = 0
        failed = 0
        failed_datasets = []  # Track failed datasets
        
        # Use ThreadPoolExecutor for parallel downloads
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all download tasks
            future_to_dataset = {
                executor.submit(self.process_dataset, dataset, i, len(DATASETS)): dataset
                for i, dataset in enumerate(DATASETS, 1)
            }
            
            # Process completed downloads as they finish
            for future in as_completed(future_to_dataset):
                dataset = future_to_dataset[future]
                try:
                    name, success = future.result()
                    if success:
                        completed += 1
                    else:
                        failed += 1
                        failed_datasets.append(name)
                except Exception as e:
                    logger.error(f"✗ Error processing {dataset['name']}: {e}")
                    failed += 1
                    failed_datasets.append(dataset['name'])
        
        elapsed_time = time.time() - start_time
        
        logger.info("\n" + "=" * 60)
        logger.info("✓ All datasets processed!")
        logger.info(f"Completed: {completed}, Failed: {failed}")
        logger.info(f"Total time: {elapsed_time:.1f} seconds ({elapsed_time/60:.1f} minutes)")
        logger.info("=" * 60)
        
        # Summary
        self.print_summary(failed_datasets)
    
    def print_summary(self, failed_datasets=None):
        """Print download summary"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                status,
                COUNT(*) as count,
                SUM(file_count) as total_files,
                SUM(total_size_mb) as total_size_mb
            FROM datasets.kaggle_datasets
            GROUP BY status
        """)
        
        results = cursor.fetchall()
        
        print("\nDownload Summary:")
        print("-" * 60)
        for status, count, files, size in results:
            print(f"  {status.upper()}: {count} datasets, {files or 0} files, {size or 0:.2f} MB")
        
        if failed_datasets:
            print("\nFailed Datasets:")
            for name in failed_datasets:
                print(f"  - {name}")
            print("\nNote: Some datasets (especially competitions) require you to accept the rules on the Kaggle website before downloading.")
        
        cursor.close()
        conn.close()


def main():
    """Main function"""
    # Use 8 parallel workers for supercomputer (can increase to 16 or 32 if needed)
    max_workers = int(os.environ.get('KAGGLE_WORKERS', 8))
    logger.info(f"Initializing with {max_workers} parallel workers")
    
    loader = KaggleDatasetLoader(max_workers=max_workers)
    loader.process_all_datasets()


if __name__ == '__main__':
    main()
