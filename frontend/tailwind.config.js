/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class', // Enable class-based dark mode
  theme: {
    extend: {
      colors: {
        // 2025 Theme System - Using CSS custom properties for theme switching
        bg: {
          DEFAULT: 'var(--color-bg)',
          secondary: 'var(--color-bg-secondary)',
          tertiary: 'var(--color-bg-tertiary)',
        },
        text: {
          primary: 'var(--color-text-primary)',
          secondary: 'var(--color-text-secondary)',
          tertiary: 'var(--color-text-tertiary)',
        },
        icon: {
          DEFAULT: 'var(--color-icon)',
        },
        stroke: {
          subtle: 'var(--color-stroke-subtle)',
        },
        accent: {
          blue: 'var(--color-accent-blue)',
          violet: 'var(--color-accent-violet)',
          mint: 'var(--color-accent-mint)',
        },
        ai: {
          DEFAULT: 'var(--color-ai-button)',
          hover: 'var(--color-ai-button-hover)',
          text: 'var(--color-ai-button-text)',
        },
        // Semantic colors
        success: '#16C39A',
        warning: '#F59E0B',
        error: '#EF4444',
      },
      borderRadius: {
        'button': '10px', // Standard button radius
        'card': '12px',   // Card radius
        'modal': '16px',  // Modal radius
      },
      opacity: {
        'hover': '0.05',    // Hover layer opacity
        'active': '0.10',   // Active layer opacity
        'disabled': '0.40', // Disabled state opacity
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'gradient': 'gradient 8s ease infinite',
        'float': 'float 3s ease-in-out infinite',
      },
      keyframes: {
        gradient: {
          '0%, 100%': {
            'background-size': '200% 200%',
            'background-position': 'left center'
          },
          '50%': {
            'background-size': '200% 200%',
            'background-position': 'right center'
          },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        },
      },
    },
  },
  plugins: [],
}
