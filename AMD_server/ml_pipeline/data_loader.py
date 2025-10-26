"""
Data Loader Module for ML Pipeline
Provides unified interface to load training data from PostgreSQL and disk files
"""

import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataLoader:
    """
    Unified data loading interface for Morgan & Morgan documents and Kaggle datasets
    
    Usage:
        loader = DataLoader(
            db_host="134.199.202.8",
            db_name="paralegal_db",
            db_user="paralegal_user",
            db_password="hackathon2024"
        )
        
        # Load Morgan & Morgan documents (already labeled)
        morgan_df = loader.load_morgan_documents()
        
        # Load Kaggle dataset files
        kaggle_df = loader.load_kaggle_dataset_files(dataset_id=1)
    """
    
    def __init__(
        self,
        db_host: str = "134.199.202.8",
        db_name: str = "paralegal_db",
        db_user: str = "paralegal_user",
        db_password: str = "hackathon2024",
        db_port: int = 5432
    ):
        """
        Initialize DataLoader with database connection parameters
        
        Args:
            db_host: PostgreSQL host address
            db_name: Database name
            db_user: Database user
            db_password: Database password
            db_port: Database port
        """
        self.db_config = {
            'host': db_host,
            'database': db_name,
            'user': db_user,
            'password': db_password,
            'port': db_port
        }
        self._test_connection()
        
    def _test_connection(self):
        """Test database connection"""
        try:
            conn = psycopg2.connect(**self.db_config)
            conn.close()
            logger.info("✅ Database connection successful")
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise
    
    def _execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        """
        Execute SQL query and return results as list of dictionaries
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            List of dictionaries (one per row)
        """
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query, params)
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise
    
    def load_morgan_documents(self) -> pd.DataFrame:
        """
        Load Morgan & Morgan case documents from legal_data.documents table
        
        These documents are already labeled with document_type and have extracted text.
        Perfect for training document classification models.
        
        Returns:
            DataFrame with columns:
                - document_id: Unique identifier
                - case_id: Case identifier
                - document_type: Label (Settlement Offer, Police Report, etc.)
                - file_name: Original filename
                - full_text: Extracted text content
                - upload_date: When document was uploaded
                - source: Always 'morgan_morgan'
        
        Example:
            >>> loader = DataLoader()
            >>> df = loader.load_morgan_documents()
            >>> print(f"Loaded {len(df)} documents")
            >>> print(df['document_type'].value_counts())
        """
        query = """
            SELECT 
                id,
                document_id,
                title,
                document_type,
                full_text,
                created_at as upload_date
            FROM legal_data.documents
            WHERE session_id = 5  -- Morgan & Morgan session
            AND full_text IS NOT NULL
            AND full_text != ''
            ORDER BY document_id
        """
        
        logger.info("Loading Morgan & Morgan documents from database...")
        results = self._execute_query(query)
        df = pd.DataFrame(results)
        
        # Add source column
        df['source'] = 'morgan_morgan'
        
        # Clean text (remove extra whitespace)
        df['full_text'] = df['full_text'].str.strip()
        
        # Remove any duplicates
        df = df.drop_duplicates(subset=['document_id'])
        
        logger.info(f"✅ Loaded {len(df)} Morgan & Morgan documents")
        logger.info(f"Document types: {df['document_type'].nunique()} unique categories")
        logger.info(f"\nDocument type distribution:\n{df['document_type'].value_counts()}")
        
        return df
    
    def load_kaggle_dataset_metadata(self, dataset_id: Optional[int] = None) -> pd.DataFrame:
        """
        Load metadata about Kaggle datasets from datasets.kaggle_datasets table
        
        Args:
            dataset_id: Optional - filter by specific dataset ID
            
        Returns:
            DataFrame with dataset information
        """
        if dataset_id:
            query = """
                SELECT * FROM datasets.kaggle_datasets
                WHERE id = %s
            """
            params = (dataset_id,)
        else:
            query = "SELECT * FROM datasets.kaggle_datasets ORDER BY id"
            params = None
        
        logger.info("Loading Kaggle dataset metadata...")
        results = self._execute_query(query, params)
        df = pd.DataFrame(results)
        
        logger.info(f"✅ Loaded metadata for {len(df)} Kaggle datasets")
        return df
    
    def load_kaggle_dataset_files(
        self, 
        dataset_id: int,
        max_files: Optional[int] = None,
        file_extensions: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Load file metadata for a specific Kaggle dataset
        
        NOTE: This returns metadata only. Actual file content must be read from disk
        using the file_path column.
        
        Args:
            dataset_id: Kaggle dataset ID
            max_files: Optional limit on number of files to return
            file_extensions: Optional list of extensions to filter (e.g., ['.pdf', '.txt'])
            
        Returns:
            DataFrame with columns:
                - file_id: Unique identifier
                - dataset_id: Parent dataset ID
                - file_name: Name of file
                - file_path: Full path to file on disk
                - file_size: Size in bytes
                - file_type: Extension/type
                - download_date: When file was downloaded
                
        Example:
            >>> # Load PDF files from dataset 1
            >>> df = loader.load_kaggle_dataset_files(dataset_id=1, file_extensions=['.pdf'])
            >>> 
            >>> # Read first file content
            >>> first_file_path = df.iloc[0]['file_path']
            >>> with open(first_file_path, 'r') as f:
            >>>     content = f.read()
        """
        query = """
            SELECT 
                file_id,
                dataset_id,
                file_name,
                file_path,
                file_size,
                file_type,
                download_date
            FROM datasets.dataset_files
            WHERE dataset_id = %s
            ORDER BY file_id
        """
        
        if max_files:
            query += f" LIMIT {max_files}"
        
        logger.info(f"Loading file metadata for Kaggle dataset {dataset_id}...")
        results = self._execute_query(query, (dataset_id,))
        df = pd.DataFrame(results)
        
        # Filter by file extensions if specified
        if file_extensions and len(df) > 0:
            df = df[df['file_type'].isin(file_extensions)]
            logger.info(f"Filtered to {len(df)} files with extensions: {file_extensions}")
        
        logger.info(f"✅ Loaded metadata for {len(df)} files")
        
        return df
    
    def get_classification_data(
        self,
        source: str = 'morgan',
        text_column: str = 'full_text',
        label_column: str = 'document_type'
    ) -> Tuple[pd.Series, pd.Series]:
        """
        Convenience method to get (X, y) for classification tasks
        
        Args:
            source: 'morgan' or 'kaggle'
            text_column: Name of column containing text
            label_column: Name of column containing labels
            
        Returns:
            Tuple of (X, y) where:
                X = text data (pd.Series)
                y = labels (pd.Series)
                
        Example:
            >>> loader = DataLoader()
            >>> X, y = loader.get_classification_data()
            >>> print(f"Training data: {len(X)} samples")
            >>> print(f"Classes: {y.nunique()}")
        """
        if source == 'morgan':
            df = self.load_morgan_documents()
        else:
            raise ValueError("Only 'morgan' source implemented currently")
        
        X = df[text_column]
        y = df[label_column]
        
        logger.info(f"✅ Classification data ready: {len(X)} samples, {y.nunique()} classes")
        
        return X, y
    
    def get_dataset_summary(self) -> Dict:
        """
        Get summary statistics about all available data
        
        Returns:
            Dictionary with dataset statistics
        """
        summary = {}
        
        # Morgan & Morgan documents
        morgan_df = self.load_morgan_documents()
        summary['morgan_morgan'] = {
            'total_documents': len(morgan_df),
            'unique_cases': morgan_df['case_id'].nunique(),
            'document_types': morgan_df['document_type'].nunique(),
            'avg_text_length': morgan_df['full_text'].str.len().mean(),
            'type_distribution': morgan_df['document_type'].value_counts().to_dict()
        }
        
        # Kaggle datasets
        kaggle_df = self.load_kaggle_dataset_metadata()
        summary['kaggle_datasets'] = {
            'total_datasets': len(kaggle_df),
            'dataset_names': kaggle_df['name'].tolist() if 'name' in kaggle_df.columns else []
        }
        
        return summary


# Convenience function for quick access
def get_classification_data() -> Tuple[pd.Series, pd.Series]:
    """
    Quick one-liner to get Morgan & Morgan classification data
    
    Returns:
        (X, y) tuple ready for training
        
    Example:
        >>> from ml_pipeline.data_loader import get_classification_data
        >>> X, y = get_classification_data()
        >>> # Train your model
    """
    loader = DataLoader()
    return loader.get_classification_data()


if __name__ == "__main__":
    # Demo usage
    print("=" * 80)
    print("DATA LOADER DEMO")
    print("=" * 80)
    
    # Initialize loader
    loader = DataLoader()
    
    # Load Morgan documents
    print("\n1. Loading Morgan & Morgan Documents...")
    morgan_df = loader.load_morgan_documents()
    print(f"\nSample document:")
    print(morgan_df[['document_id', 'document_type', 'file_name']].head())
    
    # Get classification data
    print("\n2. Getting classification data...")
    X, y = loader.get_classification_data()
    print(f"X shape: {X.shape}")
    print(f"y shape: {y.shape}")
    print(f"Classes: {sorted(y.unique())}")
    
    # Get summary
    print("\n3. Dataset Summary...")
    summary = loader.get_dataset_summary()
    print(f"Total Morgan docs: {summary['morgan_morgan']['total_documents']}")
    print(f"Total Kaggle datasets: {summary['kaggle_datasets']['total_datasets']}")
    
    print("\n✅ Data loader working correctly!")
