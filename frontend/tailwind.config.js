/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        studio: {
          950: '#090a0f',
          900: '#10121a',
          800: '#181b26',
          700: '#232838',
          accent: '#6366f1',
          accentHover: '#4f46e5',
        }
      }
    },
  },
  plugins: [],
}
