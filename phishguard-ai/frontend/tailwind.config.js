/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        navy: {
          50: '#eef2ff',
          100: '#dce4fd',
          200: '#b9c9fb',
          300: '#8ba6f7',
          400: '#5b7ef2',
          500: '#3b5ce6',
          600: '#2a42c9',
          700: '#2235a3',
          800: '#1e2d7d',
          900: '#0f1729',
          950: '#0a0f1d',
        },
        teal: {
          50: '#edfffe',
          100: '#d1fffe',
          200: '#a9fefb',
          300: '#6bfbf7',
          400: '#2eeee9',
          500: '#14d4d0',
          600: '#0da9a9',
          700: '#118787',
          800: '#156b6b',
          900: '#165858',
          950: '#063838',
        },
      },
    },
  },
  plugins: [],
};

