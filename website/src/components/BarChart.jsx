import React from 'react';

/**
 * Bar chart component for displaying data with horizontal bars
 * @param {Object} props
 * @param {string} props.title - Chart title
 * @param {Array} props.data - Array of {label, count, linkUrl} objects
 * @param {number} [props.maxCount] - Optional max count for scaling (auto-calculated if not provided)
 */
export function BarChart({ title, data, maxCount: propMaxCount }) {
    if (!data || data.length === 0) {
        return (
            <div className="bar-chart" style={{ display: 'block' }}>
                <div className="bar-chart-title">{title}</div>
                <div style={{ color: '#666', fontSize: '0.9em', fontStyle: 'italic', padding: '20px', textAlign: 'center' }}>
                    No data available
                </div>
            </div>
        );
    }

    const maxCount = propMaxCount || Math.max(...data.map(item => item.count));

    return (
        <div className="bar-chart" style={{ display: 'block' }}>
            <div className="bar-chart-title">{title}</div>
            <div className="bar-chart-container">
                {data.map((item, index) => {
                    const percentage = maxCount > 0 ? (item.count / maxCount) * 100 : 0;
                    return (
                        <div className="bar-chart-row" key={item.label || index}>
                            {item.linkUrl ? (
                                <a 
                                    href={item.linkUrl} 
                                    className="bar-chart-label" 
                                    title={item.tooltip || `View: ${item.label}`}
                                >
                                    {item.label}
                                </a>
                            ) : (
                                <span className="bar-chart-label">{item.label}</span>
                            )}
                            <div className="bar-chart-bar-container">
                                <div 
                                    className="bar-chart-bar" 
                                    style={{ width: `${percentage}%` }}
                                />
                            </div>
                            <div className="bar-chart-count">{item.count}</div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}

export default BarChart;
