import React from 'react';
import { createRoot } from 'react-dom/client';
import { App } from './pages/App.jsx';
import './styles/common.css';

// Render the main App component
const container = document.getElementById('root');
const root = createRoot(container);
root.render(<App />);
