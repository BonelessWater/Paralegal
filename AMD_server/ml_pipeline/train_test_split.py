"""
Train/Test/Val Split Utilities
Handles data splitting with special consideration for small datasets
"""

import numpy as np
import pandas as pd
from typing import Tuple, Optional
from sklearn.model_selection import train_test_split, StratifiedKFold
import pickle
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataSplitter:
    """
    Create reproducible train/test/validation splits
    
    Handles:
    - Stratified splitting (maintains class distribution)
    - Small dataset handling (k-fold cross-validation)
    - Reproducible random seeds
    - Save/load split indices
    """
    
    def __init__(self, random_state: int = 42):
        """
        Initialize splitter
        
        Args:
            random_state: Random seed for reproducibility
        """
        self.random_state = random_state
        self.split_indices = None
        
    def create_splits(
        self,
        X: pd.Series,
        y: pd.Series,
        test_size: float = 0.15,
        val_size: float = 0.15,
        stratify: bool = True
    ) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series, pd.Series, pd.Series]:
        """
        Create train/val/test splits
        
        Args:
            X: Features (text)
            y: Labels
            test_size: Fraction for test set (0-1)
            val_size: Fraction for validation set (0-1)
            stratify: Whether to maintain class distribution
            
        Returns:
            (X_train, X_val, X_test, y_train, y_val, y_test)
            
        Example:
            >>> splitter = DataSplitter()
            >>> X_train, X_val, X_test, y_train, y_val, y_test = splitter.create_splits(X, y)
        """
        logger.info("=" * 80)
        logger.info("CREATING DATA SPLITS")
        logger.info("=" * 80)
        logger.info(f"Total samples: {len(X)}")
        logger.info(f"Test size: {test_size:.1%}")
        logger.info(f"Val size: {val_size:.1%}")
        logger.info(f"Train size: {1 - test_size - val_size:.1%}")
        logger.info(f"Stratified: {stratify}")
        
        # Check if dataset is too small
        if len(X) < 30:
            logger.warning("⚠️ Very small dataset! Consider using cross-validation instead.")
        
        # First split: separate test set
        stratify_arg = y if stratify else None
        
        X_temp, X_test, y_temp, y_test = train_test_split(
            X, y,
            test_size=test_size,
            random_state=self.random_state,
            stratify=stratify_arg
        )
        
        # Second split: separate validation from training
        # Adjust val_size to be relative to remaining data
        val_size_adjusted = val_size / (1 - test_size)
        stratify_temp = y_temp if stratify else None
        
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp,
            test_size=val_size_adjusted,
            random_state=self.random_state,
            stratify=stratify_temp
        )
        
        # Store indices for reproducibility
        self.split_indices = {
            'train': X_train.index.tolist(),
            'val': X_val.index.tolist(),
            'test': X_test.index.tolist()
        }
        
        # Log split statistics
        logger.info("\n" + "=" * 80)
        logger.info("SPLIT STATISTICS")
        logger.info("=" * 80)
        logger.info(f"Train: {len(X_train)} samples ({len(X_train)/len(X):.1%})")
        logger.info(f"Val:   {len(X_val)} samples ({len(X_val)/len(X):.1%})")
        logger.info(f"Test:  {len(X_test)} samples ({len(X_test)/len(X):.1%})")
        
        # Log class distribution if labels are categorical
        if stratify:
            logger.info("\nClass distribution:")
            logger.info(f"Train:\n{y_train.value_counts().sort_index()}")
            logger.info(f"\nVal:\n{y_val.value_counts().sort_index()}")
            logger.info(f"\nTest:\n{y_test.value_counts().sort_index()}")
        
        return X_train, X_val, X_test, y_train, y_val, y_test
    
    def save_split_indices(self, filepath: str):
        """
        Save split indices to disk for reproducibility
        
        Args:
            filepath: Path to save pickle file
        """
        if self.split_indices is None:
            raise ValueError("No splits created yet. Call create_splits() first.")
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'wb') as f:
            pickle.dump(self.split_indices, f)
        
        logger.info(f"✅ Split indices saved to {filepath}")
    
    def load_split_indices(self, filepath: str):
        """
        Load split indices from disk
        
        Args:
            filepath: Path to pickle file
        """
        with open(filepath, 'rb') as f:
            self.split_indices = pickle.load(f)
        
        logger.info(f"✅ Split indices loaded from {filepath}")
        logger.info(f"Train: {len(self.split_indices['train'])} samples")
        logger.info(f"Val: {len(self.split_indices['val'])} samples")
        logger.info(f"Test: {len(self.split_indices['test'])} samples")
    
    def apply_saved_split(
        self, 
        X: pd.Series, 
        y: pd.Series
    ) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series, pd.Series, pd.Series]:
        """
        Apply previously saved split indices to data
        
        Args:
            X: Features
            y: Labels
            
        Returns:
            (X_train, X_val, X_test, y_train, y_val, y_test)
        """
        if self.split_indices is None:
            raise ValueError("No split indices loaded. Call load_split_indices() first.")
        
        X_train = X.loc[self.split_indices['train']]
        X_val = X.loc[self.split_indices['val']]
        X_test = X.loc[self.split_indices['test']]
        
        y_train = y.loc[self.split_indices['train']]
        y_val = y.loc[self.split_indices['val']]
        y_test = y.loc[self.split_indices['test']]
        
        logger.info("✅ Applied saved split indices")
        
        return X_train, X_val, X_test, y_train, y_val, y_test


