/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ['class', '[data-theme="midnight"]'],
  content: [
    './index.html',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
        dehon: {
          navy: '#1a2639',
          gold: '#c9a96e',
          'gold-dark': '#a07840',
          'blue-bright': '#3B82F6',
        },
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Outfit', 'sans-serif'],
        serif: ['Lora', 'serif'],
      },
      keyframes: {
        'fade-in': {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'accordion-down': {
          from: { height: '0' },
          to: { height: 'var(--radix-accordion-content-height)' },
        },
        'accordion-up': {
          from: { height: 'var(--radix-accordion-content-height)' },
          to: { height: '0' },
        },
      },
      animation: {
        'fade-in': 'fade-in 0.4s ease-out',
        'accordion-down': 'accordion-down 0.2s ease-out',
        'accordion-up': 'accordion-up 0.2s ease-out',
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
    require('tailwindcss-animate'),
    function ({ addVariant }) {
      addVariant('data-open', ['&[data-state="open"]', '&[data-open]:not([data-open="false"])']);
      addVariant('data-closed', ['&[data-state="closed"]', '&[data-closed]:not([data-closed="false"])']);
      addVariant('data-checked', ['&[data-state="checked"]', '&[data-checked]:not([data-checked="false"])']);
      addVariant('data-unchecked', ['&[data-state="unchecked"]', '&[data-unchecked]:not([data-unchecked="false"])']);
      addVariant('data-selected', '&[data-selected="true"]');
      addVariant('data-disabled', ['&[data-disabled="true"]', '&[data-disabled]:not([data-disabled="false"])']);
      addVariant('data-active', ['&[data-state="active"]', '&[data-active]:not([data-active="false"])']);
      addVariant('data-horizontal', '&[data-orientation="horizontal"]');
      addVariant('data-vertical', '&[data-orientation="vertical"]');
    }
  ],
}
