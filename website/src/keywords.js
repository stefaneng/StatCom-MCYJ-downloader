// Keywords page - displays all keywords with counts
import { Trie } from './trie.js';

let keywordTrie = new Trie();

// Load and display data
async function init() {
    try {
        // Fetch the agency data
        const response = await fetch('/data/agencies_data.json');
        if (!response.ok) {
            throw new Error(`Failed to load data: ${response.statusText}`);
        }
        
        const allAgencies = await response.json();
        
        // Build keyword trie from all documents
        buildKeywordTrie(allAgencies);
        
        // Render the complete keyword bar chart
        renderKeywordBarChart();
        
        hideLoading();
        
    } catch (error) {
        console.error('Error loading data:', error);
        showError(`Failed to load data: ${error.message}`);
        hideLoading();
    }
}

function buildKeywordTrie(allAgencies) {
    allAgencies.forEach(agency => {
        if (agency.documents && Array.isArray(agency.documents)) {
            agency.documents.forEach(doc => {
                if (doc.sir_violation_level && doc.sir_violation_level.keywords && Array.isArray(doc.sir_violation_level.keywords)) {
                    doc.sir_violation_level.keywords.forEach(keyword => {
                        keywordTrie.insert(keyword, true, keyword);
                        
                        const words = keyword.trim().split(/\s+/);
                        words.forEach(word => {
                            if (word.length > 0) {
                                keywordTrie.insert(word, false, keyword);
                            }
                        });
                    });
                }
            });
        }
    });
}

function renderKeywordBarChart() {
    const container = document.getElementById('barChartContainer');
    const chartDiv = document.getElementById('keywordBarChart');
    
    if (!container || !chartDiv) return;
    
    // Get all keywords sorted by count
    const allKeywords = keywordTrie.getAllKeywords();
    
    if (allKeywords.length === 0) {
        container.innerHTML = '<div style="color: #666; font-size: 0.9em; font-style: italic; padding: 20px; text-align: center;">No keyword data available</div>';
        chartDiv.style.display = 'block';
        return;
    }
    
    // Find max count for scaling
    const maxCount = Math.max(...allKeywords.map(k => k.count));
    
    // Build bar chart HTML for all keywords
    const barsHtml = allKeywords.map(item => {
        const percentage = maxCount > 0 ? (item.count / maxCount) * 100 : 0;
        const encodedKeyword = encodeURIComponent(item.keyword);
        return `
            <div class="bar-chart-row">
                <a href="/?keyword=${encodedKeyword}" class="bar-chart-label" title="View documents with keyword: ${escapeHtml(item.keyword)}">${escapeHtml(item.keyword)}</a>
                <div class="bar-chart-bar-container">
                    <div class="bar-chart-bar" style="width: ${percentage}%"></div>
                </div>
                <div class="bar-chart-count">${item.count}</div>
            </div>
        `;
    }).join('');
    
    container.innerHTML = barsHtml;
    chartDiv.style.display = 'block';
}

function hideLoading() {
    document.getElementById('loading').style.display = 'none';
}

function showError(message) {
    const loadingEl = document.getElementById('loading');
    loadingEl.textContent = `Error: ${message}`;
    loadingEl.style.color = '#e74c3c';
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize the page
init();
