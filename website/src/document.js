// Document viewer page logic

let currentDocumentData = null;

// Load and display document
async function init() {
    const urlParams = new URLSearchParams(window.location.search);
    const sha = urlParams.get('sha');
    
    if (sha) {
        // Load document from query string
        await loadDocument(sha);
    } else {
        // Show search box
        showSearchBox();
    }
    
    setCommitHash();
}

function showSearchBox() {
    document.getElementById('searchContainer').style.display = 'block';
}

function hideSearchBox() {
    document.getElementById('searchContainer').style.display = 'none';
}

function showLoading() {
    document.getElementById('loading').style.display = 'block';
}

function hideLoading() {
    document.getElementById('loading').style.display = 'none';
}

function showError(message) {
    const errorEl = document.getElementById('error');
    errorEl.textContent = message;
    errorEl.style.display = 'block';
}

function hideError() {
    document.getElementById('error').style.display = 'none';
}

async function loadDocument(sha256) {
    hideSearchBox();
    showLoading();
    hideError();
    
    try {
        // Fetch document data
        const response = await fetch(`/documents/${sha256}.json`);
        if (!response.ok) {
            throw new Error(`Failed to load document: ${response.statusText}`);
        }
        
        const docData = await response.json();
        currentDocumentData = docData;
        
        // Try to fetch metadata from agencies data
        let docMetadata = null;
        try {
            const agenciesResponse = await fetch('/data/agencies_data.json');
            if (agenciesResponse.ok) {
                const agencies = await agenciesResponse.json();
                
                // Find document metadata
                for (const agency of agencies) {
                    if (agency.documents && Array.isArray(agency.documents)) {
                        const document = agency.documents.find(d => d.sha256 === sha256);
                        if (document) {
                            docMetadata = {
                                title: document.document_title || document.agency_name || 'Untitled Document',
                                is_special_investigation: document.is_special_investigation || false,
                                agencyName: agency.AgencyName,
                                agencyId: agency.agencyId
                            };
                            break;
                        }
                    }
                }
            }
        } catch (error) {
            console.warn('Could not load agency metadata:', error);
        }
        
        // Display document
        displayDocument(docData, docMetadata);
        hideLoading();
        
    } catch (error) {
        console.error('Error loading document:', error);
        hideLoading();
        showError(`Failed to load document: ${error.message}`);
        showSearchBox();
    }
}

