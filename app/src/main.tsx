import { Theme } from '@radix-ui/themes';
import '@radix-ui/themes/styles.css';
import * as React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './styles.css';

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <Theme accentColor="sky" grayColor="gray" panelBackground="solid" scaling="100%" radius="full">
      <App />
    </Theme>
  </React.StrictMode>,
);
