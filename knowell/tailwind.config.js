/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          light: '#e89fba',
          DEFAULT: '#ca404f',
          dark: '#7c1d21',
        },
        secondary: {
          light: '#d8ebf2',
          DEFAULT: '#d2ecf2',
          dark: '#7c1d23',
        }
      }
    },
  },
  plugins: [],
}