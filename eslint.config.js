import airbnbTs from 'eslint-config-airbnb-typescript';
import airbnb from 'eslint-config-airbnb';
import airbnbHooks from 'eslint-config-airbnb/hooks';
import js from '@eslint/js';
import tsEslint from '@typescript-eslint/eslint-plugin';
import tsParser from '@typescript-eslint/parser';
import importPlugin from 'eslint-plugin-import';
import reactPlugin from 'eslint-plugin-react';
import prettierPlugin from 'eslint-config-prettier';
import useMemoPlugin from 'eslint-plugin-usememo-recommendations';
import { FlatCompat } from '@eslint/eslintrc';
import globals from 'globals';

const compat = new FlatCompat();

const thirdPartyRules = {
  ...tsEslint.configs['strict-type-checked'].rules,
  ...airbnbTs.rules,
};

const config = {
  languageOptions: {
    parser: tsParser,
    parserOptions: {
      project: ['./tsconfig.json', './tsconfig.node.json'],
      tsConfigRootDir: import.meta.url,
    },
    globals: {
      NodeJS: 'readonly',
      React: 'readonly',
      JSX: 'readonly',
      ...globals.browser,
    },
  },
  linterOptions: {
    reportUnusedDisableDirectives: true,
  },
  plugins: {
    '@typescript-eslint': tsEslint,
    'eslint-plugin-react': reactPlugin,
    'eslint-plugin-prettier': prettierPlugin,
    'usememo-recommendations': useMemoPlugin,
  },
  rules: {
    ...thirdPartyRules,
    '@typescript-eslint/switch-exhaustiveness-check': ['warn'],
    'usememo-recommendations/detect-heavy-operations': ['warn'],
    'padding-line-between-statements': [
      'warn',
      {
        blankLine: 'always',
        prev: 'break',
        next: '*',
      },
      {
        blankLine: 'always',
        prev: 'class',
        next: '*',
      },
      {
        blankLine: 'always',
        prev: 'cjs-import',
        next: '*',
      },
      {
        blankLine: 'always',
        prev: 'const',
        next: '*',
      },
      {
        blankLine: 'always',
        prev: '*',
        next: 'const',
      },
      {
        blankLine: 'always',
        prev: '*',
        next: 'if',
      },
      {
        blankLine: 'always',
        prev: '*',
        next: 'return',
      },
      {
        blankLine: 'always',
        prev: '*',
        next: 'block',
      },
      {
        blankLine: 'always',
        prev: '*',
        next: 'block-like',
      },
      {
        blankLine: 'any',
        prev: 'const',
        next: 'const',
      },
    ],
    'object-curly-spacing': ['error', 'always'],
    quotes: ['error', 'single'],
    'jsx-quotes': ['error', 'prefer-double'],
    'import/prefer-default-export': [
      'warn',
      {
        target: 'single',
      },
    ],
    'import/extensions': [
      'warn',
      'ignorePackages',
      {
        js: 'never',
        jsx: 'never',
        ts: 'never',
        tsx: 'never',
      },
    ],
    'no-restricted-syntax': [
      'error',
      {
        selector:
          "ImportDeclaration[source.value='react'][specifiers.0.type='ImportDefaultSpecifier']",
        message: 'Default React import not allowed',
      },
    ],
    'react/require-default-props': [
      2,
      {
        classes: 'defaultProps',
        functions: 'defaultArguments',
      },
    ],
    'react/prop-types': 0,
    'react/function-component-definition': [
      'warn',
      {
        namedComponents: ['arrow-function'],
        unnamedComponents: ['arrow-function'],
      },
    ],
    'react/jsx-props-no-spreading': 'off',
    'react/jsx-filename-extension': [
      'error',
      {
        extensions: ['.jsx', '.tsx'],
      },
    ],
    'import/no-extraneous-dependencies': [
      'error',
      {
        devDependencies: [
          '**/*.test.ts',
          './vite.config.ts',
          './postcss.config.cjs',
          './prettier.config.cjs',
        ],
      },
    ],
  },
  settings: {
    react: {
      version: 'detect',
    },
    'import/resolver': {
      typescript: {},
      alias: {
        map: [
          ['#', './src'],
          ['#assets', './assets'],
          ['#shared', './shared'],
          ['#pages', './pages'],
          ['#utils', './shared/utils'],
          ['#hooks', './shared/hooks'],
          ['#components', './shared/components'],
          ['#styles', './shared/styles'],
        ],
      },
    },
  },
};

const globalIgnores = {
  ignores: ['**/eslint.config.js'],
};

const globalFiles = {
  files: ['**/*.ts', '**/*.tsx', '**/*.js', '**/*.jsx'],
};

export default [
  ...compat.config(importPlugin.configs.recommended),
  ...compat.config(airbnb),
  ...compat.config(airbnbHooks),
  ...compat.config(reactPlugin.configs.recommended),
  ...compat.config(reactPlugin.configs['jsx-runtime']),
  js.configs.recommended,
  prettierPlugin,
  config,
  globalIgnores,
  globalFiles,
];
