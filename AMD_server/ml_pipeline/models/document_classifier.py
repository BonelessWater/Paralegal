"""
Document Classifier Model
Trains classification models on legal documents
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional, Tuple, Any
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.metrics import (
    accuracy_score, precision_recall_fscore_support,
    classification_report, confusion_matrix
)
import pickle
import logging
from pathlib import Path
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentClassifier:
    """
    Train and evaluate document classification models
    
    Supports multiple algorithms:
    - RandomForest (default, good balance)
    - LogisticRegression (fast, interpretable)
    - GradientBoosting (often best accuracy)
    - LinearSVC (good for text)
    
    Usage:
        >>> from ml_pipeline.data_loader import get_classification_data
        >>> from ml_pipeline.feature_engineering import prepare_features
        >>> from ml_pipeline.train_test_split import quick_split
        >>> 
        >>> # Load data
        >>> X, y = get_classification_data()
        >>> X_train, X_test, y_train, y_test = quick_split(X, y)
        >>> 
        >>> # Prepare features
        >>> X_train_feat, X_test_feat, y_train_enc, y_test_enc, extractor = prepare_features(
        >>>     X_train, X_test, y_train, y_test
        >>> )
        >>> 
        >>> # Train model
        >>> classifier = DocumentClassifier(model_type='random_forest')
        >>> classifier.fit(X_train_feat, y_train_enc)
        >>> 
        >>> # Evaluate
        >>> metrics = classifier.evaluate(X_test_feat, y_test_enc)
        >>> print(f"Accuracy: {metrics['accuracy']:.3f}")
    """
    
    def __init__(
        self,
        model_type: str = 'random_forest',
        **model_kwargs
    ):
        """
        Initialize classifier
        
        Args:
            model_type: One of ['random_forest', 'logistic_regression', 'gradient_boosting', 'linear_svc']
            **model_kwargs: Additional arguments for the model
        """
        self.model_type = model_type
        self.model = self._create_model(model_type, **model_kwargs)
        self.is_fitted = False
        self.training_history = {}
        
    def _create_model(self, model_type: str, **kwargs):
        """Create sklearn model based on type"""
        models = {
            'random_forest': RandomForestClassifier(
                n_estimators=kwargs.get('n_estimators', 100),
                max_depth=kwargs.get('max_depth', None),
                min_samples_split=kwargs.get('min_samples_split', 2),
                random_state=kwargs.get('random_state', 42),
                n_jobs=-1  # Use all CPUs
            ),
            'logistic_regression': LogisticRegression(
                max_iter=kwargs.get('max_iter', 1000),
                random_state=kwargs.get('random_state', 42),
                n_jobs=-1
            ),
            'gradient_boosting': GradientBoostingClassifier(
                n_estimators=kwargs.get('n_estimators', 100),
                max_depth=kwargs.get('max_depth', 3),
                random_state=kwargs.get('random_state', 42)
            ),
            'linear_svc': LinearSVC(
                max_iter=kwargs.get('max_iter', 1000),
                random_state=kwargs.get('random_state', 42)
            )
        }
        
        if model_type not in models:
            raise ValueError(f"Unknown model type: {model_type}. Choose from {list(models.keys())}")
        
        return models[model_type]
    
    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None
    ) -> 'DocumentClassifier':
        """
        Train the model
        
        Args:
            X_train: Training features (n_samples, n_features)
            y_train: Training labels (n_samples,)
            X_val: Optional validation features
            y_val: Optional validation labels
            
        Returns:
            self (for method chaining)
        """
        logger.info("=" * 80)
        logger.info(f"TRAINING {self.model_type.upper()} MODEL")
        logger.info("=" * 80)
        logger.info(f"Training samples: {len(X_train)}")
        logger.info(f"Features: {X_train.shape[1]}")
        logger.info(f"Classes: {len(np.unique(y_train))}")
        
        # Train model
        start_time = datetime.now()
        self.model.fit(X_train, y_train)
        training_time = (datetime.now() - start_time).total_seconds()
        
        self.is_fitted = True
        
        # Store training info
        self.training_history = {
            'model_type': self.model_type,
            'training_samples': len(X_train),
            'n_features': X_train.shape[1],
            'n_classes': len(np.unique(y_train)),
            'training_time_seconds': training_time,
            'timestamp': datetime.now().isoformat()
        }
        
        # Evaluate on training set
        train_acc = self.model.score(X_train, y_train)
        self.training_history['train_accuracy'] = train_acc
        
        logger.info(f"✅ Training complete in {training_time:.2f} seconds")
        logger.info(f"Training accuracy: {train_acc:.4f}")
        
        # Evaluate on validation set if provided
        if X_val is not None and y_val is not None:
            val_acc = self.model.score(X_val, y_val)
            self.training_history['val_accuracy'] = val_acc
            logger.info(f"Validation accuracy: {val_acc:.4f}")
        
        return self
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class labels
        
        Args:
            X: Features (n_samples, n_features)
            
        Returns:
            Predicted labels (n_samples,)
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        return self.model.predict(X)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class probabilities
        
        Args:
            X: Features (n_samples, n_features)
            
        Returns:
            Probabilities (n_samples, n_classes)
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        if hasattr(self.model, 'predict_proba'):
            return self.model.predict_proba(X)
        else:
            raise ValueError(f"{self.model_type} doesn't support probability prediction")
    
    def evaluate(
        self,
        X: np.ndarray,
        y_true: np.ndarray,
        class_names: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive evaluation of model
        
        Args:
            X: Features
            y_true: True labels
            class_names: Optional list of class names for better reporting
            
        Returns:
            Dictionary with metrics:
                - accuracy: Overall accuracy
                - precision: Per-class precision
                - recall: Per-class recall
                - f1: Per-class F1 score
                - confusion_matrix: Confusion matrix
                - classification_report: Detailed sklearn report
        """
        logger.info("=" * 80)
        logger.info("MODEL EVALUATION")
        logger.info("=" * 80)
        
        # Predictions
        y_pred = self.predict(X)
        
        # Calculate metrics
        accuracy = accuracy_score(y_true, y_pred)
        precision, recall, f1, support = precision_recall_fscore_support(
            y_true, y_pred, average=None, zero_division=0
        )
        
        # Confusion matrix
        cm = confusion_matrix(y_true, y_pred)
        
        # Classification report
        if class_names:
            target_names = class_names
        else:
            target_names = [f"Class {i}" for i in range(len(np.unique(y_true)))]
        
        report = classification_report(
            y_true, y_pred,
            target_names=target_names,
            zero_division=0
        )
        
        # Log results
        logger.info(f"Accuracy: {accuracy:.4f}")
        logger.info(f"\nPer-class metrics:")
        for i, name in enumerate(target_names):
            logger.info(f"  {name}:")
            logger.info(f"    Precision: {precision[i]:.4f}")
            logger.info(f"    Recall:    {recall[i]:.4f}")
            logger.info(f"    F1:        {f1[i]:.4f}")
            logger.info(f"    Support:   {support[i]}")
        
        logger.info(f"\nDetailed classification report:\n{report}")
        logger.info(f"\nConfusion Matrix:\n{cm}")
        
        return {
            'accuracy': accuracy,
            'precision': precision.tolist(),
            'recall': recall.tolist(),
            'f1': f1.tolist(),
            'support': support.tolist(),
            'confusion_matrix': cm.tolist(),
            'classification_report': report,
            'class_names': target_names
        }
    
    def save(self, filepath: str, metrics: Optional[Dict] = None):
        """
        Save trained model to disk
        
        Args:
            filepath: Path to save pickle file
            metrics: Optional evaluation metrics to save alongside
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Nothing to save.")
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        state = {
            'model': self.model,
            'model_type': self.model_type,
            'training_history': self.training_history,
            'metrics': metrics
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(state, f)
        
        logger.info(f"✅ Model saved to {filepath}")
        
        # Also save metrics as JSON for easy reading
        if metrics:
            metrics_path = filepath.replace('.pkl', '_metrics.json')
            with open(metrics_path, 'w') as f:
                # Convert numpy arrays to lists for JSON
                metrics_json = {}
                for k, v in metrics.items():
                    if isinstance(v, np.ndarray):
                        metrics_json[k] = v.tolist()
                    elif isinstance(v, (list, dict, str, int, float)):
                        metrics_json[k] = v
                
                json.dump(metrics_json, f, indent=2)
            logger.info(f"✅ Metrics saved to {metrics_path}")
    
    @classmethod
    def load(cls, filepath: str) -> 'DocumentClassifier':
        """
        Load trained model from disk
        
        Args:
            filepath: Path to pickle file
            
        Returns:
            DocumentClassifier instance with loaded model
        """
        with open(filepath, 'rb') as f:
            state = pickle.load(f)
        
        classifier = cls(model_type=state['model_type'])
        classifier.model = state['model']
        classifier.is_fitted = True
        classifier.training_history = state['training_history']
        
        logger.info(f"✅ Model loaded from {filepath}")
        logger.info(f"Model type: {classifier.model_type}")
        logger.info(f"Trained on: {state['training_history'].get('timestamp', 'Unknown')}")
        
        if state.get('metrics'):
            logger.info(f"Saved accuracy: {state['metrics'].get('accuracy', 'Unknown')}")
        
        return classifier


def train_document_classifier(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    model_type: str = 'random_forest',
    class_names: Optional[list] = None,
    save_path: Optional[str] = None
) -> Tuple[DocumentClassifier, Dict]:
    """
    One-stop function to train and evaluate a document classifier
    
    Args:
        X_train: Training features
        y_train: Training labels
        X_test: Test features
        y_test: Test labels
        model_type: Type of model to train
        class_names: Optional class names for reporting
        save_path: Optional path to save trained model
        
    Returns:
        Tuple of (classifier, metrics)
        
    Example:
        >>> from ml_pipeline.models.document_classifier import train_document_classifier
        >>> 
        >>> classifier, metrics = train_document_classifier(
        >>>     X_train, y_train, X_test, y_test,
        >>>     model_type='random_forest',
        >>>     class_names=['Settlement', 'Police Report', 'Medical']
        >>> )
        >>> print(f"Accuracy: {metrics['accuracy']:.3f}")
    """
    # Train
    classifier = DocumentClassifier(model_type=model_type)
    classifier.fit(X_train, y_train)
    
    # Evaluate
    metrics = classifier.evaluate(X_test, y_test, class_names=class_names)
    
    # Save if requested
    if save_path:
        classifier.save(save_path, metrics=metrics)
    
    return classifier, metrics


if __name__ == "__main__":
    # Demo with synthetic data
    print("=" * 80)
    print("DOCUMENT CLASSIFIER DEMO")
    print("=" * 80)
    
    # Create synthetic data
    np.random.seed(42)
    n_samples = 100
    n_features = 50
    n_classes = 5
    
    X_train = np.random.randn(n_samples, n_features)
    y_train = np.random.randint(0, n_classes, n_samples)
    
    X_test = np.random.randn(20, n_features)
    y_test = np.random.randint(0, n_classes, 20)
    
    class_names = ['Type A', 'Type B', 'Type C', 'Type D', 'Type E']
    
    # Train and evaluate
    classifier, metrics = train_document_classifier(
        X_train, y_train, X_test, y_test,
        model_type='random_forest',
        class_names=class_names,
        save_path='/tmp/test_classifier.pkl'
    )
    
    print(f"\n✅ Final Accuracy: {metrics['accuracy']:.3f}")
