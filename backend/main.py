from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from rank_bm25 import BM25Okapi
import string
import os

app = FastAPI()

# Configurazione CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- GESTIONE DATASET (Versione StackBlitz Friendly) ---
CSV_PATH = "backend/recipes.csv"

def get_dummy_data():
    """Crea dati finti se il CSV non è stato caricato"""
    print("⚠️ CSV non trovato. Generazione dati di prova...")
    data = {
        "title_page": [
            "Pasta alla Carbonara", 
            "Tiramisù Classico", 
            "Pasta al Pomodoro e Basilico", 
            "Risotto ai Funghi", 
            "Pollo al Forno con Patate"
        ],
        "ingredients": [
            "guanciale uova pecorino pepe spaghetti",
            "mascarpone savoiardi caffè cacao uova zucchero",
            "pomodoro basilico olio aglio spaghetti",
            "riso funghi porcini brodo cipolla burro",
            "pollo patate rosmarino olio sale"
        ],
        "URL": ["#", "#", "#", "#", "#"]
    }
    return pd.DataFrame(data)

try:
    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH).fillna("")
        print(f"✅ Dataset caricato: {len(df)} ricette.")
    else:
        df = get_dummy_data()
except Exception as e:
    print(f"Errore: {e}")
    df = get_dummy_data()

# --- NLP & LOGICA (Identica a prima) ---
def clean_text(text):
    text = str(text).lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    return text

def get_ngrams(text, n=2):
    words = text.split()
    tokens = words.copy()
    if len(words) >= n:
        n_grams_tuples = zip(*[words[i:] for i in range(n)])
        n_grams = [" ".join(ngram) for ngram in n_grams_tuples]
        tokens.extend(n_grams)
    return tokens

# Inizializzazione Indice
corpus_text = (df["title_page"] + " " + df["ingredients"]).apply(clean_text).tolist()
tokenized_corpus = [get_ngrams(doc, n=2) for doc in corpus_text]
bm25 = BM25Okapi(tokenized_corpus)

@app.get("/")
def read_root():
    return {"status": "Backend Python attivo su StackBlitz"}

@app.get("/search")
def search_recipes(q: str, limit: int = 10):
    if not q: return {"results": [], "query_tokens": []}
    
    cleaned_query = clean_text(q)
    tokenized_query = get_ngrams(cleaned_query, n=2)
    
    doc_scores = bm25.get_scores(tokenized_query)
    top_n_indexes = bm25.get_top_n(tokenized_query, list(range(len(df))), n=limit)
    
    results = []
    for idx in top_n_indexes:
        if doc_scores[idx] > 0:
            recipe = df.iloc[idx].to_dict()
            recipe['score'] = doc_scores[idx]
            results.append(recipe)
    
    return {"results": results, "query_tokens": tokenized_query}

if __name__ == "__main__":
    import uvicorn
    # StackBlitz richiede 127.0.0.1
    uvicorn.run(app, host="127.0.0.1", port=8000)