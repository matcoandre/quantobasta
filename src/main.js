import { createApp } from 'vue'
import './style.css' // <--- FONDAMENTALE
import App from './App.vue'
import router from './router.js'

createApp(App).use(router).mount('#app')