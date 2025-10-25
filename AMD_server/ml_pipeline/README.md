# ML Pipeline for Document Classification

Complete machine learning pipeline for training document classifiers on legal documents.

## 📁 Directory Structure

```
ml_pipeline/
├── __init__.py                          # Package init
├── data_loader.py                       # Load data from PostgreSQL
├── feature_engineering.py               # Text → ML features
├── train_test_split.py                  # Create data splits
├── train.py                             # ⭐ Main training script
├── models/
│   ├── __init__.py
│   └── document_classifier.py           # Classification models
├── trained_models/                      # Output directory
│   ├── document_classifier.pkl          # Trained model
│   ├── document_classifier_metrics.json # Evaluation metrics
│   ├── feature_extractor.pkl            # TF-IDF + Label encoder
│   └── split_indices.pkl                # Train/val/test splits
└── README.md                            # This file
```

## 🚀 Quick Start

### Train a Model (One Command)

```bash
cd AMD_server/ml_pipeline
python train.py
```

This will:
1. ✅ Load 54 Morgan & Morgan documents from PostgreSQL
2. ✅ Create stratified train/val/test splits (70/15/15)
3. ✅ Extract TF-IDF features (500 dimensions)
4. ✅ Train Random Forest classifier
5. ✅ Evaluate on test set
6. ✅ Save model and metrics to `trained_models/`

### Use the Trained Model

```python
from ml_pipeline.models.document_classifier import DocumentClassifier
from ml_pipeline.feature_engineering import FeatureExtractor

# Load model and feature extractor
classifier = DocumentClassifier.load('trained_models/document_classifier.pkl')
extractor = FeatureExtractor.load('trained_models/feature_extractor.pkl')

# Classify a new document
text = "This is a settlement offer for $50,000..."
features = extractor.transform_tfidf([text])
prediction_encoded = classifier.predict(features)[0]
prediction = extractor.inverse_transform_labels([prediction_encoded])[0]

print(f"Document type: {prediction}")
```

## 📚 Component Usage

### 1. Data Loader

```python
from ml_pipeline.data_loader import DataLoader

# Initialize
loader = DataLoader()

# Load Morgan & Morgan documents
df = loader.load_morgan_documents()
print(f"Loaded {len(df)} documents")

# Quick classification data
X, y = loader.get_classification_data()
```

**Data source**: PostgreSQL `legal_data.documents` table (session_id=5)  
**Columns**: `document_id`, `case_id`, `document_type`, `file_name`, `full_text`  
**Size**: 54 documents, 11 document types

### 2. Feature Engineering

```python
from ml_pipeline.feature_engineering import prepare_features
from sklearn.model_selection import train_test_split

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# Prepare features (TF-IDF + Label encoding)
X_train_feat, X_test_feat, y_train_enc, y_test_enc, extractor = prepare_features(
    X_train, X_test, y_train, y_test,
    max_features=500,  # TF-IDF vocabulary size
    clean_text=True    # Clean legal text
)

# Save extractor for later use
extractor.save('feature_extractor.pkl')
```

**Features**:
- Text cleaning (lowercase, remove special chars, normalize whitespace)
- TF-IDF vectorization (unigrams + bigrams)
- Label encoding (string → integer)
- Reproducible (save/load transformers)

### 3. Train/Test Splits

```python
from ml_pipeline.train_test_split import DataSplitter

# Create stratified splits
splitter = DataSplitter(random_state=42)
X_train, X_val, X_test, y_train, y_val, y_test = splitter.create_splits(
    X, y,
    test_size=0.15,   # 15% for test
    val_size=0.15,    # 15% for validation
    stratify=True     # Maintain class distribution
)

# Save splits for reproducibility
splitter.save_split_indices('split_indices.pkl')

# Load and reapply later
splitter2 = DataSplitter()
splitter2.load_split_indices('split_indices.pkl')
X_train, X_val, X_test, y_train, y_val, y_test = splitter2.apply_saved_split(X, y)
```

**For small datasets** (< 100 samples), use cross-validation:

```python
from ml_pipeline.train_test_split import get_cross_validation_folds

folds = get_cross_validation_folds(X, y, n_folds=5)
for train_idx, val_idx in folds.split(X, y):
    X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
    y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
    # Train and evaluate
```

### 4. Model Training

```python
from ml_pipeline.models.document_classifier import DocumentClassifier

# Train Random Forest (default)
classifier = DocumentClassifier(model_type='random_forest')
classifier.fit(X_train_features, y_train_encoded)

# Evaluate
metrics = classifier.evaluate(
    X_test_features, 
    y_test_encoded,
    class_names=['Settlement Offer', 'Police Report', ...]
)

print(f"Accuracy: {metrics['accuracy']:.3f}")

# Save model
classifier.save('my_model.pkl', metrics=metrics)
```

**Supported models**:
- `random_forest` - Good balance, robust (default)
- `logistic_regression` - Fast, interpretable
- `gradient_boosting` - Often best accuracy
- `linear_svc` - Good for text classification

### 5. Inference

