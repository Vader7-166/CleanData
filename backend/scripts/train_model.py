import pandas as pd
import sqlite3
import os
import sys
import pickle
import time
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

sys.stdout.reconfigure(encoding='utf-8')

script_dir = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(script_dir, "../storage/ground_truth.db")
MODEL_OUTPUT_PATH = os.path.join(script_dir, "../storage/classifier_model.pkl")

def train_model():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}. Run seed_ground_truth.py first.")
        return

    print("Loading data from database...")
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT hs_code, clean_text, `Dòng SP`, `Loại`, `Lớp 1`, `Lớp 2` FROM ground_truth", conn)
    conn.close()

    if df.empty:
        print("Database is empty.")
        return

    print(f"Loaded {len(df)} rows.")

    df['label'] = df['Dòng SP'] + " | " + df['Loại'] + " | " + df['Lớp 1'] + " | " + df['Lớp 2']
    df['features'] = "hs" + df['hs_code'] + " " + df['clean_text']

    X = df['features']
    y = df['label']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, random_state=42)

    print("Initializing pipeline (Char-level TF-IDF + SGD Classifier)...")
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(analyzer='char_wb', ngram_range=(3, 6), min_df=2, max_df=0.9)),
        ('clf', SGDClassifier(loss='log_loss', n_jobs=-1, max_iter=50, random_state=42))
    ])

    print("Training model... (This should take 10-30 seconds)")
    start_time = time.time()
    pipeline.fit(X_train, y_train)
    end_time = time.time()
    
    print(f"Model trained in {end_time - start_time:.2f} seconds.")

    print("Evaluating model...")
    y_pred = pipeline.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"Accuracy on test set: {acc * 100:.2f}%")
    
    os.makedirs(os.path.dirname(MODEL_OUTPUT_PATH), exist_ok=True)
    with open(MODEL_OUTPUT_PATH, 'wb') as f:
        pickle.dump(pipeline, f)
        
    print(f"Model successfully saved to {MODEL_OUTPUT_PATH}")

if __name__ == "__main__":
    train_model()
