"""
Case Matcher - Find similar historical cases

Uses K-NN to find most similar cases for precedent research.
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


class CaseMatcher:
    """
    Find similar historical cases using K-Nearest Neighbors.
    
    Helps identify precedent and comparable settlements.
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize case matcher.
        
        Args:
            model_path: Path to saved model (auto-creates if not found)
        """
        self.model_dir = Path(__file__).parent.parent.parent / "trained_models"
        self.model_dir.mkdir(exist_ok=True)
        
        if model_path:
            self.model_path = Path(model_path)
        else:
            self.model_path = self.model_dir / "case_matcher.pkl"
        
        self.matcher = None
        self.scaler = None
        self.feature_names = None
        self.case_database = None  # Store case metadata
        
        # Try to load existing model
        if self.model_path.exists():
            self.load_model()
        
        logger.info(f"Case Matcher initialized (model: {self.model_path.name})")
    
    def fit(
        self,
        X: pd.DataFrame,
        case_metadata: List[Dict],
        n_neighbors: int = 5
    ):
        """
        Fit case matcher on historical cases.
        
        Args:
            X: Feature DataFrame for historical cases
            case_metadata: List of dicts with case information
            n_neighbors: Number of neighbors to find
        """
        from sklearn.neighbors import NearestNeighbors
        from sklearn.preprocessing import StandardScaler
        
        logger.info(f"Fitting on {len(X)} historical cases...")
        
        # Store feature names
        self.feature_names = list(X.columns)
        
        # Store case metadata
        self.case_database = case_metadata
        
        # Scale features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # Fit K-NN
        self.matcher = NearestNeighbors(
            n_neighbors=n_neighbors,
            algorithm='auto',
            metric='euclidean',
            n_jobs=-1
        )
        
        self.matcher.fit(X_scaled)
        
        logger.info(f"✓ Case matcher fitted with {n_neighbors} neighbors")
        
        # Save model
        self.save_model()
    
    def find_similar_cases(
        self,
        case_features: pd.DataFrame,
        k: int = 5
    ) -> List[Dict]:
        """
        Find K most similar historical cases.
        
        Args:
            case_features: Features for new case
            k: Number of similar cases to return
            
        Returns:
            List of similar case dicts with similarity scores
        """
        if self.matcher is None or self.scaler is None:
            raise RuntimeError("Matcher not fitted. Call fit() first.")
        
        # Ensure features are in correct order
        if self.feature_names:
            case_features = case_features[self.feature_names]
        
        # Scale features
        X_scaled = self.scaler.transform(case_features)
        
        # Find nearest neighbors
        distances, indices = self.matcher.kneighbors(X_scaled, n_neighbors=k)
        
        # Build results
        results = []
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            # Calculate similarity score (inverse of distance)
            similarity = 1 / (1 + dist)
            
            case_info = self.case_database[idx].copy()
            case_info['similarity_score'] = round(similarity, 4)
            case_info['distance'] = round(float(dist), 4)
            case_info['rank'] = i + 1
            
            results.append(case_info)
        
        logger.info(f"✓ Found {len(results)} similar cases")
        
        return results
    
    def find_similar_settlements(
        self,
        case_features: pd.DataFrame,
        k: int = 10
    ) -> Dict[str, float]:
        """
        Find similar cases and get settlement statistics.
        
        Args:
            case_features: Features for new case
            k: Number of similar cases to consider
            
        Returns:
            Dict with settlement statistics (mean, median, min, max, range)
        """
        similar_cases = self.find_similar_cases(case_features, k=k)
        
        # Extract settlement amounts
        settlements = [
            case.get('settlement_amount', 0)
            for case in similar_cases
            if 'settlement_amount' in case
        ]
        
        if not settlements:
            logger.warning("No settlement amounts found in similar cases")
            return {
                'mean': 0,
                'median': 0,
                'min': 0,
                'max': 0,
                'range': 0,
                'n_cases': 0
            }
        
        settlements = np.array(settlements)
        
        return {
            'mean': float(settlements.mean()),
            'median': float(np.median(settlements)),
            'min': float(settlements.min()),
            'max': float(settlements.max()),
            'range': float(settlements.max() - settlements.min()),
            'std': float(settlements.std()),
            'n_cases': len(settlements)
        }
    
    def save_model(self):
        """Save trained matcher to disk."""
        if self.matcher is None:
            logger.warning("No matcher to save")
            return
        
        model_data = {
            'matcher': self.matcher,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'case_database': self.case_database,
            'version': '1.0'
        }
        
        with open(self.model_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"✓ Matcher saved to {self.model_path}")
    
    def load_model(self):
        """Load trained matcher from disk."""
        if not self.model_path.exists():
            logger.warning(f"Matcher file not found: {self.model_path}")
            return
        
        with open(self.model_path, 'rb') as f:
            model_data = pickle.load(f)
        
        self.matcher = model_data['matcher']
        self.scaler = model_data['scaler']
        self.feature_names = model_data['feature_names']
        self.case_database = model_data['case_database']
        
        logger.info(f"✓ Matcher loaded from {self.model_path}")


if __name__ == "__main__":
    # Test case matcher
    from feature_engineering import FeatureEngineer
    
    print("="*70)
    print("CASE MATCHER TEST")
    print("="*70)
    
    # Generate synthetic historical cases
    engineer = FeatureEngineer()
    
    np.random.seed(42)
    n_cases = 100
    
    historical_cases = []
    historical_features = []
    case_metadata = []
    
    for i in range(n_cases):
        severity = np.random.randint(1, 11)
        medical_costs = np.random.randint(10000, 200000)
        
        case = {
            'injury_severity': severity,
            'medical_costs': medical_costs,
            'liability_strength': np.random.uniform(0.5, 1.0),
            'age': np.random.randint(25, 75),
            'state': np.random.choice(['CA', 'NY', 'TX']),
            'case_type': np.random.choice(['CAR_ACCIDENT', 'SLIP_FALL'])
        }
        
        features = engineer.extract_all_features(case)
        settlement = medical_costs * 2 * (severity / 5)
        
        historical_features.append(features)
        
        metadata = {
            'case_id': f"CASE-{i+1:04d}",
            'settlement_amount': settlement,
            'injury_severity': severity,
            'case_type': case['case_type'],
            'description': f"{case['case_type']} case with severity {severity}"
        }
        case_metadata.append(metadata)
    
    # Combine features
    X = pd.concat(historical_features, ignore_index=True)
    
    print(f"\n✓ Generated {len(X)} historical cases")
    
    # Fit matcher
    matcher = CaseMatcher()
    matcher.fit(X, case_metadata, n_neighbors=5)
    
    # Test: Find similar cases
    new_case = {
        'injury_severity': 8,
        'medical_costs': 100000,
        'liability_strength': 0.9,
        'age': 45,
        'state': 'CA',
        'case_type': 'CAR_ACCIDENT'
    }
    
    new_features = engineer.extract_all_features(new_case)
    similar = matcher.find_similar_cases(new_features, k=5)
    
    print(f"\n✓ Found {len(similar)} similar cases:")
    for case in similar:
        print(f"\n  {case['case_id']}: {case['description']}")
        print(f"    Settlement: ${case['settlement_amount']:,.0f}")
        print(f"    Similarity: {case['similarity_score']:.3f}")
    
    # Settlement statistics
    stats = matcher.find_similar_settlements(new_features, k=10)
    print(f"\n✓ Settlement statistics from {stats['n_cases']} similar cases:")
    print(f"  Mean: ${stats['mean']:,.0f}")
    print(f"  Median: ${stats['median']:,.0f}")
    print(f"  Range: ${stats['min']:,.0f} - ${stats['max']:,.0f}")
