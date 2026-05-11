/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        agv: {
          idle: '#16a34a',
          busy: '#2563eb',
          fault: '#dc2626',
        },
      },
      boxShadow: {
        panel: '0 10px 30px rgba(15, 23, 42, 0.08)',
      },
      keyframes: {
        pulseBlue: {
          '0%, 100%': { boxShadow: '0 0 0 0 rgba(37, 99, 235, 0.4)' },
          '50%': { boxShadow: '0 0 0 10px rgba(37, 99, 235, 0)' },
        },
        flashBorder: {
          '0%': { transform: 'scale(1)' },
          '50%': { transform: 'scale(1.04)' },
          '100%': { transform: 'scale(1)' },
        },
      },
      animation: {
        'pulse-blue': 'pulseBlue 1.8s infinite',
        'flash-border': 'flashBorder 0.5s ease-in-out 3',
      },
    },
  },
  plugins: [],
}
