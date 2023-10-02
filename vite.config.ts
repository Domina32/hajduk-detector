import react from '@vitejs/plugin-react-swc';
import { internalIpV4 } from 'internal-ip';
import { fileURLToPath } from 'node:url';
import { defineConfig } from 'vite';
import checker from 'vite-plugin-checker';
import svgr from 'vite-plugin-svgr';

const mobile = !!/android|ios/.exec(process.env.TAURI_PLATFORM);

// https://vitejs.dev/config/
export default defineConfig(async () => ({
  plugins: [
    react(),
    svgr(),
    checker({
      typescript: true,
      overlay: {
        initialIsOpen: false,
      },
      // stylelint: {
      //   lintCommand:
      //     'stylelint pages/**/*.css shared/**/*.css renderer/**/*.css',
      //   dev: {
      //     logLevel: ['error', 'warning'],
      //   },
      // },
    }),
  ],
  // Vite options tailored for Tauri development and only applied in `tauri dev` or `tauri build`
  //
  // 1. prevent vite from obscuring rust errors
  clearScreen: false,
  // 2. tauri expects a fixed port, fail if that port is not available
  server: {
    host: mobile ? '0.0.0.0' : false,
    port: 1420,
    hmr: mobile
      ? {
          protocol: 'ws',
          host: await internalIpV4(),
          port: 1421,
        }
      : undefined,
    strictPort: true,
  },
  // 3. to make use of `TAURI_DEBUG` and other env variables
  // https://tauri.studio/v1/api/config#buildconfig.beforedevcommand
  envPrefix: ['VITE_', 'TAURI_'],
  css: {
    modules: {
      generateScopedName: '[name]_[local]__[hash:base64:5]',
    },
  },
  resolve: {
    alias: [
      {
        find: '#',
        replacement: fileURLToPath(new URL('./src', import.meta.url)),
      },
      {
        find: '#assets',
        replacement: fileURLToPath(new URL('./assets', import.meta.url)),
      },
      {
        find: '#shared',
        replacement: fileURLToPath(new URL('./shared', import.meta.url)),
      },
      {
        find: '#hooks',
        replacement: fileURLToPath(new URL('./shared/hooks', import.meta.url)),
      },
      {
        find: '#utils',
        replacement: fileURLToPath(new URL('./shared/utils', import.meta.url)),
      },
      {
        find: '#styles',
        replacement: fileURLToPath(new URL('./shared/styles', import.meta.url)),
      },
      {
        find: '#components',
        replacement: fileURLToPath(new URL('./shared/components', import.meta.url)),
      },
      {
        find: '#pages',
        replacement: fileURLToPath(new URL('./pages', import.meta.url)),
      },
      {
        find: '#public',
        replacement: fileURLToPath(new URL('./public', import.meta.url)),
      },
    ],
  },
}));
