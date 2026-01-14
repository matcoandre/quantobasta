# 🍳 QuantoBasta - Motore di Ricerca Ricette

**QuantoBasta** è un motore di ricerca verticale (Vertical Search Engine) progettato per trovare ricette italiane in base agli ingredienti a disposizione.
Il progetto è stato sviluppato come elaborato finale per il corso di **Laboratorio di interfacce linguistiche**.

---

## 🚀 Caratteristiche Principali

*   **Ricerca Semantica (BM25 + N-Grams):** Non si limita a cercare la corrispondenza esatta delle parole, ma calcola la rilevanza dei documenti utilizzando un indice invertito basato su unigrammi e bigrammi.
*   **Gestione Ingredienti (Chips):** Sistema di input intuitivo che trasforma gli ingredienti inseriti in "tag" (chips), permettendo di raffinare la ricerca facilmente.
*   **Interfaccia Reattiva (SPA):** Sviluppata in Vue.js, offre un'esperienza fluida senza ricaricamenti di pagina.
*   **Visualizzazione Overlay:** I dettagli della ricetta si aprono in un modale sopra i risultati, mantenendo il contesto della ricerca attivo sullo sfondo.

---

## 🛠️ Linguaggi e librerie 

### Backend (Python)
*   **FastAPI:** Framework moderno e veloce per esporre le API REST.
*   **Pandas:** Utilizzato per il caricamento e la gestione tabulare del dataset CSV.
*   **Rank_BM25:** Libreria per l'implementazione dell'algoritmo di ranking BM25.

### Frontend (Vue.js)
*   **Vue 3 (Composition API):** Per la gestione dello stato e della logica reattiva.
*   **Vite:** Build tool per un ambiente di sviluppo rapido.

---

## 🧠 Logica e Algoritmi (Documentazione Tecnica)

### 1. Preprocessing e Pulizia Dati
Il dataset utilizzato presenta alcune complessità strutturali, come liste salvate sotto forma di stringhe. Per aderire alle specifiche del corso che richiedevano la comprensione profonda del codice, sono stati implementati parser manuali:

*   **Parsing Ingredienti:** La funzione `pulisci_lista_ingredienti` analizza la stringa grezza, rimuove manualmente parentesi e virgolette utilizzando metodi base delle stringhe (`replace`, `split`) e ricostruisce la lista corretta.
*   **Parsing Procedimento:** La funzione `pulisci_procedimento` analizza la struttura del testo. Riconosce se il formato è una lista Python-like o testo libero e lo segmenta correttamente in passaggi leggibili utilizzando separatori logici, senza l'uso di espressioni regolari.

### 2. Tokenizzazione a N-Grammi
Per migliorare la precisione della ricerca, il testo non viene indicizzato solo come parole singole. La funzione `get_ngrams`:
1.  Genera **Unigrammi** (parole singole): es. "torta", "di", "mele".
2.  Genera **Bigrammi** (coppie): es. "torta di", "di mele".

Questo permette al motore di distinguere concetti composti e specifici (es. "Olio Extravergine" ha un peso semantico diverso e più specifico rispetto a "Olio" e "Extravergine" presi singolarmente).

### 3. Ranking con BM25
Al posto di una ricerca booleana semplice (Presente/Assente), viene utilizzato l'algoritmo BM25. Questo assegna un punteggio di rilevanza (`score`) ad ogni ricetta basandosi su:
*   **TF (Term Frequency):** Quanto spesso i termini cercati appaiono nella ricetta.
*   **IDF (Inverse Document Frequency):** Quanto sono rari i termini nell'intero corpus (premia parole specifiche come "guanciale" rispetto a parole comuni come "sale").
*   **Lunghezza del documento:** Normalizza il punteggio per evitare che ricette lunghissime appaiano sempre per prime solo perché contengono più parole.

---

## 📦 Installazione e Avvio

### Prerequisiti
*   Node.js & npm
*   Python 3.x & pip

### Single command
Aprire un terminale nella cartella del progetto:
```bash
npm run dev
```
Il sito sarà accessibile all'indirizzo mostrato nel terminale (solitamente http://localhost:5173).

---

## 📊 Dataset
Il dataset utilizzato è Italian Food Recipes disponibile su Kaggle.
*   Fonte: Kaggle - Italian Food Recipes
*   Contenuto: ~4000 ricette con titolo, ingredienti, procedimento e link originale.