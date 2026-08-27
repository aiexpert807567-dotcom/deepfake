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
          950: '#06070a',
          900: '#0c0e15',
          850: '#11141e',
          800: '#171b28',
          750: '#1d2334',
          700: '#262e44',
          600: '#384364',
          accent: '#6366f1',
          accentGlow: '#4f46e5',
          cyan: '#06b6d4',
          emerald: '#10b981',
          rose: '#f43f5e',
        }
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 15px rgba(99, 102, 241, 0.4)' },
          '100%': { boxShadow: '0 0 25px rgba(99, 102, 241, 0.8)' },
        }
      }
    },
  },
  plugins: [],
}
