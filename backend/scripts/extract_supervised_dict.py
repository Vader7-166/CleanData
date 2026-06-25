import pandas as pd
import sqlite3
import os
import sys
from sklearn.feature_extraction.text import TfidfVectorizer
import csv

sys.stdout.reconfigure(encoding='utf-8')

script_dir = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(script_dir, "../storage/ground_truth.db")
OUTPUT_DICT_PATH = os.path.join(script_dir, "../storage/dict_golden.csv")

def extract_dictionary():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}. Run seed_ground_truth.py first.")
        return

    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT hs_code, clean_text, `Dòng SP`, `Loại`, `Lớp 1`, `Lớp 2` FROM ground_truth", conn)
    conn.close()

    if df.empty:
        print("Database is empty.")
        return

    print(f"Loaded {len(df)} rows from Ground Truth Database.")

    hs_codes = df['hs_code'].unique()
    dictionary_entries = []
    
    for hs in hs_codes:
        df_hs = df[df['hs_code'] == hs].copy()
        
        # Combine labels for grouping
        df_hs['full_label'] = df_hs['Dòng SP'] + " | " + df_hs['Loại'] + " | " + df_hs['Lớp 1'] + " | " + df_hs['Lớp 2']
        
        grouped = df_hs.groupby('full_label')['clean_text'].apply(lambda x: ' '.join(x)).reset_index()
        
        if len(grouped) < 2:
            text = grouped['clean_text'].iloc[0]
            from collections import Counter
            words = text.split()
            bigrams = [' '.join(b) for b in zip(words[:-1], words[1:])]
            most_common = [k for k, v in Counter(words + bigrams).most_common(15)]
            dictionary_entries.append({
                'Mã HS': hs,
                'Label': grouped['full_label'].iloc[0],
                'Keywords': ', '.join(most_common)
            })
            continue

        vectorizer = TfidfVectorizer(
            ngram_range=(1, 3),
            max_df=0.9,
            min_df=1,
            token_pattern=r'(?u)\b\w+\b'
        )
        
        try:
            tfidf_matrix = vectorizer.fit_transform(grouped['clean_text'])
            feature_names = vectorizer.get_feature_names_out()
            
            for i, row in grouped.iterrows():
                row_vector = tfidf_matrix[i].toarray()[0]
                top_indices = row_vector.argsort()[-20:][::-1] # Top 20 keywords
                
                keywords = []
                for idx in top_indices:
                    if row_vector[idx] > 0.03: 
                        keywords.append(feature_names[idx])
                
                dictionary_entries.append({
                    'Mã HS': hs,
                    'Label': row['full_label'],
                    'Keywords': ', '.join(keywords)
                })
        except Exception as e:
            print(f"Error processing HS {hs}: {e}")

    os.makedirs(os.path.dirname(OUTPUT_DICT_PATH), exist_ok=True)
    
    with open(OUTPUT_DICT_PATH, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Keyword', 'Dòng SP', 'Loại', 'Lớp 1', 'Lớp 2', 'Mã HS'])
        
        for entry in dictionary_entries:
            parts = [p.strip() for p in entry['Label'].split(' | ')]
            if len(parts) == 4:
                writer.writerow([
                    entry['Keywords'],
                    parts[0], parts[1], parts[2], parts[3],
                    entry['Mã HS']
                ])
                
    print(f"Successfully generated golden dictionary at {OUTPUT_DICT_PATH}")

if __name__ == "__main__":
    extract_dictionary()