def get_cross_validation_folds(
    X: pd.Series,
    y: pd.Series,
    n_folds: int = 5,
    random_state: int = 42
) -> StratifiedKFold:
    """
    Create stratified k-fold cross-validation splits
    
    Useful for small datasets where a single train/test split might not be reliable.
    
    Args:
        X: Features
        y: Labels
        n_folds: Number of folds
        random_state: Random seed
        
    Returns:
        StratifiedKFold object
        
    Example:
        >>> from ml_pipeline.train_test_split import get_cross_validation_folds
        >>> from sklearn.ensemble import RandomForestClassifier
        >>> 
        >>> folds = get_cross_validation_folds(X, y, n_folds=5)
        >>> scores = []
        >>> 
        >>> for train_idx, val_idx in folds.split(X, y):
        >>>     X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        >>>     y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
        >>>     
        >>>     model = RandomForestClassifier()
        >>>     model.fit(X_train, y_train)
        >>>     score = model.score(X_val, y_val)
        >>>     scores.append(score)
        >>> 
        >>> print(f"CV Accuracy: {np.mean(scores):.3f} ± {np.std(scores):.3f}")
    """
    logger.info(f"Creating {n_folds}-fold cross-validation splits...")
    logger.info(f"Total samples: {len(X)}")
    logger.info(f"Samples per fold: ~{len(X) // n_folds}")
    
    skf = StratifiedKFold(
        n_splits=n_folds,
        shuffle=True,
        random_state=random_state
    )
    
    return skf


def quick_split(
    X: pd.Series,
    y: pd.Series,
    test_size: float = 0.2
) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
    """
    Simple train/test split (no validation set)
    
    Args:
        X: Features
        y: Labels
        test_size: Fraction for test set
        
    Returns:
        (X_train, X_test, y_train, y_test)
        
    Example:
        >>> from ml_pipeline.train_test_split import quick_split
        >>> X_train, X_test, y_train, y_test = quick_split(X, y, test_size=0.2)
    """
    logger.info(f"Creating simple train/test split ({test_size:.1%} test)...")
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=test_size,
        random_state=42,
        stratify=y
    )
    
    logger.info(f"Train: {len(X_train)} samples")
    logger.info(f"Test:  {len(X_test)} samples")
    
    return X_train, X_test, y_train, y_test


if __name__ == "__main__":
    # Demo usage
    print("=" * 80)
    print("TRAIN/TEST/VAL SPLIT DEMO")
    print("=" * 80)
    
    # Create sample data
    np.random.seed(42)
    n_samples = 54  # Same size as Morgan docs
    
    X = pd.Series([f"document_{i}" for i in range(n_samples)])
    y = pd.Series(np.random.choice(['Type A', 'Type B', 'Type C'], size=n_samples))
    
    print(f"\nSample data: {len(X)} documents")
    print(f"Classes: {y.value_counts().to_dict()}")
    
    # Create splits
    splitter = DataSplitter()
    X_train, X_val, X_test, y_train, y_val, y_test = splitter.create_splits(
        X, y, test_size=0.15, val_size=0.15
    )
    
    # Save splits
    splitter.save_split_indices('/tmp/split_indices.pkl')
    
    # Load and reapply
    splitter2 = DataSplitter()
    splitter2.load_split_indices('/tmp/split_indices.pkl')
    X_train2, X_val2, X_test2, y_train2, y_val2, y_test2 = splitter2.apply_saved_split(X, y)
    
    # Verify they match
    assert X_train.equals(X_train2), "Splits don't match!"
    print("\n✅ Split save/load working correctly!")
