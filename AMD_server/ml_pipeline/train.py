#!/usr/bin/env python3
"""
End-to-End Training Script for Document Classifier
This script demonstrates the complete ML pipeline from data loading to model deployment
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml_pipeline.data_loader import DataLoader
from ml_pipeline.feature_engineering import prepare_features
from ml_pipeline.train_test_split import DataSplitter
from ml_pipeline.models.document_classifier import train_document_classifier
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    """
    Complete training pipeline:
    1. Load Morgan & Morgan documents from PostgreSQL
    2. Create train/val/test splits
    3. Extract TF-IDF features
    4. Train Random Forest classifier
    5. Evaluate on test set
    6. Save model and metrics
    """
    
    print("\n" + "=" * 80)
    print("DOCUMENT CLASSIFICATION TRAINING PIPELINE")
    print("=" * 80)
    
    # Configuration
    OUTPUT_DIR = Path(__file__).parent.parent / "trained_models"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    MODEL_PATH = OUTPUT_DIR / "document_classifier.pkl"
    SPLIT_INDICES_PATH = OUTPUT_DIR / "split_indices.pkl"
    FEATURE_EXTRACTOR_PATH = OUTPUT_DIR / "feature_extractor.pkl"
    
    logger.info(f"Output directory: {OUTPUT_DIR}")
    
    # Step 1: Load Data
    logger.info("\n" + "=" * 80)
    logger.info("STEP 1: LOADING DATA")
    logger.info("=" * 80)
    
    loader = DataLoader()
    X, y = loader.get_classification_data()
    
    logger.info(f"✅ Loaded {len(X)} documents")
    logger.info(f"✅ {y.nunique()} document types")
    
    # Step 2: Create Splits
    logger.info("\n" + "=" * 80)
    logger.info("STEP 2: CREATING TRAIN/VAL/TEST SPLITS")
    logger.info("=" * 80)
    
    splitter = DataSplitter(random_state=42)
    X_train, X_val, X_test, y_train, y_val, y_test = splitter.create_splits(
        X, y,
        test_size=0.15,
        val_size=0.15,
        stratify=True
    )
    
    # Save split indices for reproducibility
    splitter.save_split_indices(str(SPLIT_INDICES_PATH))
    
    # Step 3: Feature Engineering
    logger.info("\n" + "=" * 80)
    logger.info("STEP 3: FEATURE ENGINEERING")
    logger.info("=" * 80)
    
    X_train_features, X_val_features, y_train_encoded, y_val_encoded, feature_extractor = prepare_features(
        X_train, X_val, y_train, y_val,
        max_features=500,
        clean_text=True
    )
    
    # Also prepare test features
    X_test_features = feature_extractor.transform_tfidf(X_test.tolist())
    y_test_encoded = feature_extractor.transform_labels(y_test)
    
    # Save feature extractor
    feature_extractor.save(str(FEATURE_EXTRACTOR_PATH))
    
    # Step 4: Train Model
    logger.info("\n" + "=" * 80)
    logger.info("STEP 4: TRAINING MODEL")
    logger.info("=" * 80)
    
    classifier, metrics = train_document_classifier(
        X_train_features,
        y_train_encoded,
        X_test_features,
        y_test_encoded,
        model_type='random_forest',
        class_names=feature_extractor.label_encoder.classes_.tolist(),
        save_path=str(MODEL_PATH)
    )
    
    # Step 5: Final Results
    logger.info("\n" + "=" * 80)
    logger.info("TRAINING COMPLETE")
    logger.info("=" * 80)
    
    logger.info(f"\n📊 FINAL RESULTS:")
    logger.info(f"   Accuracy: {metrics['accuracy']:.4f}")
    logger.info(f"   Precision (avg): {sum(metrics['precision']) / len(metrics['precision']):.4f}")
    logger.info(f"   Recall (avg): {sum(metrics['recall']) / len(metrics['recall']):.4f}")
    logger.info(f"   F1 (avg): {sum(metrics['f1']) / len(metrics['f1']):.4f}")
    
    logger.info(f"\n💾 SAVED ARTIFACTS:")
    logger.info(f"   Model: {MODEL_PATH}")
    logger.info(f"   Metrics: {str(MODEL_PATH).replace('.pkl', '_metrics.json')}")
    logger.info(f"   Feature Extractor: {FEATURE_EXTRACTOR_PATH}")
    logger.info(f"   Split Indices: {SPLIT_INDICES_PATH}")
    
    logger.info(f"\n✅ Training pipeline completed successfully!")
    
    # Step 6: Demo Inference
    logger.info("\n" + "=" * 80)
    logger.info("DEMO INFERENCE")
    logger.info("=" * 80)
    
    # Take first test sample
    sample_text = X_test.iloc[0]
    true_label = y_test.iloc[0]
    
    # Prepare sample
    sample_features = feature_extractor.transform_tfidf([sample_text])
    
    # Predict
    prediction_encoded = classifier.predict(sample_features)[0]
    prediction = feature_extractor.inverse_transform_labels([prediction_encoded])[0]
    
    logger.info(f"\nSample document:")
    logger.info(f"Text preview: {sample_text[:200]}...")
    logger.info(f"True label: {true_label}")
    logger.info(f"Predicted label: {prediction}")
    logger.info(f"Match: {'✅ Correct!' if prediction == true_label else '❌ Incorrect'}")
    
    # Get probabilities if available
    if hasattr(classifier.model, 'predict_proba'):
        proba = classifier.predict_proba(sample_features)[0]
        logger.info(f"\nTop 3 predictions:")
        top_3_idx = proba.argsort()[-3:][::-1]
        for idx in top_3_idx:
            class_name = feature_extractor.label_encoder.classes_[idx]
            confidence = proba[idx]
            logger.info(f"   {class_name}: {confidence:.4f}")


if __name__ == "__main__":
    main()
