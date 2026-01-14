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
    """
    Trasforma la stringa "['Uova', '4', 'Farina', '100g']" 
    in una lista accoppiata ["4 Uova", "100g Farina"].
    """
    s = str(testo)
    # Rimuoviamo parentesi e virgolette
    s = s.replace("[", "").replace("]", "").replace("'", "").replace('"', "")
    
    # Dividiamo per virgola
    elementi = s.split(",")
    
    # Creiamo una lista temporanea pulita dagli spazi
    elementi_puliti = []
    for x in elementi:
        p = x.strip()
        if p:
            elementi_puliti.append(p)
            
    lista_finale = []
    
    # Scorriamo la lista a passi di 2 (coppie)
    # Assumiamo che la struttura sia sempre [Nome, Quantità, Nome, Quantità...]
    i = 0
    while i < len(elementi_puliti):
        nome = elementi_puliti[i]
        
        # Controlliamo se esiste un elemento successivo (la quantità)
        if i + 1 < len(elementi_puliti):
            quantita = elementi_puliti[i+1]
            
            # Uniamo invertendo: "4" + " " + "Uova"
            ingrediente_completo = quantita + " " + nome
            lista_finale.append(ingrediente_completo)
            
            # Avanziamo di 2 perché abbiamo usato due elementi
            i += 2 
        else:
            # Se rimane un elemento spaiato alla fine, lo aggiungiamo così com'è
            lista_finale.append(nome)
            i += 1
            
    return lista_finale

def pulisci_procedimento(testo):
    """
    Divide il procedimento in passaggi analizzando la punteggiatura e le maiuscole.
    Risolve il problema del testo attaccato (es. "uova Quindi").
    """
    s = str(testo).strip()
    
    # 1. Se il testo è già una lista Python pulita (es. inizia con [ e finisce con ])
    if s.startswith("[") and s.endswith("]"):
        contenuto = s[1:-1] # Togliamo le parentesi
        if "', '" in contenuto:
            return contenuto.split("', '")
        elif '", "' in contenuto:
            return contenuto.split('", "')
    
    # 2. Se è un "muro di testo", lo analizziamo carattere per carattere
    # Puliamo artefatti comuni
    s = s.replace("['", "").replace("']", "").replace('["', '').replace('"]', '')
    s = s.replace("\\n", " ") # Togliamo gli "a capo" informatici

    testo_con_separatori = ""
    lunghezza = len(s)

    # Scorriamo il testo fino al penultimo carattere
    for i in range(lunghezza):
        char = s[i]
        testo_con_separatori += char
        
        # Logica per capire se dobbiamo spezzare QUI
        # Guardiamo avanti di 1 o 2 caratteri se possibile
        if i < lunghezza - 2:
            curr = s[i]      # Carattere corrente
            succ = s[i+1]    # Carattere successivo
            succ2 = s[i+2]   # Carattere dopo il successivo

            # CASO A: Punto attaccato alla Maiuscola (es. "ambiente.Una")
            if curr == "." and succ.isupper():
                testo_con_separatori += "|"
            
            # CASO B: Fine frase senza punto (es. "uovo Quindi" o "integre) Considerate")
            # Logica: Se (lettera minuscola O parentesi chiusa) + Spazio + Maiuscola
            # Escludiamo parole come "gr. 100" o sigle controllando che succ2 sia Maiuscola
            elif (curr.islower() or curr == ")") and succ == " " and succ2.isupper():
                testo_con_separatori += "|"

    # 3. Dividiamo usando il separatore che abbiamo inserito
    passaggi_grezzi = testo_con_separatori.split("|")
    
    passaggi_puliti = []
    for p in passaggi_grezzi:
        p = p.strip()
        # Pulizia finale
        p = p.replace("'", "").replace('"', "")
        
        # Filtriamo frammenti troppo corti
        if len(p) > 5:
            # Assicuriamo che inizi con maiuscola
            p = p[0].upper() + p[1:]
            # Assicuriamo che finisca con un punto
            if p[-1] not in [".", "!", "?", ":"]:
                p += "."
            passaggi_puliti.append(p)

    # Se non siamo riusciti a dividere nulla, ritorniamo il testo intero pulito
    if not passaggi_puliti:
        return [s]

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
    if df.empty or bm25 is None or not q: 
        return {"results": []}
    
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