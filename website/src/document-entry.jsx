import React from 'react';
import { createRoot } from 'react-dom/client';
import { DocumentPage } from './pages/DocumentPage.jsx';
import './styles/common.css';

// Render the DocumentPage component
const container = document.getElementById('root');
const root = createRoot(container);
root.render(<DocumentPage />);
