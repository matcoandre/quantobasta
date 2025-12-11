<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';

// --- STATO DARK MODE ---
const isDark = ref(false);

const toggleTheme = () => {
  isDark.value = !isDark.value;
  if (isDark.value) {
    document.documentElement.classList.add('dark');
    localStorage.setItem('theme', 'dark');
  } else {
    document.documentElement.classList.remove('dark');
    localStorage.setItem('theme', 'light');
  }
};

// Al caricamento, controlliamo le preferenze salvate
onMounted(() => {
  const userTheme = localStorage.getItem('theme');
  const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  
  if (userTheme === 'dark' || (!userTheme && systemDark)) {
    isDark.value = true;
    document.documentElement.classList.add('dark');
  } else {
    isDark.value = false;
    document.documentElement.classList.remove('dark');
  }
});

// --- STATO RICERCA ---
const query = ref('');
const results = ref([]);
const loading = ref(false);
const searchPerformed = ref(false);
const tokensUsed = ref([]);
const selectedRecipe = ref(null);
const serverStatus = ref('Check...');

const checkServer = async () => {
  try { await axios.get('/api/'); serverStatus.value = '🟢 Online'; }
  catch { serverStatus.value = '🔴 Offline'; }
}
checkServer();

const search = async () => {
  if (!query.value) return;
  loading.value = true;
  searchPerformed.value = true;
  selectedRecipe.value = null;
  results.value = [];
  
  try {
    const res = await axios.get('/api/search', { params: { q: query.value, limit: 12 } });
    results.value = res.data.results;
    tokensUsed.value = res.data.query_tokens;
  } catch (e) {
    console.error(e);
  } finally {
    loading.value = false;
  }
};

const selectRecipe = (r) => {
  selectedRecipe.value = r;
  window.scrollTo(0,0);
};
</script>

