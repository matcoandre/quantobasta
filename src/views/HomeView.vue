<script setup>
import { ref } from 'vue';
import axios from 'axios';

// --- STATO ---
const queryText = ref('');
const chips = ref([]);
const results = ref([]);
const loading = ref(false);
const selectedRecipe = ref(null); // Contiene la ricetta aperta nel modale

// --- GESTIONE CHIPS (TAG) ---
const handleInputKey = (e) => {
  if (e.key === 'Enter') {
    // Se premo Enter e c'è testo, aggiungo chip E cerco
    if (queryText.value.trim()) {
      addChip();
    }
    search(); 
  } else if (e.key === ',' || (e.key === ' ' && queryText.value.length > 2)) {
    // Virgola o Spazio creano un chip
    e.preventDefault();
    addChip();
    // Opzionale: se vuoi cercare mentre scrivi i chip, togli il commento sotto
    // search(); 
  }
};

const addChip = () => {
  const val = queryText.value.replace(',', '').trim();
  if (val) {
    chips.value.push(val);
    queryText.value = '';
  }
};

const removeChip = (index) => {
  chips.value.splice(index, 1);
  // FIX: Aggiorna la ricerca subito quando rimuovi un ingrediente
  search();
};

// --- MOTORE DI RICERCA ---
const search = async () => {
  // Unisce i chip e il testo corrente
  let fullQuery = [...chips.value, queryText.value].join(' ').trim();
  
  if (!fullQuery) {
    results.value = [];
    return;
  }
  
  loading.value = true;
  
  try {
    const res = await axios.get('/api/search', { params: { q: fullQuery, limit: 12 } });
    results.value = res.data.results;
  } catch (e) {
    console.error("Errore API:", e);
  } finally {
    loading.value = false;
  }
};

// --- GESTIONE MODALE (OVERLAY) ---
const openRecipe = (recipe) => {
  selectedRecipe.value = recipe;
  document.body.style.overflow = 'hidden'; // Blocca scroll sotto
};

const closeRecipe = () => {
  selectedRecipe.value = null;
  document.body.style.overflow = 'auto'; // Riattiva scroll
};
</script>

<template>
  <div class="home-container">
    
    <!-- 1. SEARCH AREA -->
    <header class="search-area">
      <div class="search-box">
        <!-- Input Riga -->
        <div class="search-input">
          <span class="icon">🔍</span>
          <input
            type="text"
            v-model="queryText"
            @keydown="handleInputKey"
            placeholder="Cerca uno o più ingredienti (es. Uova, Farina)..."
          />
        </div>

        <!-- Riga Sotto: Chips e Tasto Send -->
        <div class="search-bottom">
          <div class="chips">
            <span v-for="(chip, index) in chips" :key="index" class="chip">
              {{ chip }}
              <button @click="removeChip(index)">×</button>
            </span>
          </div>

          <span 
            class="send" 
            :class="{ disabled: !queryText && chips.length === 0 }"
            @click="search"
          >
            ▶
          </span>
        </div>
      </div>
    </header>

    <!-- 2. RISULTATI GRIGLIA -->
    <main class="results" v-if="results.length > 0 || loading">
      
      <!-- Loading State -->
      <div v-if="loading" class="loading-state">
        <p>Sto cercando nel ricettario...</p>
      </div>

      <!-- Grid -->
      <div class="grid" v-else>
        <article v-for="(recipe, index) in results" :key="index" class="card">
          
          <h3>{{ recipe.title_page }}</h3>
          
          <!-- FIX: Tempo in alto a destra -->
          <span class="time-badge">⏱ {{ 15 + (recipe.steps?.length || 5) * 5 }} min</span>

          <p class="ingredients">
            <strong>Ingredienti:</strong><br>
            <!-- Mostra solo i primi 4 ingredienti -->
            <span v-for="(ing, i) in (recipe.clean_ingredients || []).slice(0, 4)" :key="i">
              {{ ing }}<br>
            </span>
            <span v-if="(recipe.clean_ingredients?.length || 0) > 4" style="opacity:0.6">...e altri</span>
          </p>

          <button class="primary" @click="openRecipe(recipe)">
            Vedi preparazione →
          </button>
        </article>
      </div>
    </main>

    <!-- 3. MODALE DETTAGLIO (Overlay) -->
    <div v-if="selectedRecipe" class="recipe-modal" @click.self="closeRecipe">
      <div class="recipe-card-modal">
        
        <!-- Header Modale -->
        <div class="card-header">
          <a href="#" @click.prevent="closeRecipe" class="back-link">← Torna indietro</a>
          <span class="icon-header">🍴</span>
        </div>

        <!-- Contenuto Modale -->
        <div class="card-content">
          <div class="title-row">
            <h2>{{ selectedRecipe.title_page }}</h2>
            <div class="time-big">
              ⏱ {{ 15 + (selectedRecipe.steps?.length || 5) * 5 }} min
            </div>
          </div>

          <!-- Lista Ingredienti -->
          <div class="text-block">
            <strong>Ingredienti:</strong><br><br>
            <ul class="clean-list">
              <li v-for="(ing, i) in (selectedRecipe.clean_ingredients || [])" :key="i">
                {{ ing }}
              </li>
            </ul>
          </div>

          <!-- Lista Passaggi (Numerata) -->
          <div class="text-block">
            <strong>Preparazione:</strong><br><br>
            <ol class="step-list">
              <li v-for="(step, i) in (selectedRecipe.steps || [])" :key="i">
                {{ step }}
              </li>
            </ol>
          </div>
          
          <!-- Link Esterno -->
          <div class="link-row">
             <a :href="selectedRecipe.URL" target="_blank" class="primary-link">Vedi originale su GialloZafferano →</a>
          </div>
        </div>

      </div>
    </div>

  </div>
