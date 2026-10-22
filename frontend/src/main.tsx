import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { ScenarioProvider } from './context/ScenarioContext';
import { ViewModeProvider } from './context/ViewModeContext';
import { App } from './App';
import './styles/index.css';

const container = document.getElementById('root');
if (!container) {
  throw new Error('Root container element not found.');
}

const root = createRoot(container);

root.render(
  <StrictMode>
    <BrowserRouter>
      <ScenarioProvider>
        <ViewModeProvider>
          <App />
        </ViewModeProvider>
      </ScenarioProvider>
    </BrowserRouter>
  </StrictMode>
);
