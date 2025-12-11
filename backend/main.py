from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from rank_bm25 import BM25Okapi
import string
import os
import uvicorn

# --- CONFIGURAZIONE APP ---
app = FastAPI(title="Motore di Ricerca Ricette Italiane")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CSV_PATH = "backend/recipes.csv"

# --- 1. GESTIONE DATI ---

def get_dummy_data():
    """Fallback in caso di errore"""
    print("⚠️  ATTENZIONE: Uso dati di prova (DUMMY DATA).")
    data = {
        "title_page": ["Pasta alla Carbonara (DUMMY)", "Tiramisù (DUMMY)"],
        "ingredients": ["guanciale uova pecorino", "mascarpone savoiardi caffè"],
        "URL": ["#", "#"]
    }
    return pd.DataFrame(data)

def load_data():
    """Carica il CSV e rinomina le colonne italiane in standard interni"""
    try:
        if not os.path.exists(CSV_PATH):
            print(f"❌ File '{CSV_PATH}' non trovato.")
            return get_dummy_data()

        df = pd.read_csv(CSV_PATH)
        
        # Pulizia spazi
        df.columns = [c.strip() for c in df.columns]
        print(f"✅ Colonne originali: {df.columns.tolist()}")

        # --- MAPPATURA AGGIORNATA (FIX PER IL TUO CSV) ---
        column_mapping = {
            # Varianti Italiane (Trovate nel tuo log)
            'Nome': 'title_page',
            'Ingredienti': 'ingredients',
            'Link': 'URL',
            
            # Varianti Inglesi (Fallback)
            'Title': 'title_page',
            'title': 'title_page',
            'Name': 'title_page',
            'Recipe Name': 'title_page',
            'Ingredients': 'ingredients',
            'ingredients': 'ingredients',
            'url': 'URL',
            'link': 'URL'
        }
        
        # Rinomina
        df.rename(columns=column_mapping, inplace=True)

        # Controllo
        required_cols = ['title_page', 'ingredients']
        missing = [c for c in required_cols if c not in df.columns]
        
        if missing:
            print(f"❌ Errore: Mancano ancora le colonne {missing}. Colonne attuali: {df.columns.tolist()}")
            return get_dummy_data()

        df = df.fillna("")
        
        # Se manca URL dopo il rename, metti placeholder
        if 'URL' not in df.columns:
            df['URL'] = '#'

        print(f"✅ Dataset caricato correttamente: {len(df)} ricette.")
        return df

    except Exception as e:
        print(f"❌ Errore critico nel caricamento: {e}")
        return get_dummy_data()

df = load_data()

# --- 2. NLP & PREPROCESSING ---

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

# --- 3. INDICIZZAZIONE BM25 ---
print("⏳ Indicizzazione in corso...")
try:
    corpus_text = (df["title_page"] + " " + df["ingredients"]).apply(clean_text).tolist()
    tokenized_corpus = [get_ngrams(doc, n=2) for doc in corpus_text]
    bm25 = BM25Okapi(tokenized_corpus)
    print("✅ Indicizzazione completata.")
except Exception as e:
    print(f"❌ Errore indicizzazione: {e}")

# --- 4. ENDPOINTS ---

@app.get("/")
def read_root():
    return {"status": "ok"}

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
    uvicorn.run(app, host="0.0.0.0", port=8000)