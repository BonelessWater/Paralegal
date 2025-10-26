"""
Image Loader for ML Pipeline

Loads images from database and disk for OCR processing.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging

# Database connection
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from integrations.db_operations import DatabaseManager
except ImportError:
    DatabaseManager = None

logger = logging.getLogger(__name__)


class ImageLoader:
    """
    Load images from database and disk for OCR processing.
    """
    
    def __init__(self, db_manager: Optional[object] = None):
        """
        Initialize image loader.
        
        Args:
            db_manager: DatabaseManager instance (optional, will create if not provided)
        """
        if db_manager:
            self.db = db_manager
        elif DatabaseManager:
            self.db = DatabaseManager()
        else:
            logger.warning("DatabaseManager not available, database operations disabled")
            self.db = None
        
        logger.info("Image Loader initialized")
    
    def get_kaggle_images(
        self,
        dataset_name: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Get image files from Kaggle datasets in database.
        
        Args:
            dataset_name: Filter by dataset name (e.g., 'rvl-cdip')
            limit: Maximum number of images to return
            
        Returns:
            List of dicts with image metadata
        """
        if not self.db:
            logger.error("Database not available")
            return []
        
        try:
            query = """
                SELECT 
                    df.id,
                    df.file_path,
                    df.file_name,
                    df.file_type,
                    df.file_size,
                    ds.name as dataset_name,
                    ds.category
                FROM kaggle_data.dataset_files df
                JOIN kaggle_data.datasets ds ON df.dataset_id = ds.id
                WHERE df.file_type LIKE '%image%'
            """
            
            params = []
            if dataset_name:
                query += " AND ds.name ILIKE %s"
                params.append(f"%{dataset_name}%")
            
            if limit:
                query += f" LIMIT {limit}"
            
            if params:
                result = self.db.execute_query(query, tuple(params))
            else:
                result = self.db.execute_query(query)
            
            logger.info(f"Loaded {len(result)} images from database")
            return result
            
        except Exception as e:
            logger.error(f"Failed to load images from database: {e}")
            return []
    
    def get_document_images(
        self,
        document_type: Optional[str] = None,
        session_id: Optional[int] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Get document image paths from legal_data.documents.
        
        Args:
            document_type: Filter by document type
            session_id: Filter by case session
            limit: Maximum number to return
            
        Returns:
            List of dicts with document metadata and image paths
        """
        if not self.db:
            logger.error("Database not available")
            return []
        
        try:
            query = """
                SELECT 
                    id,
                    title,
                    document_type,
                    url as file_path,
                    session_id,
                    updated_at
                FROM legal_data.documents
                WHERE url IS NOT NULL
                AND (
                    url LIKE '%.jpg' 
                    OR url LIKE '%.jpeg' 
                    OR url LIKE '%.png'
                    OR url LIKE '%.tif'
                    OR url LIKE '%.tiff'
                )
            """
            
            params = []
            if document_type:
                query += " AND document_type = %s"
                params.append(document_type)
            
            if session_id:
                query += " AND session_id = %s"
                params.append(session_id)
            
            query += " ORDER BY updated_at DESC"
            
            if limit:
                query += f" LIMIT {limit}"
            
            if params:
                result = self.db.execute_query(query, tuple(params))
            else:
                result = self.db.execute_query(query)
            
            logger.info(f"Loaded {len(result)} document images from database")
            return result
            
        except Exception as e:
            logger.error(f"Failed to load document images: {e}")
            return []
    
    def verify_files_exist(self, file_paths: List[str]) -> Tuple[List[str], List[str]]:
        """
        Check which files exist on disk.
        
        Args:
            file_paths: List of file paths to check
            
        Returns:
            Tuple of (existing_files, missing_files)
        """
        existing = []
        missing = []
        
        for path in file_paths:
            if os.path.exists(path):
                existing.append(path)
            else:
                missing.append(path)
        
        logger.info(f"File verification: {len(existing)} exist, {len(missing)} missing")
        return existing, missing
    
    def get_training_images(
        self,
        dataset_name: str = "rvl-cdip",
        sample_size: Optional[int] = None
    ) -> List[str]:
        """
        Get image paths for training.
        
        Args:
            dataset_name: Name of Kaggle dataset
            sample_size: Number of images to sample (None = all)
            
        Returns:
            List of image file paths
        """
        images = self.get_kaggle_images(dataset_name=dataset_name, limit=sample_size)
        paths = [img['file_path'] for img in images if img.get('file_path')]
        
        # Verify files exist
        existing, missing = self.verify_files_exist(paths)
        
        if missing:
            logger.warning(f"{len(missing)} image files not found on disk")
        
        return existing
    
    def load_images_batch(
        self,
        file_paths: List[str],
        max_size: Optional[Tuple[int, int]] = None
    ) -> List[object]:
        """
        Load images into memory (use carefully with large datasets).
        
        Args:
            file_paths: List of image file paths
            max_size: Maximum image size (width, height) for resizing
            
        Returns:
            List of PIL Image objects
        """
        try:
            from PIL import Image
        except ImportError:
            raise RuntimeError("PIL not installed. Run: pip install Pillow")
        
        images = []
        for path in file_paths:
            try:
                img = Image.open(path).convert('RGB')
                if max_size:
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                images.append(img)
            except Exception as e:
                logger.error(f"Failed to load {path}: {e}")
        
        logger.info(f"Loaded {len(images)}/{len(file_paths)} images into memory")
        return images


if __name__ == "__main__":
    # Test image loader
    loader = ImageLoader()
    print("✓ Image Loader initialized")
    
    # Test loading Kaggle images metadata
    images = loader.get_kaggle_images(limit=5)
    print(f"\nSample Kaggle images: {len(images)}")
    for img in images[:3]:
        print(f"  - {img.get('file_name')}: {img.get('dataset_name')}")
