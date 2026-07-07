import type { Config } from 'tailwindcss';

export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#303030',
        muted: '#68737a',
        line: '#dce8ef',
        panel: '#f4fbfd',
        brand: '#40a0d0',
        success: '#80c090',
        warning: '#b7791f',
        danger: '#b42318',
      },
      boxShadow: {
        soft: '0 12px 30px rgba(48, 48, 48, 0.08)',
      },
    },
  },
  plugins: [],
} satisfies Config;
