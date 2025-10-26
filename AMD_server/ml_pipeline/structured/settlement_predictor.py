"""
Settlement Predictor - Predict settlement amounts using ML

Trains regression model to predict settlement amounts based on case features.
"""

import sys
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
import pandas as pd
import numpy as np

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)


class SettlementPredictor:
    """
    Predict settlement amounts for legal cases.
    
    Uses XGBoost regression on engineered features.
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize settlement predictor.
        
        Args:
            model_path: Path to saved model (auto-creates if not found)
        """
        self.model_dir = Path(__file__).parent.parent.parent / "trained_models"
        self.model_dir.mkdir(exist_ok=True)
        
        if model_path:
            self.model_path = Path(model_path)
        else:
            self.model_path = self.model_dir / "settlement_predictor.pkl"
        
        self.model = None
        self.scaler = None
        self.feature_names = None
        
        # Try to load existing model
        if self.model_path.exists():
            self.load_model()
        
        logger.info(f"Settlement Predictor initialized (model: {self.model_path.name})")
    
    def train(
        self,
        X: pd.DataFrame,
        y: np.ndarray,
        test_size: float = 0.2
    ) -> Dict[str, float]:
        """
        Train settlement prediction model.
        
        Args:
            X: Feature DataFrame
            y: Settlement amounts (target variable)
            test_size: Fraction for validation
            
        Returns:
            Training metrics (MAE, RMSE, R²)
        """
        from sklearn.model_selection import train_test_split
        from sklearn.preprocessing import StandardScaler
        from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
        
        try:
            from xgboost import XGBRegressor
            use_xgboost = True
        except ImportError:
            logger.warning("XGBoost not available, falling back to RandomForest")
            from sklearn.ensemble import RandomForestRegressor
            use_xgboost = False
        
        logger.info(f"Training on {len(X)} samples...")
        
        # Store feature names
        self.feature_names = list(X.columns)
        
        # Scale features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=test_size, random_state=42
        )
        
        # Train model
        if use_xgboost:
            self.model = XGBRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42,
                n_jobs=-1
            )
        else:
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=15,
                random_state=42,
                n_jobs=-1
            )
        
        self.model.fit(X_train, y_train)
        
        # Evaluate
        y_pred_train = self.model.predict(X_train)
        y_pred_test = self.model.predict(X_test)
        
        # Calculate metrics
        metrics = {
            'train_mae': mean_absolute_error(y_train, y_pred_train),
            'test_mae': mean_absolute_error(y_test, y_pred_test),
            'train_rmse': np.sqrt(mean_squared_error(y_train, y_pred_train)),
            'test_rmse': np.sqrt(mean_squared_error(y_test, y_pred_test)),
            'train_r2': r2_score(y_train, y_pred_train),
            'test_r2': r2_score(y_test, y_pred_test),
            'n_train': len(X_train),
            'n_test': len(X_test),
            'n_features': len(self.feature_names)
        }
        
        logger.info(f"✓ Training complete - Test R²: {metrics['test_r2']:.3f}, Test MAE: ${metrics['test_mae']:,.0f}")
        
        # Save model
        self.save_model()
        
        return metrics
    
    def predict(self, features: pd.DataFrame) -> float:
        """
        Predict settlement amount for single case.
        
        Args:
            features: DataFrame with one row of features
            
        Returns:
            Predicted settlement amount ($)
        """
        if self.model is None or self.scaler is None:
            raise RuntimeError("Model not trained. Call train() first.")
        
        # Ensure features are in correct order
        if self.feature_names:
            features = features[self.feature_names]
        
        # Scale features
        X_scaled = self.scaler.transform(features)
        
        # Predict
        prediction = self.model.predict(X_scaled)[0]
        
        # Ensure non-negative
        prediction = max(prediction, 0)
        
        return prediction
    
    def predict_with_confidence(
        self,
        features: pd.DataFrame,
        n_estimators: Optional[int] = None
    ) -> Dict[str, float]:
        """
        Predict settlement with confidence interval.
        
        Args:
            features: DataFrame with one row of features
            n_estimators: Number of trees to use (for RandomForest)
            
        Returns:
            Dict with prediction, lower_bound, upper_bound
        """
        if self.model is None:
            raise RuntimeError("Model not trained")
        
        prediction = self.predict(features)
        
        # For tree-based models, get prediction variance from individual trees
        try:
            # Scale features
            X_scaled = self.scaler.transform(features[self.feature_names])
            
            # Get predictions from all estimators
            if hasattr(self.model, 'estimators_'):
                # RandomForest
                tree_predictions = np.array([
                    tree.predict(X_scaled)[0]
                    for tree in self.model.estimators_
                ])
            elif hasattr(self.model, 'get_booster'):
                # XGBoost - use standard error estimate
                std_error = prediction * 0.15  # ~15% standard error
                return {
                    'prediction': prediction,
                    'lower_bound': max(prediction - 1.96 * std_error, 0),
                    'upper_bound': prediction + 1.96 * std_error,
                    'confidence_interval': 0.95
                }
            else:
                # Unknown model type
                return {
                    'prediction': prediction,
                    'lower_bound': prediction,
                    'upper_bound': prediction,
                    'confidence_interval': 1.0
                }
            
            # Calculate confidence interval (95%)
            std = np.std(tree_predictions)
            
            return {
                'prediction': prediction,
                'lower_bound': max(prediction - 1.96 * std, 0),
                'upper_bound': prediction + 1.96 * std,
                'confidence_interval': 0.95
            }
            
        except Exception as e:
            logger.warning(f"Could not calculate confidence interval: {e}")
            return {
                'prediction': prediction,
                'lower_bound': prediction,
                'upper_bound': prediction,
                'confidence_interval': 1.0
            }
    
    def predict_batch(self, features: pd.DataFrame) -> np.ndarray:
        """
        Predict settlement amounts for multiple cases.
        
        Args:
            features: DataFrame with features for multiple cases
            
        Returns:
            Array of predicted settlement amounts
        """
        if self.model is None or self.scaler is None:
            raise RuntimeError("Model not trained")
        
        # Ensure features are in correct order
        if self.feature_names:
            features = features[self.feature_names]
        
        # Scale and predict
        X_scaled = self.scaler.transform(features)
        predictions = self.model.predict(X_scaled)
        
        # Ensure non-negative
        predictions = np.maximum(predictions, 0)
        
        return predictions
    
    def get_feature_importance(self, top_k: int = 20) -> List[Tuple[str, float]]:
        """
        Get most important features for predictions.
        
        Args:
            top_k: Number of top features to return
            
        Returns:
            List of (feature_name, importance) tuples
        """
        if self.model is None:
            raise RuntimeError("Model not trained")
        
        # Get feature importances
        if hasattr(self.model, 'feature_importances_'):
            importances = self.model.feature_importances_
        else:
            logger.warning("Model does not support feature importances")
            return []
        
        # Pair with feature names
        feature_importance = list(zip(self.feature_names, importances))
        
        # Sort by importance
        feature_importance.sort(key=lambda x: x[1], reverse=True)
        
        return feature_importance[:top_k]
    
    def save_model(self):
        """Save trained model to disk."""
        if self.model is None:
            logger.warning("No model to save")
            return
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'version': '1.0'
        }
        
        with open(self.model_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"✓ Model saved to {self.model_path}")
    
    def load_model(self):
        """Load trained model from disk."""
        if not self.model_path.exists():
            logger.warning(f"Model file not found: {self.model_path}")
            return
        
        with open(self.model_path, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.feature_names = model_data['feature_names']
        
        logger.info(f"✓ Model loaded from {self.model_path}")


if __name__ == "__main__":
    # Test settlement predictor with synthetic data
    from feature_engineering import FeatureEngineer
    
    print("="*70)
    print("SETTLEMENT PREDICTOR TEST")
    print("="*70)
    
    # Generate synthetic training data
    engineer = FeatureEngineer()
    
    np.random.seed(42)
    n_samples = 200
    
    cases = []
    settlements = []
    
    for i in range(n_samples):
        severity = np.random.randint(1, 11)
        medical_costs = np.random.randint(10000, 200000)
        liability = np.random.uniform(0.5, 1.0)
        
        case = {
            'injury_severity': severity,
            'medical_costs': medical_costs,
            'liability_strength': liability,
            'treatment_duration_days': np.random.randint(30, 365),
            'permanent_disability': np.random.choice([True, False], p=[0.3, 0.7]),
            'surgery_required': np.random.choice([True, False], p=[0.4, 0.6]),
            'age': np.random.randint(25, 75),
            'annual_income': np.random.randint(30000, 150000),
            'state': np.random.choice(['CA', 'NY', 'TX', 'FL', 'IL']),
            'case_type': np.random.choice(['CAR_ACCIDENT', 'SLIP_FALL', 'MEDICAL_MALPRACTICE'])
        }
        
        # Settlement formula (rough approximation)
        base_settlement = medical_costs * 2
        severity_multiplier = 1 + (severity / 10)
        liability_multiplier = liability
        
        settlement = base_settlement * severity_multiplier * liability_multiplier
        settlement += np.random.normal(0, settlement * 0.2)  # Add noise
        settlement = max(settlement, 5000)  # Minimum settlement
        
        cases.append(case)
        settlements.append(settlement)
    
    # Extract features
    X = engineer.extract_batch_features(cases)
    y = np.array(settlements)
    
    print(f"\n✓ Generated {len(cases)} synthetic cases")
    print(f"  Settlement range: ${y.min():,.0f} - ${y.max():,.0f}")
    print(f"  Mean settlement: ${y.mean():,.0f}")
    
    # Train model
    predictor = SettlementPredictor()
    metrics = predictor.train(X, y, test_size=0.2)
    
    print(f"\n✓ Model trained:")
    print(f"  Test R²: {metrics['test_r2']:.3f}")
    print(f"  Test MAE: ${metrics['test_mae']:,.0f}")
    print(f"  Test RMSE: ${metrics['test_rmse']:,.0f}")
    
    # Test prediction
    test_case = {
        'injury_severity': 9,
        'medical_costs': 125000,
        'liability_strength': 0.95,
        'treatment_duration_days': 240,
        'permanent_disability': True,
        'surgery_required': True,
        'age': 45,
        'annual_income': 75000,
        'state': 'CA',
        'case_type': 'CAR_ACCIDENT'
    }
    
    test_features = engineer.extract_all_features(test_case)
    result = predictor.predict_with_confidence(test_features)
    
    print(f"\n✓ Test prediction:")
    print(f"  Predicted settlement: ${result['prediction']:,.0f}")
    print(f"  95% CI: ${result['lower_bound']:,.0f} - ${result['upper_bound']:,.0f}")
    
    # Feature importance
    importance = predictor.get_feature_importance(top_k=10)
    print(f"\n✓ Top 10 most important features:")
    for i, (feature, score) in enumerate(importance, 1):
        print(f"  {i:2d}. {feature:30s}: {score:.4f}")
