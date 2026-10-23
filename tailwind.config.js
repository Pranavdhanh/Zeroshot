/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        navy: {
          950: '#060A12',
          900: '#0B0F19',
          850: '#0F1626',
          800: '#141E33',
          700: '#1B2844',
        },
        surface: {
          DEFAULT: '#111A2E',
          card: '#131D33',
          elevated: '#18243E',
          hover: '#1D2C4D',
          border: '#23324E',
          'border-subtle': '#1C2942',
        },
        accent: {
          cyan: '#06B6D4',
          'cyan-bright': '#22D3EE',
          'cyan-muted': '#0891B2',
          glow: 'rgba(6, 182, 212, 0.15)',
        },
        risk: {
          allow: '#10B981',
          'allow-bg': 'rgba(16, 185, 129, 0.12)',
          'allow-border': 'rgba(16, 185, 129, 0.25)',
          warn: '#F59E0B',
          'warn-bg': 'rgba(245, 158, 11, 0.12)',
          'warn-border': 'rgba(245, 158, 11, 0.25)',
          hold: '#EF4444',
          'hold-bg': 'rgba(239, 68, 68, 0.12)',
          'hold-border': 'rgba(239, 68, 68, 0.25)',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      animation: {
        'pulse-subtle': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'ping-slow': 'ping 2s cubic-bezier(0, 0, 0.2, 1) infinite',
      }
    },
  },
  plugins: [],
}
