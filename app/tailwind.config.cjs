/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{html,jsx,tsx}',
    './shared/**/*.{html,jsx,tsx}',
    './renderer/**/*.{vue,js,ts,jsx,tsx}',
  ],
  corePlugins: { preflight: false },
  theme: {
    extend: {},
  },
  plugins: [],
};
