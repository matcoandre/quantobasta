import { createRouter, createWebHistory } from 'vue-router'
import HomeView from './views/HomeView.vue'
import RecipeView from './views/RecipeView.vue'

const routes = [
  { path: '/', name: 'home', component: HomeView },
  { path: '/recipe', name: 'recipe', component: RecipeView, props: true }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router