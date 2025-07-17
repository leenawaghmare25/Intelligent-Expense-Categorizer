"""Training script for the lightweight ensemble expense categorization models."""

import pandas as pd
import os
import logging
import sys
from sklearn.metrics import classification_report

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from PYTHON.ml_models import EnsembleExpenseClassifier

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
        df['Description'] = df['Description'].str.strip()
        
        # Remove any null values
        df = df.dropna(subset=['Description', 'Category'])
        
        # Remove duplicates
        df = df.drop_duplicates(subset=['Description', 'Category'])
        
        logging.info(f"Data after preprocessing. Shape: {df.shape}")
        logging.info(f"Categories: {sorted(df['Category'].unique())}")
        logging.info(f"Category distribution:\n{df['Category'].value_counts()}")
        
        return df
    except Exception as e:
        logging.error(f"Error loading data: {str(e)}")
        raise

def train_ensemble_model(df):
    """Train the ensemble expense categorization model."""
    try:
        logging.info("Starting ensemble model training...")
        
        # Features and labels
        X = df['Description'].tolist()
        y = df['Category'].tolist()
        
        # Initialize and train ensemble
        ensemble = EnsembleExpenseClassifier()
        ensemble.fit(X, y)
        
        logging.info("Ensemble model training completed successfully!")
        
        return ensemble
        
    except Exception as e:
        logging.error(f"Error training ensemble model: {str(e)}")
        raise

def evaluate_model(ensemble, df):
    """Evaluate the trained ensemble model."""
    try:
        logging.info("Evaluating ensemble model...")
        
        X = df['Description'].tolist()
        y = df['Category'].tolist()
        
        # Get predictions
        predictions = ensemble.predict(X)
        
        # Generate classification report
        report = classification_report(y, predictions, zero_division=0)
        logging.info(f"\nEnsemble Classification Report:\n{report}")
        
        # Test detailed prediction on a few examples
        logging.info("\nDetailed prediction examples:")
        for i, (desc, true_cat) in enumerate(zip(X[:5], y[:5])):
            detailed = ensemble.get_detailed_prediction(desc)
            logging.info(f"\nExample {i+1}: '{desc}'")
            logging.info(f"True category: {true_cat}")
            logging.info(f"Ensemble prediction: {detailed['ensemble_prediction']} (confidence: {detailed['ensemble_confidence']:.3f})")
            for model_name, pred_info in detailed['individual_models'].items():
                logging.info(f"  {model_name}: {pred_info['prediction']} (confidence: {pred_info['confidence']:.3f})")
        
    except Exception as e:
        logging.error(f"Error evaluating model: {str(e)}")
        raise

def main():
    """Main training pipeline."""
    try:
        # Load and preprocess data
        df = load_and_preprocess_data()
        
        # Train ensemble model
        ensemble = train_ensemble_model(df)
        
        # Evaluate model
        evaluate_model(ensemble, df)
        
        # Save ensemble model
        ensemble.save_models()
        
        logging.info("Training pipeline completed successfully!")
        logging.info(f"Models saved to: {Config.MODEL_DIR}")
        
    except Exception as e:
        logging.error(f"Training pipeline failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