function displayDocument(docData, docMetadata) {
    const container = document.getElementById('documentContainer');
    
    // Validate document data
    if (!docData.pages || !Array.isArray(docData.pages)) {
        showError('Invalid document data: pages array missing or invalid');
        return;
    }
    
    // Format the document pages
    const totalPages = docData.pages.length;
    const pagesHtml = docData.pages.map((page, pageIndex) => {
        const pageContent = escapeHtml(page);
        
        return `
            <div class="document-page">
                <div class="page-number">Page ${pageIndex + 1} of ${totalPages}</div>
                <pre class="page-text">${pageContent}</pre>
            </div>
        `;
    }).join('');
    
    // Build SIR summary section if available
    let sirSummaryHtml = '';
    if (docData.sir_summary && docData.sir_summary.summary) {
        // Determine violation level badge
        let violationLevelBadge = '';
        if (docData.sir_violation_level && docData.sir_violation_level.level) {
            const level = docData.sir_violation_level.level.toLowerCase();
            let levelColor = '#95a5a6';
            let levelEmoji = '⚪';
            
            if (level === 'low') {
                levelColor = '#f39c12';
                levelEmoji = '🟡';
            } else if (level === 'moderate') {
                levelColor = '#e67e22';
                levelEmoji = '🟠';
            } else if (level === 'severe') {
                levelColor = '#e74c3c';
                levelEmoji = '🔴';
            }
            
            violationLevelBadge = `<span style="color: ${levelColor}; margin-left: 8px; font-size: 0.9em;">${levelEmoji} ${level.charAt(0).toUpperCase() + level.slice(1)} Severity</span>`;
        }
        
        sirSummaryHtml = `
            <div class="sir-summary">
                <h3>
                    📋 Special Investigation Report Summary (AI-generated)
                    ${docData.sir_summary.violation === 'y' ? `<span class="violation-badge violation-yes">⚠️ Violation Substantiated</span>` : ''}
                    ${docData.sir_summary.violation === 'n' ? '<span class="violation-badge violation-no">✓ No Violation</span>' : ''}
                    ${violationLevelBadge}
                </h3>
                <div style="margin-bottom: ${docData.sir_violation_level && (docData.sir_violation_level.justification || (docData.sir_violation_level.keywords && docData.sir_violation_level.keywords.length > 0)) ? '15px' : '0'};">
                    <strong style="color: #2c3e50;">Summary:</strong>
                    <div style="margin-top: 8px;">${escapeHtml(docData.sir_summary.summary)}</div>
                </div>
                ${docData.sir_violation_level && docData.sir_violation_level.keywords && docData.sir_violation_level.keywords.length > 0 ? `
                    <div style="padding-top: 15px; border-top: 1px solid #ecf0f1; margin-bottom: ${docData.sir_violation_level.justification ? '15px' : '0'};">
                        <strong style="color: #2c3e50;">Keywords:</strong>
                        <div style="margin-top: 8px; display: flex; flex-wrap: wrap; gap: 6px;">
                            ${docData.sir_violation_level.keywords.map(kw => 
                                `<span style="background: #e8f4f8; color: #2980b9; padding: 4px 10px; border-radius: 12px; font-size: 0.85em; border: 1px solid #3498db;">${escapeHtml(kw)}</span>`
                            ).join('')}
                        </div>
                    </div>
                ` : ''}
                ${docData.sir_violation_level && docData.sir_violation_level.justification ? `
                    <div style="padding-top: 15px; border-top: 1px solid #ecf0f1;">
                        <strong style="color: #2c3e50;">Severity Justification:</strong>
                        <div style="margin-top: 8px;">${escapeHtml(docData.sir_violation_level.justification)}</div>
                    </div>
                ` : ''}
            </div>
        `;
    }
    
    container.innerHTML = `
        <div class="document-header">
            <h2>Document Details</h2>
        </div>
        
        <div class="document-info">
            ${docMetadata ? `
                <div><strong>Title:</strong> ${escapeHtml(docMetadata.title)}</div>
                ${docMetadata.agencyName ? `<div><strong>Agency:</strong> ${escapeHtml(docMetadata.agencyName)} (ID: ${escapeHtml(docMetadata.agencyId)})</div>` : ''}
                ${docMetadata.is_special_investigation ? `
                    <div style="color: #e74c3c;"><strong>Type:</strong> 🔍 Special Investigation Report</div>
                ` : ''}
            ` : ''}
            <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-top: 10px;">
                <button class="copy-link-btn" onclick="copyDocumentLink(event)" title="Copy link to this document">
                    🔗 Copy URL to this document
                </button>
                <button class="copy-link-btn" onclick="copyDocumentText(event)" title="Copy full document text to clipboard for use with your own AI chatbot">
                    📋 Copy Document Text
                </button>
                ${docMetadata && docMetadata.agencyId ? `
                    <a href="/?agency=${encodeURIComponent(docMetadata.agencyId)}" class="copy-link-btn" style="text-decoration: none;">
                        🏢 View Agency
                    </a>
                ` : ''}
            </div>
            <div><strong>Document ID (SHA-256):</strong> <code style="word-break: break-all;">${escapeHtml(docData.sha256)}</code></div>
            <div><strong>Date Processed:</strong> ${escapeHtml(docData.dateprocessed)}</div>
            <div><strong>Total Pages:</strong> ${totalPages}</div>
        </div>
        
        ${sirSummaryHtml}
        
        <div class="document-pages">
            ${pagesHtml}
        </div>
    `;
    
    container.style.display = 'block';
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function copyDocumentLink(event) {
    const url = window.location.href;
    const btn = event?.target;
    
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(url).then(() => {
            if (btn) {
                const originalText = btn.textContent;
                btn.textContent = '✓ Copied!';
                setTimeout(() => {
                    btn.textContent = originalText;
                }, 1500);
            }
        }).catch(err => {
            console.error('Failed to copy link:', err);
            if (btn) {
                const originalText = btn.textContent;
                btn.textContent = '✗ Failed';
                setTimeout(() => {
                    btn.textContent = originalText;
                }, 1500);
            }
        });
    } else {
        // Fallback
        const textarea = document.createElement('textarea');
        textarea.value = url;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        try {
            document.execCommand('copy');
            if (btn) {
                const originalText = btn.textContent;
                btn.textContent = '✓ Copied!';
                setTimeout(() => {
                    btn.textContent = originalText;
                }, 1500);
            }
        } catch (err) {
            console.error('Failed to copy link:', err);
            if (btn) {
                const originalText = btn.textContent;
                btn.textContent = '✗ Failed';
                setTimeout(() => {
                    btn.textContent = originalText;
                }, 1500);
            }
        } finally {
            document.body.removeChild(textarea);
        }
    }
}