<template>
  <!-- ROOT: Gestisce i colori di base Light/Dark -->
  <div class="min-h-screen font-sans transition-colors duration-300 bg-orange-50 text-slate-800 dark:bg-slate-900 dark:text-slate-100">
    
    <!-- HEADER -->
    <header class="sticky top-0 z-10 p-4 shadow-sm bg-white border-b border-orange-100 dark:bg-slate-800 dark:border-slate-700">
      <div class="max-w-4xl mx-auto flex justify-between items-center">
        
        <!-- LOGO / NOME -->
        <h1 class="text-2xl font-bold text-orange-600 cursor-pointer flex items-center gap-2 dark:text-orange-500" @click="selectedRecipe = null">
          <span>👨‍🍳</span> QuantoBasta
        </h1>
        
        <!-- DESTRA: STATUS + TOGGLE -->
        <div class="flex items-center gap-4">
          <span class="text-xs font-mono px-2 py-1 rounded bg-slate-100 dark:bg-slate-700" 
                :class="serverStatus.includes('Online') ? 'text-green-600 dark:text-green-400' : 'text-red-500'">
            {{ serverStatus }}
          </span>

          <!-- TASTO DARK MODE -->
          <button 
            @click="toggleTheme" 
            class="p-2 rounded-full bg-slate-100 text-xl hover:bg-slate-200 transition dark:bg-slate-700 dark:hover:bg-slate-600"
            :title="isDark ? 'Passa alla modalità chiara' : 'Passa alla modalità scura'"
          >
            {{ isDark ? '☀️' : '🌙' }}
          </button>
        </div>
      </div>
    </header>

    <main class="max-w-4xl mx-auto p-4 mt-4">
      
      <!-- VISTA 1: DETTAGLIO RICETTA -->
      <div v-if="selectedRecipe" class="animate-fade-in">
        <button @click="selectedRecipe = null" class="mb-4 font-bold hover:underline flex items-center gap-1 text-orange-600 dark:text-orange-400">
          &larr; Indietro
        </button>
        
        <div class="p-8 rounded-2xl shadow-lg border bg-white border-orange-100 dark:bg-slate-800 dark:border-slate-700">
          <h1 class="text-3xl md:text-4xl font-bold mb-2 text-slate-800 dark:text-white">{{ selectedRecipe.title_page }}</h1>
          <div class="text-xs font-mono mb-8 border-b pb-4 text-slate-400 border-slate-100 dark:border-slate-700">
            Relevance Score: {{ selectedRecipe.score.toFixed(2) }}
          </div>
          
          <div class="grid md:grid-cols-3 gap-8">
            <!-- INGREDIENTI -->
            <div class="p-6 rounded-xl h-fit border bg-orange-50 border-orange-100 dark:bg-slate-900 dark:border-slate-700">
              <h3 class="font-bold mb-4 flex items-center gap-2 text-lg text-orange-800 dark:text-orange-400">
                <span>🛒</span> Ingredienti
              </h3>
              <ul class="text-sm space-y-3">
                <li v-for="(ing, i) in (selectedRecipe.clean_ingredients || [])" :key="i" class="flex gap-2 items-start">
                  <span class="text-orange-500 font-bold">•</span> 
                  <span class="font-medium text-slate-700 dark:text-slate-300">{{ ing }}</span>
                </li>
              </ul>
            </div>
            
            <!-- PROCEDIMENTO -->
            <div class="md:col-span-2">
              <h3 class="font-bold mb-4 flex items-center gap-2 text-lg text-orange-800 dark:text-orange-400">
                <span>🔪</span> Procedimento
              </h3>
              
              <ol class="list-decimal list-outside ml-5 space-y-4 leading-relaxed marker:text-orange-600 marker:font-bold text-slate-700 dark:text-slate-300">
                <li v-for="(step, i) in (selectedRecipe.steps || [])" :key="i" class="pl-2">
                  {{ step }}
                </li>
              </ol>

              <div class="mt-8 pt-6 border-t text-right border-slate-100 dark:border-slate-700">
                <a :href="selectedRecipe.URL" target="_blank" class="inline-block px-6 py-2 text-white font-bold rounded-lg transition shadow-sm bg-orange-600 hover:bg-orange-700 dark:bg-orange-700 dark:hover:bg-orange-600">
                  Vedi su GialloZafferano &rarr;
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- VISTA 2: RICERCA -->
      <div v-else>
        <!-- SEARCH BAR -->
        <div class="p-6 rounded-2xl shadow-sm border mb-8 bg-white border-orange-100 dark:bg-slate-800 dark:border-slate-700">
          <div class="flex gap-3">
            <input 
              v-model="query" 
              @keyup.enter="search" 
              type="text" 
              placeholder="Cerca una ricetta (es. Carbonara)..." 
              class="flex-1 p-4 rounded-xl border shadow-sm transition text-lg focus:outline-none focus:ring-2 
                     border-slate-200 bg-slate-50 focus:bg-white focus:border-orange-500 focus:ring-orange-200
                     dark:border-slate-600 dark:bg-slate-900 dark:focus:bg-slate-900 dark:text-white dark:focus:ring-orange-900"
            >
            <button @click="search" class="text-white px-8 rounded-xl font-bold transition shadow-md bg-orange-600 hover:bg-orange-700 dark:bg-orange-700 dark:hover:bg-orange-600">
              Cerca
            </button>
          </div>
          
          <!-- TOKEN DEBUG -->
          <div v-if="tokensUsed.length" class="mt-3 text-xs flex gap-2 flex-wrap items-center text-slate-500 dark:text-slate-400">
            <span>N-Grams usati:</span>
            <span v-for="t in tokensUsed" :key="t" class="px-2 py-0.5 rounded border bg-orange-100 text-orange-800 border-orange-200 dark:bg-slate-700 dark:text-orange-300 dark:border-slate-600">
              {{ t }}
            </span>
          </div>
        </div>

        <!-- LOADING -->
        <div v-if="loading" class="text-center py-20 font-bold text-xl animate-pulse text-orange-500">
          Sto cercando nel ricettario...
        </div>

        <!-- RISULTATI GRID -->
        <div v-else class="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div 
            v-for="(r, i) in results" 
            :key="i" 
            @click="selectRecipe(r)" 
            class="p-6 rounded-xl shadow-sm border cursor-pointer transition duration-300 group h-full flex flex-col hover:shadow-lg hover:-translate-y-1
                   bg-white border-orange-100 hover:border-orange-300
                   dark:bg-slate-800 dark:border-slate-700 dark:hover:border-slate-500"
          >
            <h3 class="font-bold text-xl mb-3 transition text-slate-800 group-hover:text-orange-600 dark:text-white dark:group-hover:text-orange-400">
              {{ r.title_page }}
            </h3>
            <p class="text-sm mb-4 line-clamp-3 flex-1 text-slate-500 dark:text-slate-400">
              <span v-for="ing in (r.clean_ingredients || []).slice(0, 5)">{{ ing }}, </span>...
            </p>
            <div class="pt-4 border-t text-sm font-bold flex justify-between items-center border-slate-50 text-orange-600 dark:border-slate-700 dark:text-orange-400">
              <span>Leggi Ricetta</span>
              <span>&rarr;</span>
            </div>
          </div>
        </div>
        
        <!-- NESSUN RISULTATO -->
        <div v-if="searchPerformed && results.length === 0 && !loading" class="text-center py-20 text-slate-400">
           <div class="text-4xl mb-2">🤷‍♂️</div>
           Nessuna ricetta trovata per "{{ query }}".
        </div>
      </div>
    </main>
  </div>
</template>

<style>
.animate-fade-in {
  animation: fadeIn 0.4s ease-out;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>