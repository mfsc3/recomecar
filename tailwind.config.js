/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './accounts/**/*.py',
    './vagas/**/*.py',
    './vitrine/**/*.py',
  ],
  theme: {
    extend: {
      colors: {
        purple: {
          50:  '#FBF6F0', 100: '#F5E6EA', 200: '#E8C9D4', 300: '#DBA4B8',
          400: '#C77B95', 500: '#B76B87', 600: '#8A4D6B', 700: '#4A1F3D',
          800: '#3A1830', 900: '#2D0F24',
        },
        violet: {
          50:  '#FBF6F0', 100: '#F5E6EA', 200: '#E8C9D4', 300: '#DBA4B8',
          400: '#C77B95', 500: '#B76B87', 600: '#8A4D6B', 700: '#4A1F3D',
          800: '#3A1830', 900: '#2D0F24', 950: '#2D0F24',
        },
      },
      fontFamily: {
        serif: ['"Playfair Display"', 'Georgia', '"Times New Roman"', 'serif'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
};