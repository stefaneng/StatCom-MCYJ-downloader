import React from 'react';
import { KeywordBadge, KeywordBadgeList } from './KeywordBadge.jsx';
import { AutocompleteInput } from './AutocompleteInput.jsx';
import { getBaseUrl } from '../utils/helpers.js';

/**
 * FilterPanel component for filtering agencies and documents
 * @param {Object} props
 * @param {Object} props.filters - Current filter state
 * @param {Function} props.onFilterChange - Callback when filters change
 * @param {Function} props.onKeywordSearch - Function to search keywords
 * @param {Function} props.onKeywordSelect - Callback when keyword is selected
 * @param {Function} props.onKeywordRemove - Callback when keyword is removed
 * @param {Function} props.onClearAllKeywords - Callback to clear all keywords
 * @param {Function} props.onAgencySearch - Function to search agencies
 * @param {Function} props.onAgencySelect - Callback when agency is selected
 * @param {Function} props.onAgencyRemove - Callback when agency is removed
 * @param {Array} props.uniqueLicenseStatuses - Available license status options
 * @param {Array} props.uniqueAgencyTypes - Available agency type options
 * @param {Array} props.uniqueCounties - Available county options
 * @param {string} [props.selectedAgencyText] - Display text for selected agency
 * @param {number} props.totalAgencies - Total agencies count
 * @param {number} props.totalReports - Total reports count
 */
