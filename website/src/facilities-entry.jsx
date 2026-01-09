import React from 'react';
import { createRoot } from 'react-dom/client';
import { FacilitiesPage } from './pages/FacilitiesPage.jsx';
import './styles/common.css';

// Render the FacilitiesPage component
const container = document.getElementById('root');
const root = createRoot(container);
root.render(<FacilitiesPage />);
