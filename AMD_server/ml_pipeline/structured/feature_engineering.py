"""
Feature Engineering - Extract features for settlement prediction

Creates numerical features from healthcare data for ML models.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional
import logging
import pandas as pd
import numpy as np

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """
    Engineer features for settlement prediction from case data.
    
    Extracts numerical features from structured healthcare data.
    """
    
    def __init__(self):
        """Initialize feature engineer."""
        self.feature_names = []
        logger.info("Feature Engineer initialized")
    
    def extract_injury_features(self, case_data: Dict) -> Dict[str, float]:
        """
        Extract injury-related features.
        
        Args:
            case_data: Dict with case information
            
        Returns:
            Dict of injury features
        """
        features = {}
        
        # Injury severity (1-10 scale)
        severity = case_data.get('injury_severity', 5)
        features['injury_severity'] = severity
        
        # Treatment duration (days)
        features['treatment_days'] = case_data.get('treatment_duration_days', 90)
        
        # Medical costs
        features['medical_costs'] = case_data.get('medical_costs', 25000)
        
        # Permanent disability
        features['permanent_disability'] = 1 if case_data.get('permanent_disability', False) else 0
        
        # Surgery required
        features['surgery_required'] = 1 if case_data.get('surgery_required', False) else 0
        
        # Hospitalization days
        features['hospital_days'] = case_data.get('hospital_days', 3)
        
        # Pain scale (1-10)
        features['pain_level'] = case_data.get('pain_level', 5)
        
        return features
    
    def extract_patient_features(self, case_data: Dict) -> Dict[str, float]:
        """
        Extract patient demographic features.
        
        Args:
            case_data: Dict with patient information
            
        Returns:
            Dict of patient features
        """
        features = {}
        
        # Age
        age = case_data.get('age', 45)
        features['age'] = age
        features['age_squared'] = age ** 2  # Non-linear age effect
        
        # Employment status
        features['employed'] = 1 if case_data.get('employed', True) else 0
        
        # Income (log-transformed to handle wide range)
        income = case_data.get('annual_income', 50000)
        features['log_income'] = np.log1p(income)
        
        # Dependents
        features['num_dependents'] = case_data.get('num_dependents', 0)
        
        # Veteran status
        features['is_veteran'] = 1 if case_data.get('is_veteran', False) else 0
        
        # Disability rating (for veterans)
        features['disability_rating'] = case_data.get('disability_rating', 0) / 100
        
        return features
    
    def extract_legal_features(self, case_data: Dict) -> Dict[str, float]:
        """
        Extract legal/liability features.
        
        Args:
            case_data: Dict with legal information
            
        Returns:
            Dict of legal features
        """
        features = {}
        
        # Liability strength (0-1, where 1 = clear liability)
        features['liability_strength'] = case_data.get('liability_strength', 0.7)
        
        # Comparative negligence (% plaintiff fault)
        features['comparative_negligence'] = case_data.get('comparative_negligence', 0.0)
        
        # Statute of limitations proximity (days until expiration)
        features['statute_days_remaining'] = case_data.get('statute_days_remaining', 365)
        
        # Number of defendants
        features['num_defendants'] = case_data.get('num_defendants', 1)
        
        # Insurance coverage available
        features['insurance_coverage'] = case_data.get('insurance_coverage', 100000)
        
        # Witnesses available
        features['num_witnesses'] = case_data.get('num_witnesses', 2)
        
        # Documentation quality (1-10)
        features['doc_quality'] = case_data.get('documentation_quality', 7)
        
        return features
    
    def extract_geographic_features(self, case_data: Dict) -> Dict[str, float]:
        """
        Extract geographic/venue features.
        
        Args:
            case_data: Dict with location information
            
        Returns:
            Dict of geographic features
        """
        features = {}
        
        # State (one-hot encode top states)
        state = case_data.get('state', 'UNKNOWN')
        
        # Top plaintiff-friendly states
        plaintiff_friendly_states = ['CA', 'NY', 'IL', 'FL', 'TX']
        features['plaintiff_friendly_state'] = 1 if state in plaintiff_friendly_states else 0
        
        # Urban vs rural
        features['is_urban'] = 1 if case_data.get('is_urban', True) else 0
        
        # State one-hot (top 5 states)
        for s in plaintiff_friendly_states:
            features[f'state_{s}'] = 1 if state == s else 0
        
        return features
    
    def extract_case_complexity_features(self, case_data: Dict) -> Dict[str, float]:
        """
        Extract case complexity features.
        
        Args:
            case_data: Dict with case details
            
        Returns:
            Dict of complexity features
        """
        features = {}
        
        # Expert witnesses needed
        features['num_expert_witnesses'] = case_data.get('num_expert_witnesses', 1)
        
        # Medical reports
        features['num_medical_reports'] = case_data.get('num_medical_reports', 3)
        
        # Pre-existing conditions
        features['has_preexisting'] = 1 if case_data.get('has_preexisting_conditions', False) else 0
        
        # Case type (encode common types)
        case_type = case_data.get('case_type', 'OTHER')
        case_types = ['CAR_ACCIDENT', 'SLIP_FALL', 'MEDICAL_MALPRACTICE', 'PRODUCT_LIABILITY', 'WORKPLACE']
        
        for ct in case_types:
            features[f'type_{ct}'] = 1 if case_type == ct else 0
        
        # Discovery disputes
        features['num_discovery_disputes'] = case_data.get('num_discovery_disputes', 0)
        
        return features
    
    def extract_all_features(self, case_data: Dict) -> pd.DataFrame:
        """
        Extract all features from case data.
        
        Args:
            case_data: Complete case information dict
            
        Returns:
            DataFrame with one row containing all features
        """
        all_features = {}
        
        # Combine all feature groups
        all_features.update(self.extract_injury_features(case_data))
        all_features.update(self.extract_patient_features(case_data))
        all_features.update(self.extract_legal_features(case_data))
        all_features.update(self.extract_geographic_features(case_data))
        all_features.update(self.extract_case_complexity_features(case_data))
        
        # Derived features
        all_features['severity_x_liability'] = (
            all_features.get('injury_severity', 5) * 
            all_features.get('liability_strength', 0.7)
        )
        
        all_features['costs_per_day'] = (
            all_features.get('medical_costs', 25000) / 
            max(all_features.get('treatment_days', 90), 1)
        )
        
        # Store feature names
        self.feature_names = sorted(all_features.keys())
        
        # Convert to DataFrame
        return pd.DataFrame([all_features])
    
    def extract_batch_features(self, cases: List[Dict]) -> pd.DataFrame:
        """
        Extract features from multiple cases.
        
        Args:
            cases: List of case data dicts
            
        Returns:
            DataFrame with features for all cases
        """
        features_list = []
        
        for case in cases:
            features = self.extract_all_features(case)
            features_list.append(features)
        
        # Concatenate all features
        df = pd.concat(features_list, ignore_index=True)
        
        logger.info(f"✓ Extracted {len(self.feature_names)} features for {len(cases)} cases")
        
        return df
    
    def get_feature_importance_groups(self) -> Dict[str, List[str]]:
        """
        Get features grouped by category.
        
        Returns:
            Dict mapping category to feature names
        """
        groups = {
            'injury': [f for f in self.feature_names if any(x in f for x in ['injury', 'severity', 'pain', 'disability', 'surgery', 'hospital'])],
            'patient': [f for f in self.feature_names if any(x in f for x in ['age', 'income', 'employed', 'dependents', 'veteran'])],
            'legal': [f for f in self.feature_names if any(x in f for x in ['liability', 'negligence', 'statute', 'defendant', 'insurance', 'witness', 'doc'])],
            'geographic': [f for f in self.feature_names if any(x in f for x in ['state', 'urban', 'friendly'])],
            'complexity': [f for f in self.feature_names if any(x in f for x in ['expert', 'report', 'preexisting', 'type_', 'discovery'])],
            'derived': [f for f in self.feature_names if any(x in f for x in ['_x_', '_per_', 'squared'])]
        }
        
        return groups


if __name__ == "__main__":
    # Test feature engineering
    engineer = FeatureEngineer()
    
    # Example case
    test_case = {
        'injury_severity': 8,
        'treatment_duration_days': 180,
        'medical_costs': 75000,
        'permanent_disability': True,
        'surgery_required': True,
        'hospital_days': 14,
        'pain_level': 9,
        'age': 55,
        'employed': True,
        'annual_income': 65000,
        'num_dependents': 2,
        'is_veteran': True,
        'disability_rating': 40,
        'liability_strength': 0.9,
        'comparative_negligence': 0.1,
        'statute_days_remaining': 450,
        'num_defendants': 2,
        'insurance_coverage': 250000,
        'num_witnesses': 5,
        'documentation_quality': 9,
        'state': 'CA',
        'is_urban': True,
        'num_expert_witnesses': 3,
        'num_medical_reports': 8,
        'has_preexisting_conditions': False,
        'case_type': 'CAR_ACCIDENT',
        'num_discovery_disputes': 1
    }
    
    # Extract features
    features = engineer.extract_all_features(test_case)
    
    print("="*70)
    print("FEATURE ENGINEERING TEST")
    print("="*70)
    print(f"\n✓ Extracted {len(features.columns)} features:")
    print(features.T)
    
    # Show feature groups
    print("\n" + "="*70)
    print("FEATURE GROUPS")
    print("="*70)
    
    groups = engineer.get_feature_importance_groups()
    for group_name, feature_list in groups.items():
        print(f"\n{group_name.upper()} ({len(feature_list)} features):")
        for feature in feature_list[:5]:
            print(f"  - {feature}")
        if len(feature_list) > 5:
            print(f"  ... and {len(feature_list) - 5} more")
