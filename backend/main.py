from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from rank_bm25 import BM25Okapi
import string
import os
import uvicorn
import ast
import re

app = FastAPI(title="Motore Ricette")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CSV_PATH = "backend/recipes.csv"

# --- 1. PREPROCESSING CORRETTO ---

def clean_text(text):
    """
    Pulisce il testo per l'indicizzazione.
    FIX IMPORTANTE: Sostituisce la punteggiatura con SPAZI.
    Prima: "all'amatriciana" -> "allamatriciana" (Errore)
    Ora: "all'amatriciana" -> "all amatriciana" (Corretto)
    """
    text = str(text).lower()
    
    # Crea una tabella di traduzione: ogni segno di punteggiatura diventa uno spazio
    # Questo preserva le parole composte con apostrofi o trattini
    translator = str.maketrans(string.punctuation, ' ' * len(string.punctuation))
    text = text.translate(translator)
    
    # Rimuove doppi spazi generati dalla sostituzione
    return " ".join(text.split())

def get_ngrams(text, n=2):
    words = text.split()
    tokens = words.copy() # Unigrammi (parole singole)
    
    # Bigrammi (coppie di parole)
    if len(words) >= n:
        n_grams_tuples = zip(*[words[i:] for i in range(n)])
        tokens.extend([" ".join(ngram) for ngram in n_grams_tuples])
    return tokens

# --- 2. LOGICA DI PULIZIA VISIVA (STOP WORDS & STEPS) ---

def split_text_smart(text):
    text = str(text).strip()
    if not text: return []
    text = text.replace("['", "").replace("']", "").replace('["', '').replace('"]', '')
    text = text.replace(". ", ". |SPLIT|")
    text = re.sub(r'(?<=[a-zà-ù])\s+(?=[A-Z])', ' |SPLIT|', text)
    raw_parts = text.split('|SPLIT|')

    bad_endings = {
        'il', 'lo', 'la', 'i', 'gli', 'le', 'un', 'uno', 'una', 
        'del', 'dello', 'della', 'dei', 'degli', 'delle', 
        'al', 'allo', 'alla', 'ai', 'agli', 'alle', 
        'nel', 'nello', 'nella', 'nei', 'negli', 'nelle', 
        'sul', 'sullo', 'sulla', 'sui', 'sugli', 'sulle',
        'col', 'coi', 'dal', 'dallo', 'dalla', 'dai', 'dagli', 'dalle',
        'di', 'a', 'da', 'in', 'con', 'su', 'per', 'tra', 'fra', 
        'e', 'ed', 'o'
    }

    final_steps = []
    buffer = ""

    for part in raw_parts:
        part = part.strip()
        if not part: continue
        if buffer:
            part = buffer + " " + part
            buffer = ""
        
        words = part.split()
        if not words: continue
        last_word = words[-1].lower().translate(str.maketrans('', '', string.punctuation))

        if last_word in bad_endings:
            buffer = part
        else:
            if part[-1] not in ['.', '!', '?', ':']: part += "."
            final_steps.append(part)

    if buffer:
        if buffer[-1] not in ['.', '!', '?', ':']: buffer += "."
        final_steps.append(buffer)
            
    return final_steps

def parse_ingredients_smart(val):
    if pd.isna(val) or val == "": return []
    try:
        parsed = ast.literal_eval(str(val))
        if isinstance(parsed, list):
            clean = []
            for item in parsed:
                if isinstance(item, list) and len(item) >= 1:
                    clean.append(" ".join([str(x) for x in item[::-1]]))
                elif isinstance(item, str):
                    clean.append(item)
            return clean
        return [str(val)]
    except:
        return [str(val).replace("[", "").replace("]", "").replace("'", "")]

def parse_steps_smart(val):
    if pd.isna(val) or val == "": return ["Procedimento non disponibile."]
    try:
        parsed = ast.literal_eval(str(val))
        if isinstance(parsed, list) and len(parsed) > 1:
            return [str(p).strip() for p in parsed]
        content = parsed[0] if isinstance(parsed, list) and len(parsed) > 0 else str(val)
        return split_text_smart(content)
    except:
        return split_text_smart(str(val))

# --- 3. CARICAMENTO ---

def load_data():
    if not os.path.exists(CSV_PATH): return pd.DataFrame()
    try:
        df = pd.read_csv(CSV_PATH)
        df.columns = [c.strip() for c in df.columns]
        
        rename_map = {}
        cols_lower = {c.lower(): c for c in df.columns}
        
        if 'nome' in cols_lower: rename_map[cols_lower['nome']] = 'title_page'
        elif 'title' in cols_lower: rename_map[cols_lower['title']] = 'title_page'
        elif 'name' in cols_lower: rename_map[cols_lower['name']] = 'title_page'

        if 'ingredienti' in cols_lower: rename_map[cols_lower['ingredienti']] = 'ingredients_raw'
        elif 'ingredients' in cols_lower: rename_map[cols_lower['ingredients']] = 'ingredients_raw'

        if 'steps' in cols_lower: rename_map[cols_lower['steps']] = 'steps_raw'
        elif 'procedimento' in cols_lower: rename_map[cols_lower['procedimento']] = 'steps_raw'

        if 'link' in cols_lower: rename_map[cols_lower['link']] = 'URL'
        elif 'url' in cols_lower: rename_map[cols_lower['url']] = 'URL'

        df.rename(columns=rename_map, inplace=True)
        if 'title_page' not in df.columns: return pd.DataFrame()

        df = df.fillna("")
        df['title_page'] = df['title_page'].astype(str)
        
        df['clean_ingredients'] = df['ingredients_raw'].apply(parse_ingredients_smart)
        if 'steps_raw' in df.columns:
            df['clean_steps'] = df['steps_raw'].apply(parse_steps_smart)
        else:
            df['clean_steps'] = [["Nessun procedimento."]] * len(df)

        if 'URL' not in df.columns: df['URL'] = "#"

        # Search Text: Qui usiamo la nuova clean_text implicitamente dopo
        df['search_text'] = df['title_page'] + " " + \
                            df['clean_ingredients'].apply(lambda x: " ".join(x))
        
        print(f"✅ Dataset caricato: {len(df)} ricette.")
        return df

    except Exception as e:
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

df = load_data()

# --- 4. MOTORE BM25 ---

if not df.empty and 'search_text' in df.columns:
    # Applica la NUOVA clean_text
    corpus = df['search_text'].apply(clean_text).tolist()
    tokenized_corpus = [get_ngrams(doc) for doc in corpus]
    bm25 = BM25Okapi(tokenized_corpus)
else:
    bm25 = None

@app.get("/search")
def search(q: str, limit: int = 12):
    if df.empty or bm25 is None or not q: 
        return {"results": [], "query_tokens": []}
    
    # Applica la NUOVA clean_text anche alla query
    cleaned_query = clean_text(q)
    tokens = get_ngrams(cleaned_query)
    
    scores = bm25.get_scores(tokens)
    top_n = bm25.get_top_n(tokens, list(range(len(df))), n=limit)
    
    results = []
    for idx in top_n:
        if scores[idx] > 0:
            row = df.iloc[idx]
            results.append({
                "title_page": str(row['title_page']),
                "clean_ingredients": row['clean_ingredients'],
                "steps": row['clean_steps'],
                "URL": str(row['URL']),
                "score": float(scores[idx])
            })
            
    return {"results": results, "query_tokens": tokens}

@app.get("/")
def root(): return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)