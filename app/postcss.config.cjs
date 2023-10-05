module.exports = {
  plugins: {
    'postcss-import': {
      from: 'renderer/index.css',
    },
    'postcss-nested-ancestors': {},
    'tailwindcss/nesting': {},
    tailwindcss: {},
    autoprefixer: {},
  },
};
