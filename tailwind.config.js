/** @type {import('tailwindcss').Config} */
export default {
  // Abilita la dark mode basata sulla classe "dark" nel tag HTML
  darkMode: 'class', 
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}