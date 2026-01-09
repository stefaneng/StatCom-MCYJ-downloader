import React, { useState } from 'react';
import { DocumentList } from './DocumentItem.jsx';
import { copyToClipboard, getBaseUrl } from '../utils/helpers.js';

/**
 * AgencyCard component for displaying agency information
 * @param {Object} props
 * @param {Object} props.agency - Agency data object
 * @param {boolean} [props.isOpen] - Whether the card details are expanded
 * @param {Function} [props.onToggle] - Callback when card is clicked
 * @param {Function} [props.onCopyDocumentLink] - Callback for copying document link
 */
export function AgencyCard({ agency, isOpen = false, onToggle, onCopyDocumentLink }) {
    const [copyFeedback, setCopyFeedback] = useState(false);
    const baseUrl = getBaseUrl();

    const handleCopyAgencyLink = (e) => {
        e.stopPropagation();
        const url = `${window.location.origin}${window.location.pathname}?agency=${agency.agencyId}`;
        
        copyToClipboard(
            url,
            () => {
                setCopyFeedback(true);
                setTimeout(() => setCopyFeedback(false), 1000);
            },
            (err) => {
                console.error('Failed to copy link:', err);
                alert('Failed to copy link to clipboard');
            }
        );
    };

    const handleCardClick = (e) => {
        // Don't toggle if clicking on buttons or if card is already open
        if (e.target.closest('.copy-link-btn') || e.target.closest('.view-document-btn') || isOpen) {
            return;
        }
        onToggle?.(agency.agencyId);
    };

    // Dynamic styles: when open, remove pointer cursor and hover effects
    const cardStyle = isOpen ? {
        cursor: 'default',
        transform: 'none'
    } : {};

    return (
        <div 
            className={`agency-card ${isOpen ? 'agency-card-open' : ''}`}
            id={`agency-${agency.agencyId}`}
            onClick={handleCardClick}
            style={cardStyle}
        >
            <div className="agency-header">
                <div>
                    <div className="agency-name">
                        {agency.AgencyName || 'Unknown Agency'}
                        <button 
                            className="copy-link-btn" 
                            onClick={handleCopyAgencyLink}
                            title="Copy link to this agency"
                        >
                            {copyFeedback ? '✓' : '🔗'}
                        </button>
                    </div>
                    <div style={{ color: '#666', fontSize: '0.9em', marginTop: '4px' }}>
                        ID: {agency.agencyId}
                    </div>
                </div>
            </div>

            <div className="agency-stats">
                <span className="stat-badge reports-badge">
                    📋 {agency.total_reports} {agency.total_reports === 1 ? 'Report' : 'Reports'}
                    {agency.filtered_out_count > 0 && (
                        <span style={{ color: '#e67e22' }}>
                            {' '}({agency.filtered_out_count} filtered out)
                        </span>
                    )}
                </span>
            </div>

            <div className={`agency-details ${isOpen ? 'visible' : ''}`}>
                <DocumentList 
                    documents={agency.documents}
                    filteredOutCount={agency.filtered_out_count}
                    baseUrl={baseUrl}
                    onCopyLink={onCopyDocumentLink}
                />
            </div>
        </div>
    );
}

/**
 * AgencyList component for displaying a grid of agency cards
 * @param {Object} props
 * @param {Array} props.agencies - Array of agency objects
 * @param {string|null} [props.openAgencyId] - ID of currently open agency
 * @param {Function} [props.onToggleAgency] - Callback when an agency card is toggled
 * @param {Function} [props.onCopyDocumentLink] - Callback for copying document links
 */
export function AgencyList({ agencies, openAgencyId, onToggleAgency, onCopyDocumentLink }) {
    if (!agencies || agencies.length === 0) {
        return (
            <div className="no-results" style={{ display: 'block' }}>
                No agencies found matching your search.
            </div>
        );
    }

    return (
        <div className="agencies-grid">
            {agencies.map((agency) => (
                <AgencyCard
                    key={agency.agencyId}
                    agency={agency}
                    isOpen={openAgencyId === agency.agencyId}
                    onToggle={onToggleAgency}
                    onCopyDocumentLink={onCopyDocumentLink}
                />
            ))}
        </div>
    );
}

export default AgencyCard;
