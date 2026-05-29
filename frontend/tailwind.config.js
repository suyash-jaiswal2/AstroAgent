import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['Cinzel', 'serif'],
        body: ['Cormorant Garamond', 'serif'],
        ui: ['Inter', 'sans-serif'],
      },
      colors: {
        void: '#04040C',
        'deep-space': '#080818',
        nebula: '#0D0D2B',
        cosmic: '#12123A',
        gold: '#C9A84C',
        'gold-bright': '#F4D03F',
        celestial: '#E8E8FF',
        stardust: '#9090C0',
      },
      animation: {
        'orb-breathe': 'orb-breathe 4s ease-in-out infinite',
        'orb-ripple': 'orb-ripple 0.6s ease-out forwards',
        'fade-in': 'fade-in 0.8s ease forwards',
        'slide-up': 'slide-up 0.6s ease forwards',
        'twinkle': 'twinkle 3s ease-in-out infinite alternate',
        'nebula-drift': 'nebula-drift 20s ease-in-out infinite',
        'energy-stream': 'energy-stream 1.5s ease-in-out infinite',
        'pulse-soft': 'pulse-soft 2s ease-in-out infinite',
      },
    },
  },
  plugins: [],
} satisfies Config