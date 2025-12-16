<script setup>
import { computed } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();

// Recuperiamo i dati passati dalla Home
const recipe = computed(() => {
  if (history.state.recipeData) {
    return JSON.parse(history.state.recipeData);
  }
  return null;
});

// Se non c'è ricetta (es. ricarica pagina diretta), torna home
if (!recipe.value) {
  router.push('/');
}
</script>

<template>
  <div class="page-center" v-if="recipe">
    
    <div class="recipe-card card">
      
      <!-- HEADER -->
      <div class="card-header">
        <a href="#" @click.prevent="router.back()" class="back-link">← Torna indietro</a>
        <span class="header-icon">🍴</span>
      </div>

      <!-- CONTENT -->
      <div class="card-content">

        <div class="title-row">
          <h2>{{ recipe.title_page }}</h2>

          <div class="time">
            ⏱ {{ 15 + (recipe.steps?.length || 5) * 5 }} min
          </div>
        </div>

        <div class="text">
          <strong>Ingredienti:</strong><br><br>
          <ul class="ing-list">
            <li v-for="(ing, i) in (recipe.clean_ingredients || [])" :key="i">
              {{ ing }}
            </li>
          </ul>
        </div>

        <div class="text">
          <strong>Preparazione:</strong><br><br>
          <ol class="step-list">
            <li v-for="(step, i) in (recipe.steps || [])" :key="i">
              {{ step }}
            </li>
          </ol>
        </div>
        
        <div class="link-row">
           <a :href="recipe.URL" target="_blank" class="external-link">Vedi originale su GialloZafferano →</a>
        </div>

      </div>

    </div>
  </div>
</template>

<style scoped>
/* PAGINA CENTRATA */
.page-center {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  padding: 50px 20px;
}

/* RECIPE CARD (Dal tuo CSS) */
.recipe-card {
  display: flex;
  width: 100%;
  max-width: 900px; /* Adattato per schermi normali, 1362px è molto largo */
  padding-bottom: 30px;
  flex-direction: column;
  
  background: var(--bg-card);
  border-radius: 15px;
  border: 1px solid var(--border);
  box-shadow: 0 4px 4px rgba(0, 0, 0, 0.10), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
}

/* HEADER */
.card-header {
  width: 100%;
  padding: 15px 30px;
  border-bottom: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.back-link {
  color: #0099FF;
  text-decoration: none;
  font-weight: 600;
  font-size: 14px;
}

.header-icon { font-size: 24px; }

/* CONTENT */
.card-content {
  width: 100%;
  padding: 30px;
  display: flex;
  flex-direction: column;
  gap: 30px;
}

/* TITLE ROW */
.title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.title-row h2 {
  margin: 0;
  font-size: 32px;
  font-weight: 700;
  color: var(--text-main);
}

.time {
  font-size: 20px;
  color: var(--text-gray);
}

/* TEXT BLOCKS */
.text {
  font-size: 16px;
  line-height: 24px;
  color: var(--text-gray);
}

.text strong { color: var(--text-main); }

.ing-list, .step-list {
  padding-left: 20px;
  margin: 0;
}
.step-list li { margin-bottom: 10px; }

.external-link {
  color: #0099FF;
  font-weight: bold;
  text-decoration: none;
}
</style>