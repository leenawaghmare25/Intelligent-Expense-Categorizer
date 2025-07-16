from flask import Flask, render_template, request
import joblib

app = Flask(__name__)  # ✅ corrected here

# Load the trained model and vectorizer
model = joblib.load("model/expense_model.pkl")
vectorizer = joblib.load("model/vectorizer.pkl")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/predict", methods=["POST"])
def predict():
    description = request.form["description"]
    description_transformed = vectorizer.transform([description])
    prediction = model.predict(description_transformed)[0]
    return f"""
    <h2>Predicted Category: {prediction}</h2>
    <br><a href='/'>Try Another</a>
    """

if __name__ == "__main__":  # ✅ corrected here
    app.run(debug=True)
