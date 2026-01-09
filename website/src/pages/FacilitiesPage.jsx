import React, { useState, useEffect } from 'react';
import { Header, BarChart, Loading, Error } from '../components/index.js';
import { getBaseUrl, ACTIVE_LICENSE_STATUSES } from '../utils/helpers.js';

const BASE_URL = getBaseUrl();

/**
 * FacilitiesPage component for displaying facility statistics
 */
export function FacilitiesPage() {
    const [allFacilities, setAllFacilities] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [currentGrouping, setCurrentGrouping] = useState('LicenseStatus');

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const response = await fetch(`${BASE_URL}data/facilities_data.json`);
            if (!response.ok) {
                throw new Error(`Failed to load data: ${response.statusText}`);
            }
            
            let data = await response.json();
            
            // Filter to only active facilities
            data = data.filter(f => ACTIVE_LICENSE_STATUSES.includes(f.LicenseStatus));
            
            setAllFacilities(data);
            setLoading(false);
        } catch (err) {
            console.error('Error loading data:', err);
            setError(`Failed to load data: ${err.message}`);
            setLoading(false);
        }
    };

    const groupFacilities = (groupBy) => {
        const groups = {};
        
        allFacilities.forEach(facility => {
            const key = facility[groupBy] || 'Unknown';
            if (!groups[key]) {
                groups[key] = [];
            }
            groups[key].push(facility);
        });
        
        return Object.entries(groups)
            .map(([key, facilities]) => ({ 
                label: key, 
                count: facilities.length,
                linkUrl: `${BASE_URL}?${groupBy.toLowerCase()}=${encodeURIComponent(key)}`,
                tooltip: `View agencies with ${groupBy}: ${key}`
            }))
            .sort((a, b) => b.count - a.count);
    };

    const getChartTitle = () => {
        const titles = {
            'LicenseStatus': 'Facilities by License Status',
            'AgencyType': 'Facilities by Agency Type',
            'County': 'Facilities by County'
        };
        return titles[currentGrouping] || `Facilities by ${currentGrouping}`;
    };

    const getStatsSummary = () => {
        const totalFacilities = allFacilities.length;
        const uniqueCounties = new Set(allFacilities.map(f => f.County)).size;
        const uniqueTypes = new Set(allFacilities.map(f => f.AgencyType)).size;
        
        return (
            <>
                <strong>📊 Summary:</strong>{' '}
                {totalFacilities} active facilities across{' '}
                {uniqueCounties} counties and{' '}
                {uniqueTypes} agency types.
            </>
        );
    };

    if (loading) {
        return (
            <>
                <Header 
                    title="Facility Statistics" 
                    subtitle="Active Licensed Facilities by Grouping" 
                />
                <div className="container">
                    <Loading message="Loading data..." />
                </div>
            </>
        );
    }

    if (error) {
        return (
            <>
                <Header 
                    title="Facility Statistics" 
                    subtitle="Active Licensed Facilities by Grouping" 
                />
                <div className="container">
                    <Error message={error} />
                </div>
            </>
        );
    }

    const chartData = groupFacilities(currentGrouping);

    return (
        <>
            <Header 
                title="Facility Statistics" 
                subtitle="Active Licensed Facilities by Grouping" 
            />
            <div className="container">
                <a href={`${BASE_URL}`} className="back-link">← Back to Dashboard</a>
                
                <div className="facilities-container">
                    <div className="facilities-header">
                        <h2>🏢 Facility Counts by Grouping</h2>
                        <p className="facilities-description">
                            This page shows counts of facilities with active licenses, grouped by various attributes.
                            Click on any group to view the corresponding agencies in the main dashboard.
                        </p>
                    </div>
                    
                    <div className="grouping-selector">
                        <label htmlFor="groupingSelect">Group by:</label>
                        <select 
                            id="groupingSelect"
                            value={currentGrouping}
                            onChange={(e) => setCurrentGrouping(e.target.value)}
                        >
                            <option value="LicenseStatus">License Status</option>
                            <option value="AgencyType">Agency Type</option>
                            <option value="County">County</option>
                        </select>
                    </div>
                    
                    <div className="stats-summary">
                        {getStatsSummary()}
                    </div>
                    
                    <BarChart 
                        title={getChartTitle()}
                        data={chartData}
                    />
                </div>
            </div>
        </>
    );
}

export default FacilitiesPage;
