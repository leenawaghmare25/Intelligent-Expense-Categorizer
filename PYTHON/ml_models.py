"""Lightweight machine learning models for expense categorization."""

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, classification_report
import joblib
import os
import logging
import re
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Any
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class KeywordBasedClassifier:
    """Simple keyword-based classifier for expense categorization."""
    
    def __init__(self):
        self.category_keywords = {}
        self.categories = []
    
    def fit(self, X, y):
        """Train the keyword classifier."""
        self.categories = list(set(y))
        
        # Build keyword dictionary for each category
        category_texts = defaultdict(list)
        for text, category in zip(X, y):
            category_texts[category].append(text.lower())
        
        # Extract keywords for each category
        for category, texts in category_texts.items():
            all_text = ' '.join(texts)
            words = re.findall(r'\b\w+\b', all_text)
            word_counts = Counter(words)
            
            # Get top keywords (excluding common words)
            common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an'}
            keywords = [word for word, count in word_counts.most_common(20) 
                       if word not in common_words and len(word) > 2]
            
            self.category_keywords[category] = keywords[:10]  # Top 10 keywords
        
        return self
    
    def predict(self, X):
        """Predict categories based on keywords."""
        predictions = []
        
        for text in X:
            text_lower = text.lower()
            scores = {}
            
            for category, keywords in self.category_keywords.items():
                score = sum(1 for keyword in keywords if keyword in text_lower)
                scores[category] = score
            
            # Get category with highest score
            if scores and max(scores.values()) > 0:
                predicted_category = max(scores, key=scores.get)
            else:
                # Default to most common category if no keywords match
                predicted_category = self.categories[0] if self.categories else 'Other'
            
            predictions.append(predicted_category)
        
        return np.array(predictions)
    
    def predict_proba(self, X):
        """Predict probabilities for each category."""
        probabilities = []
        
        for text in X:
            text_lower = text.lower()
            scores = {}
            
            for category, keywords in self.category_keywords.items():
                score = sum(1 for keyword in keywords if keyword in text_lower)
                scores[category] = score
            
            # Normalize scores to probabilities
            total_score = sum(scores.values())
            if total_score > 0:
                probs = [scores.get(cat, 0) / total_score for cat in self.categories]
            else:
                # Uniform distribution if no matches
                probs = [1.0 / len(self.categories)] * len(self.categories)
            
            probabilities.append(probs)
        
        return np.array(probabilities)