```python
# Load saved model
classifier = DocumentClassifier.load('trained_models/document_classifier.pkl')
extractor = FeatureExtractor.load('trained_models/feature_extractor.pkl')

# Classify new text
def classify_document(text: str) -> str:
    # Extract features
    features = extractor.transform_tfidf([text])
    
    # Predict
    prediction_encoded = classifier.predict(features)[0]
    prediction = extractor.inverse_transform_labels([prediction_encoded])[0]
    
    return prediction

# Use it
doc_type = classify_document("SETTLEMENT OFFER: $75,000 for case #12345")
print(f"Document type: {doc_type}")
```

## 📊 Model Performance

**Dataset**: 54 Morgan & Morgan documents  
**Classes**: 11 document types  
**Split**: 70% train, 15% val, 15% test  
**Features**: TF-IDF (500 dimensions, unigrams + bigrams)

**Expected Performance** (on 8 test documents):
- Accuracy: 75-90%
- Depends on class balance and text quality

**Class distribution** (from actual data):
```
Police Report: 5 docs
Settlement Offer: 8 docs
Property Damage: 7 docs
Medical Lien: 4 docs
...
```

## 🔧 Customization

### Change Model Type

```python
# Try different models
classifier = DocumentClassifier(model_type='logistic_regression')
classifier = DocumentClassifier(model_type='gradient_boosting')
classifier = DocumentClassifier(model_type='linear_svc')
```

### Adjust TF-IDF Parameters

```python
extractor = FeatureExtractor()
extractor.fit_tfidf(
    texts,
    max_features=1000,      # More features
    ngram_range=(1, 3),     # Unigrams, bigrams, trigrams
    min_df=2,               # Ignore rare words
    max_df=0.8              # Ignore common words
)
```

### Hyperparameter Tuning

```python
from sklearn.model_selection import GridSearchCV

# Define parameter grid
param_grid = {
    'n_estimators': [50, 100, 200],
    'max_depth': [None, 10, 20],
    'min_samples_split': [2, 5, 10]
}

# Grid search
from sklearn.ensemble import RandomForestClassifier
rf = RandomForestClassifier()
grid_search = GridSearchCV(rf, param_grid, cv=5, scoring='accuracy')
grid_search.fit(X_train_features, y_train_encoded)

print(f"Best params: {grid_search.best_params_}")
print(f"Best accuracy: {grid_search.best_score_:.3f}")
```

## 🎯 Integration with Agents

### Evidence Sorter Agent

```python
from ml_pipeline.models.document_classifier import DocumentClassifier
from ml_pipeline.feature_engineering import FeatureExtractor

class EvidenceSorterAgent:
    def __init__(self):
        self.classifier = DocumentClassifier.load('trained_models/document_classifier.pkl')
        self.extractor = FeatureExtractor.load('trained_models/feature_extractor.pkl')
    
    def classify_document(self, extracted_text: str) -> str:
        """Classify a legal document"""
        features = self.extractor.transform_tfidf([extracted_text])
        prediction_encoded = self.classifier.predict(features)[0]
        document_type = self.extractor.inverse_transform_labels([prediction_encoded])[0]
        return document_type
```

## 📈 Next Steps

### 1. Add More Data
- ✅ Morgan & Morgan: 54 docs (done)
- 🔄 Kaggle Document OCR: +400K images (augmentation)
- 🔄 Synthetic data generation

### 2. Improve Features
- ✅ TF-IDF (done)
- 🔄 Word embeddings (sentence-transformers)
- 🔄 BERT features

### 3. Better Models
- ✅ Random Forest (done)
- 🔄 Fine-tuned BERT
- 🔄 Ensemble methods

### 4. Production Deployment
- ✅ Save/load models (done)
- 🔄 FastAPI inference server
- 🔄 Docker container
- 🔄 Model monitoring

## 🐛 Troubleshooting

### Database Connection Failed
```
Solution: Check that you're running on the AMD server or have SSH tunnel:
ssh -L 5432:localhost:5432 amd-knights@134.199.202.8
```

### Low Accuracy
```
Possible causes:
1. Small dataset (54 docs) - use cross-validation
2. Class imbalance - use class weights
3. Noisy text - improve cleaning
4. Need more features - increase max_features or try embeddings
```

### Import Errors
```bash
# Install required packages
pip install scikit-learn pandas numpy psycopg2-binary
```

## 📝 Files Generated

After training, you'll have:

- `trained_models/document_classifier.pkl` - Trained model (sklearn)
- `trained_models/document_classifier_metrics.json` - Performance metrics
- `trained_models/feature_extractor.pkl` - TF-IDF + Label encoder
- `trained_models/split_indices.pkl` - Train/val/test indices

## 🎓 Learn More

- [scikit-learn Documentation](https://scikit-learn.org/stable/)
- [TF-IDF Explained](https://en.wikipedia.org/wiki/Tf%E2%80%93idf)
- [Text Classification Tutorial](https://scikit-learn.org/stable/tutorial/text_analytics/working_with_text_data.html)

---

**Questions?** Check the code comments or run with `--help` flag.
