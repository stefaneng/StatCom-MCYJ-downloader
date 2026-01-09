import React from 'react';

/**
 * Loading component
 * @param {Object} props
 * @param {string} [props.message] - Loading message
 */
export function Loading({ message = 'Loading data...' }) {
    return (
        <div className="loading">
            {message}
        </div>
    );
}

/**
 * Error component
 * @param {Object} props
 * @param {string} props.message - Error message
 */
export function Error({ message }) {
    if (!message) return null;
    
    return (
        <div className="error">
            {message}
        </div>
    );
}

export default Loading;