class EnsembleExpenseClassifier:
    """Ensemble classifier combining multiple lightweight models."""
    
    def __init__(self, model_weights=None):
        self.model_weights = model_weights or Config.MODEL_WEIGHTS
        self.models = {}
        self.vectorizers = {}
        self.categories = []
        self.is_trained = False
    
    def _preprocess_text(self, text):
        """Preprocess text for better classification."""
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters but keep spaces
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
    
    def fit(self, X, y):
        """Train all models in the ensemble."""
        logging.info("Training ensemble models...")
        
        # Preprocess data
        X_processed = [self._preprocess_text(text) for text in X]
        self.categories = sorted(list(set(y)))
        
        # Split data for evaluation
        X_train, X_test, y_train, y_test = train_test_split(
            X_processed, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # 1. Naive Bayes with TF-IDF
        logging.info("Training Naive Bayes model...")
        self.vectorizers['naive_bayes'] = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=2
        )
        X_train_nb = self.vectorizers['naive_bayes'].fit_transform(X_train)
        X_test_nb = self.vectorizers['naive_bayes'].transform(X_test)
        
        self.models['naive_bayes'] = MultinomialNB(alpha=0.1)
        self.models['naive_bayes'].fit(X_train_nb, y_train)
        
        # Evaluate Naive Bayes
        nb_pred = self.models['naive_bayes'].predict(X_test_nb)
        nb_accuracy = accuracy_score(y_test, nb_pred)
        logging.info(f"Naive Bayes accuracy: {nb_accuracy:.4f}")
        
        # 2. Linear SVM with TF-IDF
        logging.info("Training SVM model...")
        self.vectorizers['svm'] = TfidfVectorizer(
            max_features=800,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=2
        )
        X_train_svm = self.vectorizers['svm'].fit_transform(X_train)
        X_test_svm = self.vectorizers['svm'].transform(X_test)
        
        self.models['svm'] = LinearSVC(C=0.1, random_state=42, max_iter=1000)
        self.models['svm'].fit(X_train_svm, y_train)
        
        # Evaluate SVM
        svm_pred = self.models['svm'].predict(X_test_svm)
        svm_accuracy = accuracy_score(y_test, svm_pred)
        logging.info(f"SVM accuracy: {svm_accuracy:.4f}")
        
        # 3. Keyword-based classifier
        logging.info("Training keyword-based model...")
        self.models['keyword'] = KeywordBasedClassifier()
        self.models['keyword'].fit(X_train, y_train)
        
        # Evaluate keyword model
        keyword_pred = self.models['keyword'].predict(X_test)
        keyword_accuracy = accuracy_score(y_test, keyword_pred)
        logging.info(f"Keyword model accuracy: {keyword_accuracy:.4f}")
        
        # Evaluate ensemble
        ensemble_pred = self.predict(X_test)
        ensemble_accuracy = accuracy_score(y_test, ensemble_pred)
        logging.info(f"Ensemble accuracy: {ensemble_accuracy:.4f}")
        
        self.is_trained = True
        return self
    
    def predict(self, X):
        """Predict using ensemble of models."""
        if not self.is_trained:
            raise ValueError("Models must be trained before prediction")
        
        X_processed = [self._preprocess_text(text) for text in X]
        predictions = []
        
        for text in X_processed:
            model_predictions = {}
            
            # Get predictions from each model
            # Naive Bayes
            text_nb = self.vectorizers['naive_bayes'].transform([text])
            nb_proba = self.models['naive_bayes'].predict_proba(text_nb)[0]
            model_predictions['naive_bayes'] = dict(zip(self.categories, nb_proba))
            
            # SVM (convert decision function to probabilities)
            text_svm = self.vectorizers['svm'].transform([text])
            svm_decision = self.models['svm'].decision_function(text_svm)[0]
            if len(self.categories) == 2:
                svm_proba = [1 / (1 + np.exp(-svm_decision)), 1 / (1 + np.exp(svm_decision))]
            else:
                # Softmax for multiclass
                exp_scores = np.exp(svm_decision - np.max(svm_decision))
                svm_proba = exp_scores / np.sum(exp_scores)
            model_predictions['svm'] = dict(zip(self.categories, svm_proba))
            
            # Keyword model
            keyword_proba = self.models['keyword'].predict_proba([text])[0]
            model_predictions['keyword'] = dict(zip(self.categories, keyword_proba))
            
            # Combine predictions using weighted voting
            final_scores = defaultdict(float)
            for model_name, weight in self.model_weights.items():
                if model_name in model_predictions:
                    for category, prob in model_predictions[model_name].items():
                        final_scores[category] += weight * prob
            
            # Get final prediction
            predicted_category = max(final_scores, key=final_scores.get)
            predictions.append(predicted_category)
        
        return np.array(predictions)
    
    def predict_proba(self, X):
        """Predict probabilities using ensemble."""
        if not self.is_trained:
            raise ValueError("Models must be trained before prediction")
        
        X_processed = [self._preprocess_text(text) for text in X]
        all_probabilities = []
        
        for text in X_processed:
            model_predictions = {}
            
            # Get predictions from each model
            # Naive Bayes
            text_nb = self.vectorizers['naive_bayes'].transform([text])
            nb_proba = self.models['naive_bayes'].predict_proba(text_nb)[0]
            model_predictions['naive_bayes'] = dict(zip(self.categories, nb_proba))
            
            # SVM
            text_svm = self.vectorizers['svm'].transform([text])
            svm_decision = self.models['svm'].decision_function(text_svm)[0]
            if len(self.categories) == 2:
                svm_proba = [1 / (1 + np.exp(-svm_decision)), 1 / (1 + np.exp(svm_decision))]
            else:
                exp_scores = np.exp(svm_decision - np.max(svm_decision))
                svm_proba = exp_scores / np.sum(exp_scores)
            model_predictions['svm'] = dict(zip(self.categories, svm_proba))
            
            # Keyword model
            keyword_proba = self.models['keyword'].predict_proba([text])[0]
            model_predictions['keyword'] = dict(zip(self.categories, keyword_proba))
            
            # Combine predictions using weighted voting
            final_scores = defaultdict(float)
            for model_name, weight in self.model_weights.items():
                if model_name in model_predictions:
                    for category, prob in model_predictions[model_name].items():
                        final_scores[category] += weight * prob
            
            # Convert to probability array
            probabilities = [final_scores[cat] for cat in self.categories]
            all_probabilities.append(probabilities)
        
        return np.array(all_probabilities)
    
    def get_detailed_prediction(self, text):
        """Get detailed prediction with individual model outputs."""
        if not self.is_trained:
            raise ValueError("Models must be trained before prediction")
        
        text_processed = self._preprocess_text(text)
        model_predictions = {}
        
        # Naive Bayes
        text_nb = self.vectorizers['naive_bayes'].transform([text_processed])
        nb_proba = self.models['naive_bayes'].predict_proba(text_nb)[0]
        nb_pred = self.categories[np.argmax(nb_proba)]
        model_predictions['naive_bayes'] = {
            'prediction': nb_pred,
            'confidence': float(np.max(nb_proba)),
            'probabilities': dict(zip(self.categories, [float(p) for p in nb_proba]))
        }
        
        # SVM
        text_svm = self.vectorizers['svm'].transform([text_processed])
        svm_decision = self.models['svm'].decision_function(text_svm)[0]
        if len(self.categories) == 2:
            svm_proba = [1 / (1 + np.exp(-svm_decision)), 1 / (1 + np.exp(svm_decision))]
        else:
            exp_scores = np.exp(svm_decision - np.max(svm_decision))
            svm_proba = exp_scores / np.sum(exp_scores)
        svm_pred = self.categories[np.argmax(svm_proba)]
        model_predictions['svm'] = {
            'prediction': svm_pred,
            'confidence': float(np.max(svm_proba)),
            'probabilities': dict(zip(self.categories, [float(p) for p in svm_proba]))
        }
        
        # Keyword model
        keyword_proba = self.models['keyword'].predict_proba([text_processed])[0]
        keyword_pred = self.categories[np.argmax(keyword_proba)]
        model_predictions['keyword'] = {
            'prediction': keyword_pred,
            'confidence': float(np.max(keyword_proba)),
            'probabilities': dict(zip(self.categories, [float(p) for p in keyword_proba]))
        }
        
        # Ensemble prediction
        final_scores = defaultdict(float)
        for model_name, weight in self.model_weights.items():
            if model_name in model_predictions:
                for category, prob in model_predictions[model_name]['probabilities'].items():
                    final_scores[category] += weight * prob
        
        ensemble_pred = max(final_scores, key=final_scores.get)
        ensemble_confidence = final_scores[ensemble_pred]
        
        return {
            'ensemble_prediction': ensemble_pred,
            'ensemble_confidence': float(ensemble_confidence),
            'ensemble_probabilities': dict(final_scores),
            'individual_models': model_predictions
        }
    
    def save_models(self):
        """Save all trained models."""
        if not self.is_trained:
            raise ValueError("Models must be trained before saving")
        
        os.makedirs(Config.MODEL_DIR, exist_ok=True)
        
        # Save individual models
        joblib.dump(self.models['naive_bayes'], Config.NAIVE_BAYES_MODEL_PATH)
        joblib.dump(self.models['svm'], Config.SVM_MODEL_PATH)
        joblib.dump(self.models['keyword'], Config.KEYWORD_MODEL_PATH)
        
        # Save vectorizers
        joblib.dump(self.vectorizers, Config.VECTORIZER_PATH)
        
        # Save metadata
        metadata = {
            'categories': self.categories,
            'model_weights': self.model_weights,
            'is_trained': self.is_trained
        }
        joblib.dump(metadata, os.path.join(Config.MODEL_DIR, 'metadata.pkl'))
        
        logging.info("All models saved successfully")
    
    def load_models(self):
        """Load all trained models."""
        try:
            # Load individual models
            self.models['naive_bayes'] = joblib.load(Config.NAIVE_BAYES_MODEL_PATH)
            self.models['svm'] = joblib.load(Config.SVM_MODEL_PATH)
            self.models['keyword'] = joblib.load(Config.KEYWORD_MODEL_PATH)
            
            # Load vectorizers
            self.vectorizers = joblib.load(Config.VECTORIZER_PATH)
            
            # Load metadata
            metadata = joblib.load(os.path.join(Config.MODEL_DIR, 'metadata.pkl'))
            self.categories = metadata['categories']
            self.model_weights = metadata['model_weights']
            self.is_trained = metadata['is_trained']
            
            logging.info("All models loaded successfully")
            return True
            
        except Exception as e:
            logging.error(f"Error loading models: {str(e)}")
            return False