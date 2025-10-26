"""
Structured Data Pipeline Tests

Tests data loading, feature engineering, settlement prediction, and case matching.
"""

import sys
from pathlib import Path
import unittest
import numpy as np
import pandas as pd

# Add parent directory
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ml_pipeline.structured import (
    DataLoader,
    FeatureEngineer,
    SettlementPredictor,
    CaseMatcher
)


class TestDataLoader(unittest.TestCase):
    """Test data loading functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.loader = DataLoader()
    
    def test_initialization(self):
        """Test loader initializes correctly."""
        self.assertIsNotNone(self.loader)
        print("✓ Data Loader initialized")
    
    def test_load_vha_hospitals(self):
        """Test VHA hospitals dataset loading."""
        df = self.loader.load_vha_hospitals()
        
        self.assertIsInstance(df, pd.DataFrame)
        self.assertGreater(len(df), 0)
        self.assertIn('hospital_id', df.columns)
        
        print(f"✓ VHA Hospitals loaded: {len(df)} rows")
    
    def test_load_us_hospitals(self):
        """Test US hospitals dataset loading."""
        df = self.loader.load_us_hospitals()
        
        self.assertIsInstance(df, pd.DataFrame)
        self.assertGreater(len(df), 0)
        
        print(f"✓ US Hospitals loaded: {len(df)} rows")
    
    def test_load_veterans_employment(self):
        """Test veterans employment dataset."""
        df = self.loader.load_veterans_employment()
        
        self.assertIsInstance(df, pd.DataFrame)
        self.assertGreater(len(df), 0)
        
        print(f"✓ Veterans Employment loaded: {len(df)} rows")
    
    def test_load_lung_cancer(self):
        """Test lung cancer dataset."""
        df = self.loader.load_lung_cancer()
        
        self.assertIsInstance(df, pd.DataFrame)
        self.assertGreater(len(df), 0)
        
        print(f"✓ Lung Cancer loaded: {len(df)} rows")
    
    def test_load_all_datasets(self):
        """Test loading all datasets at once."""
        datasets = self.loader.load_all_datasets()
        
        self.assertEqual(len(datasets), 4)
        self.assertIn('vha_hospitals', datasets)
        self.assertIn('us_hospitals', datasets)
        self.assertIn('veterans_employment', datasets)
        self.assertIn('lung_cancer', datasets)
        
        total_rows = sum(len(df) for df in datasets.values())
        print(f"✓ All datasets loaded: {total_rows:,} total rows")
    
    def test_get_summary(self):
        """Test dataset summary statistics."""
        summary = self.loader.get_summary()
        
        self.assertIsInstance(summary, dict)
        self.assertEqual(len(summary), 4)
        
        print(f"✓ Dataset summary generated")
        for name, stats in summary.items():
            print(f"  {name}: {stats['rows']} rows, {stats['columns']} cols")


class TestFeatureEngineer(unittest.TestCase):
    """Test feature engineering."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engineer = FeatureEngineer()
        
        # Sample case data
        self.test_case = {
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
    
    def test_initialization(self):
        """Test engineer initializes."""
        self.assertIsNotNone(self.engineer)
        print("✓ Feature Engineer initialized")
    
    def test_extract_injury_features(self):
        """Test injury feature extraction."""
        features = self.engineer.extract_injury_features(self.test_case)
        
        self.assertIsInstance(features, dict)
        self.assertIn('injury_severity', features)
        self.assertIn('medical_costs', features)
        self.assertEqual(features['injury_severity'], 8)
        
        print(f"✓ Extracted {len(features)} injury features")
    
    def test_extract_patient_features(self):
        """Test patient feature extraction."""
        features = self.engineer.extract_patient_features(self.test_case)
        
        self.assertIsInstance(features, dict)
        self.assertIn('age', features)
        self.assertIn('age_squared', features)
        self.assertIn('log_income', features)
        
        print(f"✓ Extracted {len(features)} patient features")
    
    def test_extract_legal_features(self):
        """Test legal feature extraction."""
        features = self.engineer.extract_legal_features(self.test_case)
        
        self.assertIsInstance(features, dict)
        self.assertIn('liability_strength', features)
        self.assertIn('insurance_coverage', features)
        
        print(f"✓ Extracted {len(features)} legal features")
    
    def test_extract_geographic_features(self):
        """Test geographic feature extraction."""
        features = self.engineer.extract_geographic_features(self.test_case)
        
        self.assertIsInstance(features, dict)
        self.assertIn('state_CA', features)
        self.assertEqual(features['state_CA'], 1)
        
        print(f"✓ Extracted {len(features)} geographic features")
    
    def test_extract_all_features(self):
        """Test complete feature extraction."""
        features = self.engineer.extract_all_features(self.test_case)
        
        self.assertIsInstance(features, pd.DataFrame)
        self.assertEqual(len(features), 1)
        self.assertGreater(len(features.columns), 30)
        
        print(f"✓ Extracted {len(features.columns)} total features")
        print(f"  Feature names: {list(features.columns)[:10]}...")
    
    def test_extract_batch_features(self):
        """Test batch feature extraction."""
        cases = [self.test_case] * 5
        features = self.engineer.extract_batch_features(cases)
        
        self.assertIsInstance(features, pd.DataFrame)
        self.assertEqual(len(features), 5)
        
        print(f"✓ Batch extracted features for {len(features)} cases")
    
    def test_feature_groups(self):
        """Test feature grouping."""
        self.engineer.extract_all_features(self.test_case)
        groups = self.engineer.get_feature_importance_groups()
        
        self.assertIsInstance(groups, dict)
        self.assertIn('injury', groups)
        self.assertIn('patient', groups)
        self.assertIn('legal', groups)
        
        print(f"✓ Feature groups: {list(groups.keys())}")


class TestSettlementPredictor(unittest.TestCase):
    """Test settlement prediction."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.predictor = SettlementPredictor()
        self.engineer = FeatureEngineer()
        
        # Generate synthetic training data
        np.random.seed(42)
        self.n_samples = 100
        
        self.cases = []
        self.settlements = []
        
        for i in range(self.n_samples):
            severity = np.random.randint(1, 11)
            medical_costs = np.random.randint(10000, 200000)
            liability = np.random.uniform(0.5, 1.0)
            
            case = {
                'injury_severity': severity,
                'medical_costs': medical_costs,
                'liability_strength': liability,
                'treatment_duration_days': np.random.randint(30, 365),
                'permanent_disability': np.random.choice([True, False]),
                'age': np.random.randint(25, 75),
                'annual_income': np.random.randint(30000, 150000),
                'state': np.random.choice(['CA', 'NY', 'TX']),
                'case_type': np.random.choice(['CAR_ACCIDENT', 'SLIP_FALL'])
            }
            
            # Settlement formula
            settlement = medical_costs * 2 * (severity / 5) * liability
            settlement += np.random.normal(0, settlement * 0.1)
            settlement = max(settlement, 5000)
            
            self.cases.append(case)
            self.settlements.append(settlement)
    
    def test_initialization(self):
        """Test predictor initializes."""
        self.assertIsNotNone(self.predictor)
        print("✓ Settlement Predictor initialized")
    
    def test_training(self):
        """Test model training."""
        X = self.engineer.extract_batch_features(self.cases)
        y = np.array(self.settlements)
        
        metrics = self.predictor.train(X, y, test_size=0.2)
        
        self.assertIsInstance(metrics, dict)
        self.assertIn('test_r2', metrics)
        self.assertIn('test_mae', metrics)
        
        print(f"✓ Model trained successfully")
        print(f"  Test R²: {metrics['test_r2']:.3f}")
        print(f"  Test MAE: ${metrics['test_mae']:,.0f}")
    
    def test_prediction(self):
        """Test settlement prediction."""
        # Train first
        X = self.engineer.extract_batch_features(self.cases)
        y = np.array(self.settlements)
        self.predictor.train(X, y, test_size=0.2)
        
        # Predict on new case
        test_case = {
            'injury_severity': 7,
            'medical_costs': 100000,
            'liability_strength': 0.85,
            'age': 45,
            'state': 'CA',
            'case_type': 'CAR_ACCIDENT'
        }
        
        features = self.engineer.extract_all_features(test_case)
        prediction = self.predictor.predict(features)
        
        self.assertIsInstance(prediction, (int, float, np.number))
        self.assertGreater(prediction, 0)
        
        print(f"✓ Prediction: ${prediction:,.0f}")
    
    def test_prediction_with_confidence(self):
        """Test prediction with confidence interval."""
        X = self.engineer.extract_batch_features(self.cases)
        y = np.array(self.settlements)
        self.predictor.train(X, y, test_size=0.2)
        
        test_features = self.engineer.extract_all_features(self.cases[0])
        result = self.predictor.predict_with_confidence(test_features)
        
        self.assertIsInstance(result, dict)
        self.assertIn('prediction', result)
        self.assertIn('lower_bound', result)
        self.assertIn('upper_bound', result)
        
        print(f"✓ Prediction with confidence:")
        print(f"  Point estimate: ${result['prediction']:,.0f}")
        print(f"  95% CI: ${result['lower_bound']:,.0f} - ${result['upper_bound']:,.0f}")
    
    def test_batch_prediction(self):
        """Test batch prediction."""
        X = self.engineer.extract_batch_features(self.cases)
        y = np.array(self.settlements)
        self.predictor.train(X, y, test_size=0.2)
        
        test_features = self.engineer.extract_batch_features(self.cases[:10])
        predictions = self.predictor.predict_batch(test_features)
        
        self.assertEqual(len(predictions), 10)
        self.assertTrue(all(p >= 0 for p in predictions))
        
        print(f"✓ Batch predictions: {len(predictions)} cases")
    
    def test_feature_importance(self):
        """Test feature importance extraction."""
        X = self.engineer.extract_batch_features(self.cases)
        y = np.array(self.settlements)
        self.predictor.train(X, y, test_size=0.2)
        
        importance = self.predictor.get_feature_importance(top_k=10)
        
        self.assertIsInstance(importance, list)
        self.assertLessEqual(len(importance), 10)
        
        print(f"✓ Top 5 features:")
        for i, (feature, score) in enumerate(importance[:5], 1):
            print(f"  {i}. {feature}: {score:.4f}")


class TestCaseMatcher(unittest.TestCase):
    """Test case matching."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.matcher = CaseMatcher()
        self.engineer = FeatureEngineer()
        
        # Generate synthetic historical cases
        np.random.seed(42)
        self.n_cases = 50
        
        self.historical_features = []
        self.case_metadata = []
        
        for i in range(self.n_cases):
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
            
            features = self.engineer.extract_all_features(case)
            settlement = medical_costs * 2 * (severity / 5)
            
            self.historical_features.append(features)
            
            metadata = {
                'case_id': f"CASE-{i+1:04d}",
                'settlement_amount': settlement,
                'injury_severity': severity,
                'case_type': case['case_type']
            }
            self.case_metadata.append(metadata)
    
    def test_initialization(self):
        """Test matcher initializes."""
        self.assertIsNotNone(self.matcher)
        print("✓ Case Matcher initialized")
    
    def test_fit(self):
        """Test fitting matcher."""
        X = pd.concat(self.historical_features, ignore_index=True)
        
        self.matcher.fit(X, self.case_metadata, n_neighbors=5)
        
        self.assertIsNotNone(self.matcher.matcher)
        self.assertIsNotNone(self.matcher.scaler)
        
        print(f"✓ Matcher fitted on {len(X)} cases")
    
    def test_find_similar_cases(self):
        """Test finding similar cases."""
        X = pd.concat(self.historical_features, ignore_index=True)
        self.matcher.fit(X, self.case_metadata, n_neighbors=5)
        
        # New case
        new_case = {
            'injury_severity': 7,
            'medical_costs': 100000,
            'liability_strength': 0.85,
            'age': 45,
            'state': 'CA',
            'case_type': 'CAR_ACCIDENT'
        }
        
        new_features = self.engineer.extract_all_features(new_case)
        similar = self.matcher.find_similar_cases(new_features, k=5)
        
        self.assertEqual(len(similar), 5)
        self.assertIn('similarity_score', similar[0])
        self.assertIn('case_id', similar[0])
        
        print(f"✓ Found {len(similar)} similar cases")
        for i, case in enumerate(similar[:3], 1):
            print(f"  {i}. {case['case_id']}: similarity={case['similarity_score']:.3f}")
    
    def test_find_similar_settlements(self):
        """Test settlement statistics from similar cases."""
        X = pd.concat(self.historical_features, ignore_index=True)
        self.matcher.fit(X, self.case_metadata, n_neighbors=5)
        
        new_case = {
            'injury_severity': 7,
            'medical_costs': 100000,
            'age': 45,
            'state': 'CA',
            'case_type': 'CAR_ACCIDENT'
        }
        
        new_features = self.engineer.extract_all_features(new_case)
        stats = self.matcher.find_similar_settlements(new_features, k=10)
        
        self.assertIsInstance(stats, dict)
        self.assertIn('mean', stats)
        self.assertIn('median', stats)
        self.assertIn('n_cases', stats)
        
        print(f"✓ Settlement statistics from {stats['n_cases']} cases:")
        print(f"  Mean: ${stats['mean']:,.0f}")
        print(f"  Median: ${stats['median']:,.0f}")
        print(f"  Range: ${stats['min']:,.0f} - ${stats['max']:,.0f}")


def run_tests():
    """Run all structured data pipeline tests."""
    print("\n" + "="*70)
    print("STRUCTURED DATA PIPELINE TESTS")
    print("="*70 + "\n")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestDataLoader))
    suite.addTests(loader.loadTestsFromTestCase(TestFeatureEngineer))
    suite.addTests(loader.loadTestsFromTestCase(TestSettlementPredictor))
    suite.addTests(loader.loadTestsFromTestCase(TestCaseMatcher))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
