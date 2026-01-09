/**
 * Escape HTML special characters in a string
 * @param {string} text - Text to escape
 * @returns {string} Escaped text
 */
export function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Get styling for violation level badges
 * @param {string} level - Violation level (low, moderate, severe)
 * @returns {Object} Style object
 */
export function getViolationLevelStyle(level) {
    const levelLower = level?.toLowerCase();
    let levelColor = '#95a5a6';
    
    if (levelLower === 'low') {
        levelColor = '#f39c12';
    } else if (levelLower === 'moderate') {
        levelColor = '#e67e22';
    } else if (levelLower === 'severe') {
        levelColor = '#e74c3c';
    }
    
    return {
        color: levelColor,
        fontSize: '0.85em',
        marginLeft: '6px'
    };
}

/**
 * Copy text to clipboard with fallback for older browsers
 * @param {string} text - Text to copy
 * @param {Function} [onSuccess] - Success callback
 * @param {Function} [onError] - Error callback
 */
export async function copyToClipboard(text, onSuccess, onError) {
    try {
        if (navigator.clipboard && navigator.clipboard.writeText) {
            await navigator.clipboard.writeText(text);
            onSuccess?.();
        } else {
            // Fallback for browsers without Clipboard API
            const textarea = document.createElement('textarea');
            textarea.value = text;
            textarea.style.position = 'fixed';
            textarea.style.opacity = '0';
            document.body.appendChild(textarea);
            textarea.select();
            try {
                document.execCommand('copy');
                onSuccess?.();
            } catch (err) {
                onError?.(err);
            } finally {
                document.body.removeChild(textarea);
            }
        }
    } catch (err) {
        onError?.(err);
    }
}

/**
 * Format a date string for display
 * @param {string} dateStr - Date string
 * @returns {string} Formatted date
 */
export function formatDate(dateStr) {
    if (!dateStr) return 'Date not specified';
    try {
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    } catch {
        return dateStr;
    }
}

/**
 * Get base URL from Vite environment
 * @returns {string} Base URL
 */
export function getBaseUrl() {
    return import.meta.env.BASE_URL || '/';
}

// Active license statuses
export const ACTIVE_LICENSE_STATUSES = ['Regular', 'Original', '1st Provisional', '2nd Provisional', 'Inspected'];
