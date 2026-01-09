import React from 'react';

/**
 * Header component for the dashboard
 * @param {Object} props
 * @param {string} props.title - Main title text
 * @param {string} props.subtitle - Subtitle text
 */
export function Header({ title, subtitle }) {
    return (
        <header>
            <div className="container">
                <h1>{title}</h1>
                {subtitle && <p className="subtitle">{subtitle}</p>}
            </div>
        </header>
    );
}

export default Header;
