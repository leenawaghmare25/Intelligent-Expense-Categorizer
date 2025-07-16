import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib
import os

# Load data
df = pd.read_csv("../data/synthetic_expenses.csv")  # adjust path because your main.py is inside PYTHON/

# Preprocess
df['Description'] = df['Description'].str.lower()

# Features and labels
X = df['Description']
y = df['Category']

# Vectorize
vectorizer = TfidfVectorizer()
X_vec = vectorizer.fit_transform(X)

model = LogisticRegression()
model.fit(X_vec, y)
print("Model trained on full data.")

# Save model and vectorizer
os.makedirs("../model", exist_ok=True)  # make sure model/ exists
joblib.dump(model, "../model/expense_model.pkl")
joblib.dump(vectorizer, "../model/vectorizer.pkl")
