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

    df['label'] = df['Dòng SP'] + " | " + df['Loại'] + " | " + df['Lớp 1'] + " | " + df['Lớp 2']
    
    ensemble_models = {}
    
    hs_groups = df.groupby('hs_code')
    print(f"Training ensemble of {len(hs_groups)} models...")
    start_time = time.time()
    
    for hs, sub_df in hs_groups:
        X = sub_df['clean_text']
        y = sub_df['label']
        
        if len(y.unique()) <= 1:
            ensemble_models[str(hs)] = {'type': 'single', 'label': y.iloc[0]}
            continue
            
        pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(analyzer='word', ngram_range=(1, 3), min_df=1)),
            ('clf', SGDClassifier(loss='log_loss', n_jobs=-1, max_iter=50, random_state=42))
        ])
        
        pipeline.fit(X, y)
        ensemble_models[str(hs)] = {'type': 'model', 'model': pipeline}
        
    end_time = time.time()
    print(f"Ensemble models trained in {end_time - start_time:.2f} seconds.")

    os.makedirs(os.path.dirname(MODEL_OUTPUT_PATH), exist_ok=True)
    with open(MODEL_OUTPUT_PATH, 'wb') as f:
        pickle.dump(ensemble_models, f)
        
    print(f"Ensemble successfully saved to {MODEL_OUTPUT_PATH}")

if __name__ == '__main__':
    train_model()
