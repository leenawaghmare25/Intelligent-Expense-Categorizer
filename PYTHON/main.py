import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os
import logging
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('training.log'),
        logging.StreamHandler()
    ]
)

def load_and_preprocess_data():
    """Load and preprocess the data."""
    try:
        logging.info("Loading data...")
        df = pd.read_csv(Config.DATA_PATH)
        logging.info(f"Data loaded successfully. Shape: {df.shape}")
        
        # Preprocess
        df['Description'] = df['Description'].str.lower().str.strip()
        
        # Remove any null values
        df = df.dropna(subset=['Description', 'Category'])
        
        logging.info(f"Data after preprocessing. Shape: {df.shape}")
        logging.info(f"Categories: {df['Category'].unique()}")
        
        return df
    except Exception as e:
        logging.error(f"Error loading data: {str(e)}")
        raise

def train_model(df):
    """Train the expense categorization model."""
    try:
        logging.info("Starting model training...")
        
        # Features and labels
        X = df['Description']
        y = df['Category']
        
        # Split data for evaluation
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Vectorize
        vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        X_train_vec = vectorizer.fit_transform(X_train)
        X_test_vec = vectorizer.transform(X_test)
        
        # Train model
        model = LogisticRegression(
            max_iter=1000,
            random_state=42
        )
        model.fit(X_train_vec, y_train)
        
        # Evaluate model
        y_pred = model.predict(X_test_vec)
        accuracy = accuracy_score(y_test, y_pred)
        
        logging.info(f"Model trained successfully. Accuracy: {accuracy:.4f}")
        logging.info("\nClassification Report:")
        logging.info(classification_report(y_test, y_pred))
        
        return model, vectorizer
        
    except Exception as e:
        logging.error(f"Error training model: {str(e)}")
        raise

def save_model(model, vectorizer):
    """Save the trained model and vectorizer."""
    try:
        logging.info("Saving model and vectorizer...")
        
        os.makedirs(Config.MODEL_DIR, exist_ok=True)
        
        joblib.dump(model, Config.MODEL_PATH)
        joblib.dump(vectorizer, Config.VECTORIZER_PATH)
        
        logging.info("Model and vectorizer saved successfully.")
        
    except Exception as e:
        logging.error(f"Error saving model: {str(e)}")
        raise

def main():
    """Main training pipeline."""
    try:
        # Load and preprocess data
        df = load_and_preprocess_data()
        
        # Train model
        model, vectorizer = train_model(df)
        
        # Save model
        save_model(model, vectorizer)
        
        logging.info("Training pipeline completed successfully!")
        
    except Exception as e:
        logging.error(f"Training pipeline failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
