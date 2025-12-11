<script setup>
import { ref } from 'vue';
import axios from 'axios';

const query = ref('');
const results = ref([]);
const loading = ref(false);
const searchPerformed = ref(false);
const tokensUsed = ref([]);
const serverStatus = ref('In attesa...');

// Test connessione backend
const checkBackend = async () => {
  try {
    await axios.get('/api/'); // Usa il proxy
    serverStatus.value = '🟢 Backend Connesso';
  } catch (e) {
    serverStatus.value = '🔴 Backend Disconnesso (Attendi avvio Python...)';
  }
};
checkBackend();

const search = async () => {
  if (!query.value.trim()) return;
  loading.value = true;
  searchPerformed.value = true;
  results.value = [];

  try {
    // NOTA: Usiamo /api/search invece di localhost:8000
    const response = await axios.get(`/api/search`, {
      params: { q: query.value, limit: 12 },
    });
    results.value = response.data.results;
    tokensUsed.value = response.data.query_tokens;
  } catch (error) {
    console.error(error);
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div class="min-h-screen bg-orange-50 text-slate-800 font-sans p-4">
    <header class="max-w-4xl mx-auto text-center mb-8 pt-6">
      <h1 class="text-4xl font-bold text-orange-600 mb-2">
        🇮🇹 Il Cucchiaio AI
      </h1>
      <p class="text-slate-600">Motore di ricerca semantico (BM25 + N-grams)</p>
      <div
        class="text-xs mt-2 font-mono"
        :class="serverStatus.includes('🟢') ? 'text-green-600' : 'text-red-500'"
      >
        Status Sistema: {{ serverStatus }}
      </div>
    </header>

    <main class="max-w-4xl mx-auto">
      <div class="flex gap-2 mb-6">
        <input
          v-model="query"
          @keyup.enter="search"
          type="text"
          placeholder="Cerca ingredienti o ricette (es. Tiramisù, Guanciale...)"
          class="flex-1 p-4 rounded-lg border border-orange-200 shadow-sm focus:outline-none focus:border-orange-500"
        />
        <button
          @click="search"
          class="bg-orange-600 text-white px-6 rounded-lg font-bold hover:bg-orange-700 transition"
          :disabled="loading"
        >
          {{ loading ? '...' : 'Cerca' }}
        </button>
      </div>

      <div
        v-if="searchPerformed && tokensUsed.length"
        class="mb-6 p-3 bg-white rounded border border-slate-200 text-xs"
      >
        <span class="font-bold text-slate-500">Token Analizzati:</span>
        <div class="flex flex-wrap gap-1 mt-1">
          <span
            v-for="t in tokensUsed"
            :key="t"
            class="bg-slate-100 px-2 py-0.5 rounded text-slate-700"
          >
            {{ t }}
          </span>
        </div>
      </div>

      <div v-if="loading" class="text-center py-10 text-orange-500">
        Caricamento...
      </div>

      <div
        v-else-if="results.length"
        class="grid grid-cols-1 md:grid-cols-2 gap-4"
      >
        <article
          v-for="(r, i) in results"
          :key="i"
          class="bg-white p-5 rounded-xl shadow-sm border border-orange-100 hover:shadow-md transition"
        >
          <h3 class="font-bold text-lg text-orange-800">{{ r.title_page }}</h3>
          <div class="text-xs text-slate-400 font-mono mb-2">
            Score: {{ r.score.toFixed(2) }}
          </div>
          <p class="text-sm text-slate-600 line-clamp-2 mb-3">
            {{ r.ingredients }}
          </p>
          <a
            :href="r.URL"
            target="_blank"
            class="text-xs font-bold text-orange-600 hover:underline"
            >VAI ALLA RICETTA →</a
          >
        </article>
      </div>

      <div v-else-if="searchPerformed" class="text-center text-slate-500 mt-10">
        Nessun risultato trovato. <br />
        <span class="text-xs"
          >(Se stai usando i dati dummy, prova a cercare "Carbonara" o
          "Pollo")</span
        >
      </div>
    </main>
  </div>
</template>
