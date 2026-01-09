import React, { useState } from 'react';

/**
 * AutocompleteInput component for search with suggestions
 * @param {Object} props
 * @param {string} props.id - Input element ID
 * @param {string} props.placeholder - Input placeholder text
 * @param {Function} props.onSearch - Callback to get suggestions for a query
 * @param {Function} props.onSelect - Callback when a suggestion is selected
 * @param {Function} [props.renderSuggestion] - Custom render function for suggestions
 */
export function AutocompleteInput({ 
    id, 
    placeholder, 
    onSearch, 
    onSelect, 
    renderSuggestion,
    disabled = false,
    style = {}
}) {
    const [query, setQuery] = useState('');
    const [suggestions, setSuggestions] = useState([]);
    const [showSuggestions, setShowSuggestions] = useState(false);

    const handleInputChange = (e) => {
        const value = e.target.value;
        setQuery(value);

        if (value.trim().length < 2) {
            setSuggestions([]);
            setShowSuggestions(false);
            return;
        }

        const results = onSearch(value.trim());
        setSuggestions(results || []);
        setShowSuggestions(results && results.length > 0);
    };

    const handleSelect = (suggestion) => {
        onSelect(suggestion);
        setQuery('');
        setSuggestions([]);
        setShowSuggestions(false);
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            if (suggestions.length > 0) {
                handleSelect(suggestions[0]);
            }
        }
    };

    const handleBlur = (e) => {
        // Delay hiding to allow click on suggestion
        setTimeout(() => {
            setShowSuggestions(false);
        }, 200);
    };

    const defaultRenderSuggestion = (suggestion) => (
        <>
            <span>{suggestion.keyword || suggestion}</span>
            {suggestion.count !== undefined && (
                <span style={{ color: '#666', fontSize: '0.85em' }}>({suggestion.count})</span>
            )}
        </>
    );

    return (
        <div style={{ position: 'relative', ...style }}>
            <input
                type="text"
                id={id}
                placeholder={placeholder}
                value={query}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                onBlur={handleBlur}
                disabled={disabled}
                style={{
                    width: '100%',
                    padding: '10px',
                    border: '1px solid #ddd',
                    borderRadius: '4px',
                    fontSize: '14px'
                }}
            />
            {showSuggestions && (
                <div style={{
                    position: 'absolute',
                    top: '100%',
                    left: 0,
                    right: 0,
                    background: 'white',
                    border: '1px solid #ddd',
                    borderTop: 'none',
                    borderRadius: '0 0 4px 4px',
                    maxHeight: '200px',
                    overflowY: 'auto',
                    zIndex: 100,
                    boxShadow: '0 4px 8px rgba(0,0,0,0.1)'
                }}>
                    {suggestions.map((suggestion, index) => (
                        <div
                            key={suggestion.keyword || suggestion.id || index}
                            onClick={() => handleSelect(suggestion)}
                            className="keyword-suggestion"
                        >
                            {renderSuggestion 
                                ? renderSuggestion(suggestion)
                                : defaultRenderSuggestion(suggestion)
                            }
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default AutocompleteInput;
