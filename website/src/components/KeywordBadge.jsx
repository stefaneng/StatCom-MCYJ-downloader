import React from 'react';

/**
 * KeywordBadge component for displaying keywords with optional remove button
 * @param {Object} props
 * @param {string} props.keyword - The keyword text
 * @param {Function} [props.onRemove] - Optional callback to remove the keyword
 * @param {boolean} [props.small] - Use smaller styling
 */
export function KeywordBadge({ keyword, onRemove, small = false }) {
    const badgeStyle = small ? {
        background: '#e8f4f8',
        color: '#2980b9',
        padding: '2px 8px',
        borderRadius: '10px',
        fontSize: '0.75em',
        border: '1px solid #3498db'
    } : {};

    if (small) {
        return (
            <span style={badgeStyle}>
                {keyword}
            </span>
        );
    }

    return (
        <span className="selected-keyword-badge">
            {keyword}
            {onRemove && (
                <button 
                    className="remove-keyword-btn" 
                    onClick={(e) => {
                        e.stopPropagation();
                        onRemove(keyword);
                    }}
                    title="Remove keyword"
                >
                    ✕
                </button>
            )}
        </span>
    );
}

/**
 * KeywordBadgeList component for displaying multiple keywords
 * @param {Object} props
 * @param {Array<string>} props.keywords - Array of keyword strings
 * @param {Function} [props.onRemove] - Optional callback to remove a keyword
 * @param {number} [props.maxDisplay] - Max keywords to display before showing "+N more"
 * @param {boolean} [props.small] - Use smaller styling
 */
export function KeywordBadgeList({ keywords, onRemove, maxDisplay = 5, small = false }) {
    if (!keywords || keywords.length === 0) {
        return null;
    }

    const displayKeywords = maxDisplay ? keywords.slice(0, maxDisplay) : keywords;
    const remainingCount = keywords.length - displayKeywords.length;

    return (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', alignItems: 'center' }}>
            {small && (
                <span style={{ fontSize: '0.8em', color: '#666', marginRight: '4px' }}>🏷️</span>
            )}
            {displayKeywords.map((keyword, index) => (
                <KeywordBadge 
                    key={keyword || index}
                    keyword={keyword}
                    onRemove={onRemove}
                    small={small}
                />
            ))}
            {remainingCount > 0 && (
                <span style={{ fontSize: '0.75em', color: '#666' }}>
                    +{remainingCount} more
                </span>
            )}
        </div>
    );
}

export default KeywordBadge;
