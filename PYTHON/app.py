from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
import os
import joblib
import sys
import logging
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def create_app():
    """Application factory pattern."""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Load model and vectorizer
    try:
        app.model = joblib.load(Config.MODEL_PATH)
        app.vectorizer = joblib.load(Config.VECTORIZER_PATH)
        logging.info("Model and vectorizer loaded successfully")
    except Exception as e:
        logging.error(f"Error loading model: {str(e)}")
        app.model = None
        app.vectorizer = None
    
    return app

app = create_app()

@app.route("/")
def home():
    """Home page route."""
    return render_template("index.html")

@app.route("/predict", methods=["POST"])
def predict():
    """Prediction route."""
    try:
        if not app.model or not app.vectorizer:
            flash("Model not loaded. Please train the model first.", "error")
            return redirect(url_for('home'))
        
        description = request.form.get("description", "").strip()
        
        if not description:
            flash("Please enter a description.", "error")
            return redirect(url_for('home'))
        
        # Preprocess the input
        description_processed = description.lower()
        
        # Transform and predict
        description_transformed = app.vectorizer.transform([description_processed])
        prediction = app.model.predict(description_transformed)[0]
        confidence = app.model.predict_proba(description_transformed)[0].max()
        
        # Log the prediction
        logging.info(f"Prediction made: '{description}' -> {prediction} (confidence: {confidence:.2f})")
        
        return render_template("result.html", 
                             description=description,
                             prediction=prediction,
                             confidence=confidence)
        
    except Exception as e:
        logging.error(f"Error in prediction: {str(e)}")
        flash("An error occurred during prediction. Please try again.", "error")
        return redirect(url_for('home'))

@app.route("/api/predict", methods=["POST"])
def api_predict():
    """API endpoint for prediction."""
    try:
        if not app.model or not app.vectorizer:
            return jsonify({"error": "Model not loaded"}), 500
        
        data = request.get_json()
        if not data or 'description' not in data:
            return jsonify({"error": "Missing description"}), 400
        
        description = data['description'].strip()
        if not description:
            return jsonify({"error": "Empty description"}), 400
        
        # Preprocess and predict
        description_processed = description.lower()
        description_transformed = app.vectorizer.transform([description_processed])
        prediction = app.model.predict(description_transformed)[0]
        confidence = app.model.predict_proba(description_transformed)[0].max()
        
        return jsonify({
            "prediction": prediction,
            "confidence": float(confidence),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logging.error(f"Error in API prediction: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/health")
def health_check():
    """Health check endpoint."""
    status = {
        "status": "healthy",
        "model_loaded": app.model is not None,
        "vectorizer_loaded": app.vectorizer is not None,
        "timestamp": datetime.now().isoformat()
    }
    return jsonify(status)

@app.errorhandler(404)
def not_found(error):
    """404 error handler."""
    return render_template("error.html", error="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    """500 error handler."""
    logging.error(f"Internal server error: {str(error)}")
    return render_template("error.html", error="Internal server error"), 500

if __name__ == "__main__":
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=5000)