</template>

<style scoped>
/* =========================================
   IMPORTANTE: Tutto usa var(--...) per la Dark Mode
   ========================================= */

/* --- SEARCH AREA --- */
.search-area {
  padding-top: 75px;
  display: flex;
  justify-content: center;
  margin-bottom: 50px;
}

.search-box {
  width: 618px;
  max-width: 90%;
  background: var(--bg-search);   /* Variabile */
  border: 1px solid var(--border); /* Variabile */
  border-radius: 15px;
  padding: 15px 30px;
  display: flex;
  flex-direction: column;
  gap: 23px;
  box-shadow: 0 4px 10px rgba(0,0,0,0.05);
}

.search-input { display: flex; align-items: center; gap: 15px; }
.search-input .icon { font-size: 20px; filter: grayscale(1); opacity: 0.5; }

.search-input input {
  border: none;
  background: transparent;
  outline: none;
  font-size: 16px;
  color: var(--text-main); /* Variabile */
  width: 100%;
}
.search-input input::placeholder { color: var(--text-gray); }

.search-bottom { display: flex; justify-content: space-between; align-items: center; min-height: 24px; }
.chips { display: flex; gap: 12px; flex-wrap: wrap; }

.chip {
  background: var(--chip-bg);    /* Variabile */
  color: var(--chip-text);       /* Variabile */
  padding: 2px 12px;
  border-radius: 6px;
  font-size: 14px;
  display: flex; align-items: center; gap: 6px;
}
.chip button { border: none; background: none; color: inherit; cursor: pointer; font-weight: bold; padding: 0; }

.send { font-size: 20px; cursor: pointer; color: var(--primary); transition: opacity 0.2s; }
.send.disabled { opacity: 0.2; cursor: default; color: var(--text-gray); }

/* --- RESULTS --- */
.results { padding: 0 50px 75px; }
.loading-state { text-align: center; color: var(--text-gray); padding: 20px; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 36px; justify-content: center; }

/* --- CARD (Home) --- */
.card {
  background: var(--bg-card); /* Variabile */
  border: 1px solid var(--border); /* Variabile */
  border-radius: 15px;
  padding: 30px;
  position: relative;
  display: flex; flex-direction: column;
  transition: transform 0.2s;
}
.card:hover { transform: translateY(-10px); border-color: var(--primary); }

.card h3 { 
  margin: 0; font-size: 24px; 
  color: var(--text-main); /* Variabile */
  padding-right: 80px; /* Spazio per il tempo */
  line-height: 1.3;
}

/* TEMPO IN ALTO A DESTRA */
.time-badge {
  position: absolute;
  top: 30px;
  right: 30px;
  color: var(--text-gray); /* Variabile */
  background: var(--bg-search); /* Sfondo leggero per contrasto */
  padding: 4px 8px;
  border-radius: 8px;
  font-size: 14px;
}

.ingredients { margin-top: 15px; color: var(--text-gray); margin-bottom: 60px; line-height: 1.6; }
.ingredients strong { color: var(--text-main); }

.primary {
  position: absolute; bottom: 30px; right: 30px;
  background: var(--primary); /* Variabile */
  color: #fff; border: none;
  border-radius: 8px; padding: 10px 20px; cursor: pointer;
  font-weight: 600; font-size: 14px;
}

/* --- MODALE (Overlay) --- */
.recipe-modal {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.6); /* Backdrop scuro */
  backdrop-filter: blur(3px);
  z-index: 2000;
  display: flex; justify-content: center; align-items: center;
  padding: 20px;
  animation: fadeIn 0.2s ease-out;
}

.recipe-card-modal {
  width: 100%; max-width: 900px; max-height: 90vh;
  overflow-y: auto;
  background: var(--bg-card); /* Variabile */
  border: 1px solid var(--border); /* Variabile */
  border-radius: 15px;
  box-shadow: 0 20px 50px rgba(0,0,0,0.3);
  display: flex; flex-direction: column;
}

.card-header {
  padding: 15px 30px;
  border-bottom: 1px solid var(--border);
  display: flex; justify-content: space-between; align-items: center;
}
.back-link { color: var(--primary); text-decoration: none; font-weight: 600; font-size: 14px; }
.icon-header { font-size: 24px; }

.card-content { padding: 30px; display: flex; flex-direction: column; gap: 30px; }

.title-row { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; }
.title-row h2 { margin: 0; font-size: 32px; font-weight: 700; color: var(--text-main); }
.time-big { font-size: 20px; color: var(--text-gray); }

.text-block { font-size: 16px; line-height: 1.6; color: var(--text-gray); }
.text-block strong { color: var(--text-main); }

.clean-list { padding-left: 20px; margin: 0; }
.step-list { padding-left: 20px; margin: 0; }
.step-list li { margin-bottom: 12px; }

.primary-link { color: var(--primary); font-weight: bold; text-decoration: none; }

@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
</style>