function copyDocumentText(event) {
    if (!currentDocumentData || !currentDocumentData.pages) {
        console.error('Document not loaded');
        return;
    }
    
    const btn = event?.target;
    
    // Concatenate all pages with double newlines between them
    const fullText = currentDocumentData.pages.join('\n\n');
    
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(fullText).then(() => {
            if (btn) {
                const originalText = btn.textContent;
                btn.textContent = '✓ Copied!';
                setTimeout(() => {
                    btn.textContent = originalText;
                }, 2000);
            }
        }).catch(err => {
            console.error('Failed to copy document text:', err);
            if (btn) {
                const originalText = btn.textContent;
                btn.textContent = '✗ Failed';
                setTimeout(() => {
                    btn.textContent = originalText;
                }, 1500);
            }
        });
    } else {
        // Fallback
        const textarea = document.createElement('textarea');
        textarea.value = fullText;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        try {
            document.execCommand('copy');
            if (btn) {
                const originalText = btn.textContent;
                btn.textContent = '✓ Copied!';
                setTimeout(() => {
                    btn.textContent = originalText;
                }, 2000);
            }
        } catch (err) {
            console.error('Failed to copy document text:', err);
            if (btn) {
                const originalText = btn.textContent;
                btn.textContent = '✗ Failed';
                setTimeout(() => {
                    btn.textContent = originalText;
                }, 1500);
            }
        } finally {
            document.body.removeChild(textarea);
        }
    }
}

function loadDocumentFromSearch() {
    const shaInput = document.getElementById('shaInput');
    const sha = shaInput.value.trim();
    
    if (!sha) {
        alert('Please enter a document SHA-256 hash');
        return;
    }
    
    // Validate SHA format (64 hex characters)
    if (!/^[a-fA-F0-9]{64}$/.test(sha)) {
        alert('Invalid SHA-256 format. Please enter a 64-character hexadecimal hash.');
        return;
    }
    
    // Update URL and load document
    const url = new URL(window.location);
    url.searchParams.set('sha', sha);
    window.history.pushState({}, '', url);
    
    loadDocument(sha);
}

function setCommitHash() {
    const commitHashEl = document.getElementById('commitHash');
    if (commitHashEl) {
        const commitHash = '__COMMIT_HASH__';
        commitHashEl.textContent = `Version: ${commitHash}`;
    }
}

// Make functions available globally
window.copyDocumentLink = copyDocumentLink;
window.copyDocumentText = copyDocumentText;
window.loadDocumentFromSearch = loadDocumentFromSearch;

// Initialize the page
init();
