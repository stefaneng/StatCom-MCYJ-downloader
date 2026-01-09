import React from 'react';
import { createRoot } from 'react-dom/client';
import { KeywordsPage } from './pages/KeywordsPage.jsx';
import './styles/common.css';

// Render the KeywordsPage component
const container = document.getElementById('root');
const root = createRoot(container);
root.render(<KeywordsPage />);