export function FilterPanel({
    filters,
    onFilterChange,
    onKeywordSearch,
    onKeywordSelect,
    onKeywordRemove,
    onClearAllKeywords,
    onAgencySearch,
    onAgencySelect,
    onAgencyRemove,
    uniqueLicenseStatuses = [],
    uniqueAgencyTypes = [],
    uniqueCounties = [],
    selectedAgencyText,
    totalAgencies,
    totalReports
}) {
    const baseUrl = getBaseUrl();

    return (
        <div className="search-filter" style={{ marginBottom: '20px' }}>
            <h3 style={{ marginBottom: '12px', color: '#2c3e50', fontSize: '1.1em' }}>Filters</h3>
            <div style={{ display: 'grid', gap: '15px' }}>
                {/* Agency Filter */}
                <div>
                    <label style={{ display: 'block', marginBottom: '8px', fontWeight: 600, color: '#2c3e50' }}>
                        🏢 Filter by Agency
                    </label>
                    {!filters.agency ? (
                        <AutocompleteInput
                            id="agencyFilterInput"
                            placeholder="Type to search agencies..."
                            onSearch={onAgencySearch}
                            onSelect={onAgencySelect}
                            renderSuggestion={(s) => (
                                <>
                                    <span>{s.keyword}</span>
                                </>
                            )}
                        />
                    ) : null}
                    <div style={{ marginTop: '10px', display: 'flex', flexWrap: 'wrap', gap: '6px', minHeight: '28px' }}>
                        {filters.agency ? (
                            <KeywordBadge
                                keyword={selectedAgencyText || filters.agency}
                                onRemove={onAgencyRemove}
                            />
                        ) : (
                            <div style={{ color: '#666', fontSize: '0.9em', fontStyle: 'italic' }}>
                                No agency selected
                            </div>
                        )}
                    </div>
                </div>

                {/* SIR Only Filter */}
                <div style={{ borderTop: '1px solid #ddd', paddingTop: '15px' }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                        <input
                            type="checkbox"
                            checked={filters.sirOnly}
                            onChange={(e) => onFilterChange('sirOnly', e.target.checked)}
                            style={{ cursor: 'pointer' }}
                        />
                        <span>Special Investigation Reports Only</span>
                    </label>
                </div>

                {/* Active License Only Filter */}
                <div style={{ borderTop: '1px solid #ddd', paddingTop: '15px' }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                        <input
                            type="checkbox"
                            checked={filters.activeLicenseOnly}
                            onChange={(e) => onFilterChange('activeLicenseOnly', e.target.checked)}
                            style={{ cursor: 'pointer' }}
                        />
                        <span>Active License Only</span>
                    </label>
                    <p style={{ color: '#666', fontSize: '0.8em', marginTop: '4px', marginLeft: '24px' }}>
                        Limits results to agencies with Regular, Original, Provisional, or Inspected license status
                    </p>
                </div>

                {/* Facility Attribute Filters */}
                <div style={{ borderTop: '1px solid #ddd', paddingTop: '15px' }}>
                    <label style={{ display: 'block', marginBottom: '8px', fontWeight: 600, color: '#2c3e50' }}>
                        🏢 Filter by Facility Attributes
                    </label>
                    <div style={{ display: 'grid', gap: '10px' }}>
                        <div>
                            <label htmlFor="filterLicenseStatus" style={{ display: 'block', marginBottom: '4px', fontSize: '0.9em', color: '#666' }}>
                                License Status:
                            </label>
                            <select
                                id="filterLicenseStatus"
                                value={filters.licenseStatus || ''}
                                onChange={(e) => onFilterChange('licenseStatus', e.target.value || null)}
                                style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px', fontSize: '14px' }}
                            >
                                <option value="">All Statuses</option>
                                {uniqueLicenseStatuses.map(status => (
                                    <option key={status} value={status}>{status}</option>
                                ))}
                            </select>
                        </div>
                        <div>
                            <label htmlFor="filterAgencyType" style={{ display: 'block', marginBottom: '4px', fontSize: '0.9em', color: '#666' }}>
                                Agency Type:
                            </label>
                            <select
                                id="filterAgencyType"
                                value={filters.agencyType || ''}
                                onChange={(e) => onFilterChange('agencyType', e.target.value || null)}
                                style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px', fontSize: '14px' }}
                            >
                                <option value="">All Types</option>
                                {uniqueAgencyTypes.map(type => (
                                    <option key={type} value={type}>{type}</option>
                                ))}
                            </select>
                        </div>
                        <div>
                            <label htmlFor="filterCounty" style={{ display: 'block', marginBottom: '4px', fontSize: '0.9em', color: '#666' }}>
                                County:
                            </label>
                            <select
                                id="filterCounty"
                                value={filters.county || ''}
                                onChange={(e) => onFilterChange('county', e.target.value || null)}
                                style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px', fontSize: '14px' }}
                            >
                                <option value="">All Counties</option>
                                {uniqueCounties.map(county => (
                                    <option key={county} value={county}>{county}</option>
                                ))}
                            </select>
                        </div>
                    </div>
                    <div style={{ marginTop: '10px', textAlign: 'center' }}>
                        <a href={`${baseUrl}facilities.html`} style={{ color: '#3498db', textDecoration: 'none', fontSize: '0.9em' }}>
                            📊 View Facility Statistics
                        </a>
                    </div>
                </div>

                {/* Keyword Filter */}
                <div style={{ borderTop: '1px solid #ddd', paddingTop: '15px' }}>
                    <label style={{ display: 'block', marginBottom: '8px', fontWeight: 600, color: '#2c3e50' }}>
                        🏷️ Filter by Keywords (OR)
                    </label>
                    <p style={{ color: '#666', fontSize: '0.85em', marginBottom: '8px', fontStyle: 'italic' }}>
                        Select multiple keywords to show documents matching ANY keyword
                    </p>
                    <AutocompleteInput
                        id="keywordFilterInput"
                        placeholder="Type to search and add keywords..."
                        onSearch={onKeywordSearch}
                        onSelect={onKeywordSelect}
                        renderSuggestion={(s) => (
                            <>
                                <span>{s.keyword}</span>
                                <span style={{ color: '#666', fontSize: '0.85em' }}>({s.count})</span>
                            </>
                        )}
                    />
                    <div style={{ marginTop: '10px', minHeight: '28px' }}>
                        {filters.keywords.length > 0 ? (
                            <>
                                {filters.keywords.length > 1 && (
                                    <div style={{ color: '#e67e22', fontWeight: 600, fontSize: '0.85em', marginBottom: '6px' }}>
                                        🔍 Showing documents matching ANY of these keywords (OR):
                                    </div>
                                )}
                                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', alignItems: 'center' }}>
                                    {filters.keywords.map(kw => (
                                        <KeywordBadge
                                            key={kw}
                                            keyword={kw}
                                            onRemove={onKeywordRemove}
                                        />
                                    ))}
                                    {filters.keywords.length > 1 && (
                                        <button
                                            onClick={onClearAllKeywords}
                                            style={{
                                                background: '#e74c3c',
                                                color: 'white',
                                                border: 'none',
                                                padding: '6px 12px',
                                                borderRadius: '16px',
                                                fontSize: '0.85em',
                                                cursor: 'pointer',
                                                marginLeft: '6px'
                                            }}
                                        >
                                            Clear All
                                        </button>
                                    )}
                                </div>
                            </>
                        ) : (
                            <div style={{ color: '#666', fontSize: '0.9em', fontStyle: 'italic' }}>
                                No keywords selected
                            </div>
                        )}
                    </div>
                    <div style={{
                        marginTop: '10px',
                        padding: '10px',
                        background: '#fff3cd',
                        borderLeft: '3px solid #ffc107',
                        borderRadius: '4px',
                        fontSize: '0.85em'
                    }}>
                        <strong>Note:</strong> Keywords were generated by Deepseek V3.2 and may be inconsistent and/or erroneous.
                        See the <a href={`${baseUrl}keywords.html`} style={{ color: '#856404', textDecoration: 'underline' }}>keywords page</a> for more information about limitations.
                    </div>
                    <div style={{ marginTop: '10px', textAlign: 'center' }}>
                        <a href={`${baseUrl}keywords.html`} style={{ color: '#3498db', textDecoration: 'none', fontSize: '0.9em' }}>
                            📊 View All Keywords
                        </a>
                    </div>
                </div>

                {/* Stats Count */}
                <div style={{ borderTop: '1px solid #ddd', paddingTop: '15px', textAlign: 'center', color: '#666', fontSize: '0.9em' }}>
                    Showing {totalAgencies} {totalAgencies === 1 ? 'agency' : 'agencies'} with {totalReports} {totalReports === 1 ? 'document' : 'documents'}
                </div>
            </div>
        </div>
    );
}

export default FilterPanel;
