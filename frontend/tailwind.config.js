/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        spotify: {
          green: '#1DB954',
          black: '#191414',
          dark: '#121212',
          gray: '#535353',
          light: '#282828',
        },
        mood: {
          happy: '#1DB954',
          energetic: '#FF6B6B',
          calm: '#4ECDC4',
          romantic: '#FF9FF3',
          sad: '#45B7D1',
          aggressive: '#FF6B35',
          dreamy: '#9B59B6',
          mixed: '#F39C12',
          neutral: '#95A5A6'
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'bounce-slow': 'bounce 2s infinite',
        'float': 'float 6s ease-in-out infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        glow: {
          '0%': { boxShadow: '0 0 20px rgba(29, 185, 84, 0.3)' },
          '100%': { boxShadow: '0 0 30px rgba(29, 185, 84, 0.6)' },
        }
      },
    },
  },
  plugins: [],
}