from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from rank_bm25 import BM25Okapi
import string
import os
import uvicorn

app = FastAPI(title="QuantoBasta API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CSV_PATH = "backend/recipes.csv"

def pulisci_lista_ingredienti(testo):
    s = str(testo)
    s = s.replace("[", "").replace("]", "").replace("'", "").replace('"', "")
    elementi = s.split(",")
    lista_finale = []
    for x in elementi:
        parola = x.strip()
        if parola:
            lista_finale.append(parola)
    return lista_finale

def pulisci_procedimento(testo):
    s = str(testo).strip()
    passaggi_grezzi = []

    if s.startswith("[") and s.endswith("]"):
        contenuto = s[1:-1]
        if "', '" in contenuto:
            passaggi_grezzi = contenuto.split("', '")
        elif '", "' in contenuto:
            passaggi_grezzi = contenuto.split('", "')
        else:
            passaggi_grezzi = [contenuto]
    else:
        s = s.replace(". ", "|")
        passaggi_grezzi = s.split("|")

    passaggi_puliti = []
    for p in passaggi_grezzi:
        p = p.replace("'", "").replace('"', "").strip()
        if len(p) > 5:
            p = p[0].upper() + p[1:]
            if p[-1] not in [".", "!", "?", ":"]:
                p += "."
            passaggi_puliti.append(p)

    if not passaggi_puliti:
        return [s.replace("[", "").replace("]", "").replace("'", "")]

    return passaggi_puliti

def preprocessing_bm25(testo):
    testo = str(testo).lower()
    for char in string.punctuation:
        testo = testo.replace(char, " ")
    return testo

def get_ngrams(testo, n=2):
    parole = testo.split()
    tokens = list(parole)
    if len(parole) >= n:
        for i in range(len(parole) - 1):
            tokens.append(parole[i] + " " + parole[i+1])
    return tokens

def carica_dati():
    if not os.path.exists(CSV_PATH):
        return pd.DataFrame()

    try:
        df = pd.read_csv(CSV_PATH)
        df.columns = [c.strip() for c in df.columns]
        
        nomi_interni = {}
        for col in df.columns:
            nome_low = col.lower()
            if "unnamed" in nome_low: continue
            
            if "nome" in nome_low or "title" in nome_low or "name" in nome_low:
                nomi_interni[col] = "title_page"
            elif "ingred" in nome_low:
                nomi_interni[col] = "ingredients_raw"
            elif "step" in nome_low or "proc" in nome_low:
                nomi_interni[col] = "steps_raw"
            elif "link" in nome_low or "url" in nome_low:
                nomi_interni[col] = "URL"

        df.rename(columns=nomi_interni, inplace=True)
        
        if "title_page" not in df.columns:
            return pd.DataFrame()

        df = df.fillna("")
        
        df["clean_ingredients"] = df["ingredients_raw"].apply(pulisci_lista_ingredienti)
        
        if "steps_raw" in df.columns:
            df["steps"] = df["steps_raw"].apply(pulisci_procedimento)
        else:
            df["steps"] = df["title_page"].apply(lambda x: ["Nessun procedimento."])

        if "URL" not in df.columns: df["URL"] = "#"

        df["search_text"] = df["title_page"] + " " + \
                            df["clean_ingredients"].apply(lambda x: " ".join(x))
        
        return df

    except Exception:
        return pd.DataFrame()

df = carica_dati()

if not df.empty:
    corpus = df["search_text"].apply(preprocessing_bm25).tolist()
    tokenized_corpus = [get_ngrams(doc) for doc in corpus]
    bm25 = BM25Okapi(tokenized_corpus)
else:
    bm25 = None

@app.get("/")
def home(): return {"status": "ok"}

@app.get("/search")
def search(q: str, limit: int = 12):
    if df.empty or not q: return {"results": []}
    
    q_clean = preprocessing_bm25(q)
    q_tokens = get_ngrams(q_clean)
    
    scores = bm25.get_scores(q_tokens)
    top_n = bm25.get_top_n(q_tokens, list(range(len(df))), n=limit)
    
    results = []
    for i in top_n:
        if scores[i] > 0:
            row = df.iloc[i]
            res = {
                "title_page": str(row["title_page"]),
                "clean_ingredients": row["clean_ingredients"],
                "steps": row["steps"],
                "URL": str(row["URL"]),
                "score": float(scores[i])
            }
            results.append(res)
            
    return {"results": results}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)