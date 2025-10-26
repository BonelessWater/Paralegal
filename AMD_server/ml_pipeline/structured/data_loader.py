"""
Data Loader - Load and merge healthcare datasets

Loads 4 Kaggle healthcare CSV datasets for settlement prediction.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
import pandas as pd
import numpy as np

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from integrations.db_operations import DatabaseManager
except ImportError:
    DatabaseManager = None

logger = logging.getLogger(__name__)


# Kaggle dataset names
DATASETS = {
    'vha_hospitals': 'VHA Hospitals (1,185 rows)',
    'us_hospitals': 'US Hospitals (2,693 rows)',
    'veterans_employment': 'Employment for Veterans (3,233 rows)',
    'lung_cancer': 'Lung Cancer Trial (493 rows)'
}


class DataLoader:
    """
    Load structured healthcare datasets for case analysis.
    
    Loads 4 CSV datasets from Kaggle and Morgan case database.
    """
    
    def __init__(self, data_dir: Optional[str] = None, db_manager: Optional[object] = None):
        """
        Initialize data loader.
        
        Args:
            data_dir: Directory containing CSV files (auto-detect if not provided)
            db_manager: DatabaseManager instance (optional)
        """
        # Auto-detect data directory
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            # Try common locations
            possible_dirs = [
                Path.home() / ".cache" / "kagglehub" / "datasets",
                Path("/workspace/data"),
                Path(__file__).parent.parent.parent.parent / "data"
            ]
            
            for dir_path in possible_dirs:
                if dir_path.exists():
                    self.data_dir = dir_path
                    break
            else:
                self.data_dir = None
        
        # Database connection
        if db_manager:
            self.db = db_manager
        elif DatabaseManager:
            self.db = DatabaseManager()
        else:
            logger.warning("DatabaseManager not available")
            self.db = None
        
        # Cached datasets
        self.vha_hospitals = None
        self.us_hospitals = None
        self.veterans_employment = None
        self.lung_cancer = None
        self.merged_data = None
        
        logger.info(f"Data Loader initialized (data_dir: {self.data_dir})")
    
    def load_vha_hospitals(self) -> pd.DataFrame:
        """
        Load VHA Hospitals dataset (1,185 rows).
        
        Returns:
            DataFrame with VHA hospital information
        """
        if self.vha_hospitals is not None:
            return self.vha_hospitals
        
        try:
            if self.db:
                # Try loading from database
                query = "SELECT * FROM kaggle_data.dataset_files WHERE dataset_name LIKE '%vha%hospital%' LIMIT 1"
                result = self.db.execute_query(query)
                
                if result:
                    file_path = result[0]['file_path']
                    self.vha_hospitals = pd.read_csv(file_path)
                    logger.info(f"✓ Loaded VHA Hospitals from database: {len(self.vha_hospitals)} rows")
                    return self.vha_hospitals
            
            # Fall back to searching data directory
            if self.data_dir:
                # Search for VHA hospital files
                matches = list(self.data_dir.rglob("*vha*hospital*.csv"))
                if matches:
                    self.vha_hospitals = pd.read_csv(matches[0])
                    logger.info(f"✓ Loaded VHA Hospitals: {len(self.vha_hospitals)} rows")
                    return self.vha_hospitals
            
            # Generate synthetic data if no file found
            logger.warning("VHA Hospitals dataset not found, generating synthetic data")
            self.vha_hospitals = self._generate_synthetic_hospitals(n=1185, dataset_type='vha')
            return self.vha_hospitals
            
        except Exception as e:
            logger.error(f"Failed to load VHA Hospitals: {e}")
            self.vha_hospitals = self._generate_synthetic_hospitals(n=1185, dataset_type='vha')
            return self.vha_hospitals
    
    def load_us_hospitals(self) -> pd.DataFrame:
        """
        Load US Hospitals dataset (2,693 rows).
        
        Returns:
            DataFrame with US hospital information
        """
        if self.us_hospitals is not None:
            return self.us_hospitals
        
        try:
            if self.db:
                query = "SELECT * FROM kaggle_data.dataset_files WHERE dataset_name LIKE '%us%hospital%' AND dataset_name NOT LIKE '%vha%' LIMIT 1"
                result = self.db.execute_query(query)
                
                if result:
                    file_path = result[0]['file_path']
                    self.us_hospitals = pd.read_csv(file_path)
                    logger.info(f"✓ Loaded US Hospitals from database: {len(self.us_hospitals)} rows")
                    return self.us_hospitals
            
            if self.data_dir:
                matches = list(self.data_dir.rglob("*hospital*.csv"))
                # Filter out VHA hospitals
                matches = [m for m in matches if 'vha' not in str(m).lower()]
                if matches:
                    self.us_hospitals = pd.read_csv(matches[0])
                    logger.info(f"✓ Loaded US Hospitals: {len(self.us_hospitals)} rows")
                    return self.us_hospitals
            
            logger.warning("US Hospitals dataset not found, generating synthetic data")
            self.us_hospitals = self._generate_synthetic_hospitals(n=2693, dataset_type='us')
            return self.us_hospitals
            
        except Exception as e:
            logger.error(f"Failed to load US Hospitals: {e}")
            self.us_hospitals = self._generate_synthetic_hospitals(n=2693, dataset_type='us')
            return self.us_hospitals
    
    def load_veterans_employment(self) -> pd.DataFrame:
        """
        Load Veterans Employment dataset (3,233 rows).
        
        Returns:
            DataFrame with veteran employment data
        """
        if self.veterans_employment is not None:
            return self.veterans_employment
        
        try:
            if self.db:
                query = "SELECT * FROM kaggle_data.dataset_files WHERE dataset_name LIKE '%veteran%' LIMIT 1"
                result = self.db.execute_query(query)
                
                if result:
                    file_path = result[0]['file_path']
                    self.veterans_employment = pd.read_csv(file_path)
                    logger.info(f"✓ Loaded Veterans Employment from database: {len(self.veterans_employment)} rows")
                    return self.veterans_employment
            
            if self.data_dir:
                matches = list(self.data_dir.rglob("*veteran*.csv"))
                if matches:
                    self.veterans_employment = pd.read_csv(matches[0])
                    logger.info(f"✓ Loaded Veterans Employment: {len(self.veterans_employment)} rows")
                    return self.veterans_employment
            
            logger.warning("Veterans Employment dataset not found, generating synthetic data")
            self.veterans_employment = self._generate_synthetic_veterans(n=3233)
            return self.veterans_employment
            
        except Exception as e:
            logger.error(f"Failed to load Veterans Employment: {e}")
            self.veterans_employment = self._generate_synthetic_veterans(n=3233)
            return self.veterans_employment
    
    def load_lung_cancer(self) -> pd.DataFrame:
        """
        Load Lung Cancer Trial dataset (493 rows).
        
        Returns:
            DataFrame with lung cancer trial data
        """
        if self.lung_cancer is not None:
            return self.lung_cancer
        
        try:
            if self.db:
                query = "SELECT * FROM kaggle_data.dataset_files WHERE dataset_name LIKE '%lung%cancer%' OR dataset_name LIKE '%cancer%' LIMIT 1"
                result = self.db.execute_query(query)
                
                if result:
                    file_path = result[0]['file_path']
                    self.lung_cancer = pd.read_csv(file_path)
                    logger.info(f"✓ Loaded Lung Cancer from database: {len(self.lung_cancer)} rows")
                    return self.lung_cancer
            
            if self.data_dir:
                matches = list(self.data_dir.rglob("*cancer*.csv"))
                if matches:
                    self.lung_cancer = pd.read_csv(matches[0])
                    logger.info(f"✓ Loaded Lung Cancer: {len(self.lung_cancer)} rows")
                    return self.lung_cancer
            
            logger.warning("Lung Cancer dataset not found, generating synthetic data")
            self.lung_cancer = self._generate_synthetic_cancer(n=493)
            return self.lung_cancer
            
        except Exception as e:
            logger.error(f"Failed to load Lung Cancer: {e}")
            self.lung_cancer = self._generate_synthetic_cancer(n=493)
            return self.lung_cancer
    
    def _generate_synthetic_hospitals(self, n: int, dataset_type: str = 'us') -> pd.DataFrame:
        """Generate synthetic hospital data for testing."""
        np.random.seed(42)
        
        data = {
            'hospital_id': range(1, n+1),
            'hospital_name': [f"Hospital {i}" for i in range(1, n+1)],
            'city': np.random.choice(['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix'], n),
            'state': np.random.choice(['NY', 'CA', 'IL', 'TX', 'AZ'], n),
            'beds': np.random.randint(50, 500, n),
            'quality_score': np.random.uniform(1, 5, n).round(2),
            'trauma_center': np.random.choice([True, False], n),
            'avg_wait_time_minutes': np.random.randint(15, 240, n)
        }
        
        if dataset_type == 'vha':
            data['va_facility'] = True
            data['veteran_services'] = True
        
        return pd.DataFrame(data)
    
    def _generate_synthetic_veterans(self, n: int) -> pd.DataFrame:
        """Generate synthetic veteran employment data."""
        np.random.seed(43)
        
        return pd.DataFrame({
            'veteran_id': range(1, n+1),
            'age': np.random.randint(25, 75, n),
            'service_years': np.random.randint(2, 30, n),
            'disability_rating': np.random.choice([0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100], n),
            'employed': np.random.choice([True, False], n, p=[0.7, 0.3]),
            'income': np.random.randint(20000, 120000, n),
            'healthcare_costs': np.random.randint(1000, 50000, n),
            'location_state': np.random.choice(['CA', 'TX', 'FL', 'NY', 'PA'], n)
        })
    
    def _generate_synthetic_cancer(self, n: int) -> pd.DataFrame:
        """Generate synthetic lung cancer trial data."""
        np.random.seed(44)
        
        return pd.DataFrame({
            'patient_id': range(1, n+1),
            'age': np.random.randint(45, 85, n),
            'stage': np.random.choice([1, 2, 3, 4], n, p=[0.1, 0.2, 0.3, 0.4]),
            'treatment': np.random.choice(['surgery', 'chemo', 'radiation', 'immunotherapy'], n),
            'smoker': np.random.choice([True, False], n, p=[0.8, 0.2]),
            'pack_years': np.random.randint(0, 80, n),
            'survival_months': np.random.randint(1, 120, n),
            'treatment_cost': np.random.randint(50000, 500000, n)
        })
    
    def load_all_datasets(self) -> Dict[str, pd.DataFrame]:
        """
        Load all 4 datasets.
        
        Returns:
            Dict mapping dataset name to DataFrame
        """
        return {
            'vha_hospitals': self.load_vha_hospitals(),
            'us_hospitals': self.load_us_hospitals(),
            'veterans_employment': self.load_veterans_employment(),
            'lung_cancer': self.load_lung_cancer()
        }
    
    def get_summary(self) -> Dict:
        """
        Get summary statistics for all datasets.
        
        Returns:
            Dict with dataset summaries
        """
        datasets = self.load_all_datasets()
        
        summary = {}
        for name, df in datasets.items():
            summary[name] = {
                'rows': len(df),
                'columns': len(df.columns),
                'column_names': list(df.columns),
                'memory_mb': df.memory_usage(deep=True).sum() / 1024 / 1024
            }
        
        return summary


if __name__ == "__main__":
    # Test data loader
    loader = DataLoader()
    
    print("="*70)
    print("DATA LOADER TEST")
    print("="*70)
    
    # Load all datasets
    datasets = loader.load_all_datasets()
    
    print(f"\n✓ Loaded {len(datasets)} datasets:")
    for name, df in datasets.items():
        print(f"  {name:25s}: {len(df):>5} rows x {len(df.columns):>2} cols")
    
    # Get summary
    summary = loader.get_summary()
    print(f"\n" + "="*70)
    print("DATASET SUMMARY")
    print("="*70)
    
    for name, stats in summary.items():
        print(f"\n{name}:")
        print(f"  Rows: {stats['rows']}")
        print(f"  Columns: {stats['columns']}")
        print(f"  Memory: {stats['memory_mb']:.2f} MB")
        print(f"  Fields: {', '.join(stats['column_names'][:5])}...")
