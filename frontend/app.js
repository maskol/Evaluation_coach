// Evaluation Coach - Frontend JavaScript
// API Configuration
const API_BASE_URL = 'http://localhost:8850/api';

// State Management
const appState = {
    scope: 'portfolio',
    selectedART: '',
    selectedTeam: '',
    selectedPIs: [],  // Array of selected PIs
    selectedARTs: [],  // Array of selected ARTs for filtering
    allARTs: [],  // Full list of all ARTs (unfiltered) for admin panel
    metricFocus: 'flow',
    activeTab: 'dashboard',
    messages: [],
    sessionId: generateSessionId(),
    currentInsights: [],  // Store current insights for actions
    isLoading: false,  // Track loading state
    insightsAbortController: null,  // Track ongoing insights request
    piReportAbortController: null   // Track ongoing PI report request
};

function getSavedDefaultFilters() {
    const savedDefaults = localStorage.getItem('defaultFilters');
    if (!savedDefaults) return { pis: [], arts: [] };
    try {
        const parsed = JSON.parse(savedDefaults);
        return {
            pis: Array.isArray(parsed.pis) ? parsed.pis : [],
            arts: Array.isArray(parsed.arts) ? parsed.arts : []
        };
    } catch (e) {
        console.warn('⚠️ Failed to parse saved default filters');
        return { pis: [], arts: [] };
    }
}

// Default Filters (loaded from localStorage)
function loadDefaultFilters() {
    const defaults = getSavedDefaultFilters();
    appState.selectedPIs = defaults.pis;
    appState.selectedARTs = defaults.arts;
    console.log('📋 Loaded default filters:', defaults);
}

function saveDefaultFilters() {
    const defaultPICheckboxes = document.querySelectorAll('#defaultPISelector .default-pi-checkbox:checked');
    const defaultARTCheckboxes = document.querySelectorAll('#defaultARTSelector .default-art-checkbox:checked');

    const defaults = {
        pis: Array.from(defaultPICheckboxes).map(cb => cb.value),
        arts: Array.from(defaultARTCheckboxes).map(cb => cb.value)
    };

    localStorage.setItem('defaultFilters', JSON.stringify(defaults));

    // Apply to current state
    appState.selectedPIs = defaults.pis;
    appState.selectedARTs = defaults.arts;

    // Update dashboard with new defaults
    loadDashboardData();
    updatePIDisplay();

    alert(`✅ Default filters saved!\n\nPIs: ${defaults.pis.length > 0 ? defaults.pis.join(', ') : 'All'}\nARTs: ${defaults.arts.length > 0 ? defaults.arts.join(', ') : 'All'}`);
}

function clearDefaultFilters() {
    localStorage.removeItem('defaultFilters');
    appState.selectedPIs = [];
    appState.selectedARTs = [];

    // Uncheck all checkboxes in admin panel
    document.querySelectorAll('#defaultPISelector input[type="checkbox"]').forEach(cb => cb.checked = false);
    document.querySelectorAll('#defaultARTSelector input[type="checkbox"]').forEach(cb => cb.checked = false);

    // Update dashboard to show all data
    loadDashboardData();
    updatePIDisplay();

    alert('✅ Default filters cleared! Dashboard will show all PIs and ARTs.');
}

// LLM Configuration Functions
function loadLLMConfig() {
    const savedConfig = localStorage.getItem('llmConfig');
    if (savedConfig) {
        try {
            const config = JSON.parse(savedConfig);
            document.getElementById('llmModelSelect').value = config.model || 'gpt-4o-mini';
            document.getElementById('llmTemperature').value = config.temperature || 0.7;
            document.getElementById('tempValue').textContent = config.temperature || 0.7;
            updateLLMStatus();
            console.log('📋 Loaded LLM config:', config);
        } catch (e) {
            console.warn('⚠️ Failed to parse saved LLM config');
        }
    }
}

function saveLLMConfig() {
    const model = document.getElementById('llmModelSelect').value;
    const temperature = parseFloat(document.getElementById('llmTemperature').value);

    const config = { model, temperature };
    localStorage.setItem('llmConfig', JSON.stringify(config));

    // Also send to backend
    fetch(`${API_BASE_URL}/v1/config/llm`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
    })
        .then(response => response.json())
        .then(data => {
            updateLLMStatus();
            alert(`✅ LLM Configuration saved!\n\nModel: ${model}\nTemperature: ${temperature}\n\nThis will be used for the next insight generation.`);
        })
        .catch(error => {
            console.error('Error saving LLM config:', error);
            updateLLMStatus();
            alert(`✅ LLM Configuration saved locally!\n\nModel: ${model}\nTemperature: ${temperature}\n\nNote: Backend connection failed, but config is saved for next session.`);
        });
}

function updateLLMStatus() {
    const model = document.getElementById('llmModelSelect').value;
    const temperature = document.getElementById('llmTemperature').value;
    document.getElementById('llmStatus').textContent = `Model: ${model} | Temp: ${temperature}`;
}

function getLLMConfig() {
    const savedConfig = localStorage.getItem('llmConfig');
    if (savedConfig) {
        try {
            return JSON.parse(savedConfig);
        } catch (e) {
            return { model: 'gpt-4o-mini', temperature: 0.7 };
        }
    }
    return { model: 'gpt-4o-mini', temperature: 0.7 };
}

// Strategic Targets Functions
async function loadStrategicTargets() {
    try {
        const response = await fetch(`${API_BASE_URL}/admin/config`);
        const data = await response.json();
        const thresholds = data.thresholds || {};

        // Load Lead-Time targets
        if (thresholds.leadtime_target_2026) {
            document.getElementById('leadtime2026Target').value = thresholds.leadtime_target_2026;
        }
        if (thresholds.leadtime_target_2027) {
            document.getElementById('leadtime2027Target').value = thresholds.leadtime_target_2027;
        }
        if (thresholds.leadtime_target_true_north) {
            document.getElementById('leadtimeTrueNorthTarget').value = thresholds.leadtime_target_true_north;
        }

        // Load Planning Accuracy targets
        if (thresholds.planning_accuracy_target_2026) {
            document.getElementById('planningAccuracy2026Target').value = thresholds.planning_accuracy_target_2026;
        }
        if (thresholds.planning_accuracy_target_2027) {
            document.getElementById('planningAccuracy2027Target').value = thresholds.planning_accuracy_target_2027;
        }
        if (thresholds.planning_accuracy_target_true_north) {
            document.getElementById('planningAccuracyTrueNorthTarget').value = thresholds.planning_accuracy_target_true_north;
        }

        console.log('✅ Strategic targets loaded');
    } catch (error) {
        console.error('Error loading strategic targets:', error);
    }
}

async function saveStrategicTargets() {
    try {
        const targets = {
            leadtime_target_2026: parseFloat(document.getElementById('leadtime2026Target').value) || null,
            leadtime_target_2027: parseFloat(document.getElementById('leadtime2027Target').value) || null,
            leadtime_target_true_north: parseFloat(document.getElementById('leadtimeTrueNorthTarget').value) || null,
            planning_accuracy_target_2026: parseFloat(document.getElementById('planningAccuracy2026Target').value) || null,
            planning_accuracy_target_2027: parseFloat(document.getElementById('planningAccuracy2027Target').value) || null,
            planning_accuracy_target_true_north: parseFloat(document.getElementById('planningAccuracyTrueNorthTarget').value) || null,
            bottleneck_threshold_days: 7.0,  // Keep existing default
            planning_accuracy_threshold_pct: 70.0  // Keep existing default
        };

        const response = await fetch(`${API_BASE_URL}/admin/config/thresholds`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(targets)
        });

        const result = await response.json();
        alert('✅ Strategic Targets Saved!\n\nThese targets will be used by AI Insights for analysis.');
        console.log('Strategic targets saved:', result);
    } catch (error) {
        console.error('Error saving strategic targets:', error);
        alert('❌ Error saving targets. Please try again.');
    }
}

// Loading Banner Functions (Non-blocking)
function showLoadingOverlay(message = 'Loading...') {
    let banner = document.getElementById('loadingBanner');
    if (!banner) {
        banner = document.createElement('div');
        banner.id = 'loadingBanner';
        banner.style.cssText = `
            position: fixed;
            top: 60px;
            left: 0;
            right: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
            animation: slideDown 0.3s ease-out;
        `;

        banner.innerHTML = `
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="
                    width: 18px;
                    height: 18px;
                    border: 3px solid rgba(255, 255, 255, 0.3);
                    border-top: 3px solid white;
                    border-radius: 50%;
                    animation: spin 0.8s linear infinite;
                "></div>
                <div id="loadingMessage" style="
                    font-size: 14px;
                    font-weight: 600;
                ">${message}</div>
            </div>
            <style>
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
                @keyframes slideDown {
                    from { transform: translateY(-100%); opacity: 0; }
                    to { transform: translateY(0); opacity: 1; }
                }
            </style>
        `;
        document.body.appendChild(banner);
    } else {
        banner.style.display = 'flex';
        const messageEl = document.getElementById('loadingMessage');
        if (messageEl) messageEl.textContent = message;
    }
}

function hideLoadingOverlay() {
    const banner = document.getElementById('loadingBanner');
    if (banner) {
        banner.style.animation = 'slideUp 0.3s ease-out';
        setTimeout(() => {
            banner.style.display = 'none';
        }, 300);
    }
}

function updateLoadingMessage(message) {
    const messageEl = document.getElementById('loadingMessage');
    if (messageEl) messageEl.textContent = message;
}

// Generate unique session ID
function generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

// Initialize app on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('🎯 Evaluation Coach initialized');
    loadDefaultFilters();  // Load saved defaults
    loadLLMConfig();  // Load saved LLM configuration
    checkBackendHealth();
    loadARTsAndTeams();
    loadDashboardData();
    updateStatusBar('Application ready');
    updateContext();
});

// Check backend API health
async function checkBackendHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        if (response.ok) {
            const health = await response.json();
            console.log('✅ Backend connected:', health);
            updateStatusBar(`Connected to API | ${health.total_issues} issues | ${health.total_insights} insights`);
        }
    } catch (error) {
        console.warn('⚠️ Backend not available, using demo mode');
        updateStatusBar('Demo mode - Backend not connected');
    }
}

// Load ARTs and Teams from API
async function loadARTsAndTeams() {
    try {
        // Load ARTs
        const artsResponse = await fetch(`${API_BASE_URL}/arts`);
        if (artsResponse.ok) {
            const artsData = await artsResponse.json();
            const artSelector = document.getElementById('artSelector');
            if (artSelector && artsData.arts) {
                // Clear existing options except the first one
                artSelector.innerHTML = '<option value="">-- Select ART --</option>';

                // Add real ARTs
                artsData.arts.forEach(art => {
                    const option = document.createElement('option');
                    option.value = art;
                    option.textContent = art;
                    artSelector.appendChild(option);
                });
                console.log(`✅ Loaded ${artsData.count} ARTs`);

                // Store full list of ARTs for admin panel (unfiltered)
                appState.allARTs = artsData.arts;
            }
        }

        // Load Teams
        const teamsResponse = await fetch(`${API_BASE_URL}/teams`);
        if (teamsResponse.ok) {
            const teamsData = await teamsResponse.json();
            const teamSelector = document.getElementById('teamSelector');
            if (teamSelector && teamsData.teams) {
                // Clear existing options except the first one
                teamSelector.innerHTML = '<option value="">-- Select Team --</option>';

                // Add real teams
                teamsData.teams.forEach(team => {
                    const option = document.createElement('option');
                    option.value = team;
                    option.textContent = team;
                    teamSelector.appendChild(option);
                });
                console.log(`✅ Loaded ${teamsData.count} teams`);
            }
        }
    } catch (error) {
        console.warn('⚠️ Could not load ARTs/Teams:', error);
    }
}

// Load dashboard data from API
async function loadDashboardData() {
    try {
        // Show loading indicator
        showLoadingOverlay('Fetching dashboard data...');
        appState.isLoading = true;

        let url = `${API_BASE_URL}/v1/dashboard?scope=${appState.scope}&time_range=last_pi`;
        if (appState.selectedPIs && appState.selectedPIs.length > 0) {
            url += `&pis=${appState.selectedPIs.join(',')}`;
        }

        // Priority: scope-specific ART selection overrides default ARTs filter
        if (appState.scope === 'art' && appState.selectedART) {
            // ART View - use the selected ART from dropdown
            url += `&arts=${appState.selectedART}`;
        } else if (appState.selectedARTs && appState.selectedARTs.length > 0) {
            // Portfolio View - only apply ARTs filter if not all ARTs are selected
            // Note: Some ARTs exist in data but not in /api/analysis/filters (42 vs 28 ARTs)
            // If all available ARTs from the filter list are selected, don't send the filter
            // to ensure we capture all data including ARTs not in the filter list
            if (appState.allARTs && appState.selectedARTs.length >= appState.allARTs.length) {
                // All ARTs selected - don't filter to include ARTs not in the filter list
                console.log('📊 All ARTs selected - no ART filter applied to capture all data');
            } else {
                // Subset of ARTs selected - apply filter
                url += `&arts=${appState.selectedARTs.join(',')}`;
                console.log(`📊 Filtering to ${appState.selectedARTs.length} ARTs`);
            }
        }

        console.log('📊 Loading dashboard data from:', url);
        const response = await fetch(url);
        if (response.ok) {
            const data = await response.json();
            console.log('📊 Dashboard data loaded:', data);
            console.log('📊 ART comparison data:', data.art_comparison);
            console.log('📊 Selected PIs:', data.selected_pis || 'All PIs');
            updateDashboardUI(data);
            hideLoadingOverlay();
            appState.isLoading = false;
        } else {
            console.error('❌ Dashboard request failed:', response.status);
            hideLoadingOverlay();
            appState.isLoading = false;
        }
    } catch (error) {
        console.error('❌ Error loading dashboard:', error);
        hideLoadingOverlay();
        appState.isLoading = false;
        console.log('Using demo dashboard data');
        updateStatusBar('Demo mode - Could not load real data');
    }
}

// Update Dashboard UI with real data
function updateDashboardUI(data) {
    if (!data) return;

    // Show active filters - respect scope priority
    const activeFiltersDisplay = document.getElementById('activeFiltersDisplay');
    const activeFiltersText = document.getElementById('activeFiltersText');
    if (activeFiltersDisplay && activeFiltersText) {
        const filters = [];
        if (appState.selectedPIs && appState.selectedPIs.length > 0) {
            filters.push(`PIs: ${appState.selectedPIs.join(', ')}`);
        }

        // Priority: scope-specific ART selection overrides default ARTs filter
        if (appState.scope === 'art' && appState.selectedART) {
            // ART View - show the selected ART
            filters.push(`ART: ${appState.selectedART}`);
        } else if (appState.selectedARTs && appState.selectedARTs.length > 0) {
            // Portfolio View - show ARTs filter
            // If all ARTs are selected, show "All ARTs" instead of listing them
            if (appState.allARTs && appState.selectedARTs.length >= appState.allARTs.length) {
                filters.push(`ARTs: All (${appState.allARTs.length} from filter + others in data)`);
            } else {
                const artText = appState.selectedARTs.length <= 5
                    ? appState.selectedARTs.join(', ')
                    : `${appState.selectedARTs.slice(0, 5).join(', ')} +${appState.selectedARTs.length - 5} more`;
                filters.push(`ARTs: ${artText}`);
            }
        }

        if (filters.length > 0) {
            activeFiltersText.textContent = filters.join(' | ');
            activeFiltersDisplay.style.display = 'block';
        } else {
            activeFiltersDisplay.style.display = 'none';
        }
    }

    // Update portfolio metrics
    if (data.portfolio_metrics) {
        const metricsContainer = document.getElementById('portfolioMetrics');
        if (metricsContainer) {
            // Define tooltips for each metric
            const metricDefinitions = {
                'Flow Efficiency': 'Percentage of time spent on value-adding work vs. waiting. Measures how much time features spend actively being worked on versus sitting idle. Value-add stages: in_progress + in_reviewing. Industry average: 15%, High performers: 40%+',
                'Planning Accuracy': 'Percentage of committed features (planned_committed=1) that were actually delivered (plc_delivery=1). Measures predictability and planning effectiveness. Target: 80%+, Acceptable: 70%+',
                'Average Lead-Time': 'Average time from feature start to completion for delivered features. Measures end-to-end delivery speed. Target: ≤30 days, Max acceptable: 60 days, Lower is better',
                'Features Delivered': 'Total number of features completed and delivered in the selected time period. Sourced from leadtime_thr_data (features with throughput=1)'
            };

            metricsContainer.innerHTML = data.portfolio_metrics.map(metric => {
                const statusColorMap = {
                    'good': '#34C759',
                    'warning': '#FF9500',
                    'critical': '#FF3B30'
                };
                const statusColor = statusColorMap[metric.status] || '#667eea';

                const trendIcon = metric.trend === 'up' ? '↑' : metric.trend === 'down' ? '↓' : '→';
                const tooltip = metricDefinitions[metric.name] || '';

                return `
                    <div style="background: linear-gradient(135deg, ${statusColor} 0%, ${adjustColor(statusColor, -30)} 100%); padding: 20px; border-radius: 12px; color: white; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2); cursor: help;" title="${tooltip}">
                        <div style="font-size: 14px; opacity: 0.9; margin-bottom: 8px;">${metric.name}</div>
                        <div style="font-size: 32px; font-weight: bold; margin-bottom: 4px;">${metric.value}${metric.unit || '%'}</div>
                        <div style="font-size: 12px; opacity: 0.8;">${trendIcon} ${metric.change || 'N/A'}</div>
                    </div>
                `;
            }).join('');
        }
    }

    // Update ART comparison table
    if (data.art_comparison) {
        const artTableBody = document.getElementById('artComparisonBody');
        if (artTableBody) {
            // Filter ARTs if selectedARTs is specified
            let displayedARTs = data.art_comparison;
            if (appState.selectedARTs && appState.selectedARTs.length > 0) {
                displayedARTs = data.art_comparison.filter(art =>
                    appState.selectedARTs.includes(art.art_name)
                );
            }

            console.log('📊 Updating ART comparison table with', displayedARTs.length, 'ARTs');
            artTableBody.innerHTML = displayedARTs.map(art => {
                const statusColor = art.status === 'healthy' ? '#34C759' :
                    art.status === 'warning' ? '#FF9500' : '#FF3B30';
                const statusLabel = art.status.charAt(0).toUpperCase() + art.status.slice(1);

                return `
                    <tr style="border-bottom: 1px solid #e9ecef;">
                        <td style="padding: 12px; font-weight: 600;">${art.art_name}</td>
                        <td style="padding: 12px;">${art.flow_efficiency?.toFixed(1) || 'N/A'}%</td>
                        <td style="padding: 12px;">${art.planning_accuracy?.toFixed(1) || 'N/A'}%</td>
                        <td style="padding: 12px;">${art.avg_leadtime?.toFixed(1) || 'N/A'} days</td>
                        <td style="padding: 12px;">${art.features_delivered || 0}</td>
                        <td style="padding: 12px;">${art.quality_score?.toFixed(1) || 'N/A'}%</td>
                        <td style="padding: 12px;">
                            <span style="background: ${statusColor}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px;">
                                ${statusLabel}
                            </span>
                        </td>
                    </tr>
                `;
            }).join('');
            console.log('✅ ART comparison table updated');
        }
    }

    // Update recent insights
    if (data.recent_insights) {
        const insightsContainer = document.getElementById('recentInsights');
        if (insightsContainer) {
            insightsContainer.innerHTML = data.recent_insights.map(insight => {
                const severityMap = {
                    'critical': { color: '#FF3B30', bg: '#fff3cd', icon: '🔴' },
                    'warning': { color: '#FF9500', bg: '#fff3cd', icon: '⚠️' },
                    'info': { color: '#007AFF', bg: '#d1ecf1', icon: 'ℹ️' }
                };
                const severity = severityMap[insight.severity] || severityMap['info'];

                return `
                    <div style="background: ${severity.bg}; padding: 16px; border-left: 4px solid ${severity.color}; border-radius: 4px; margin-bottom: 12px;">
                        <div style="font-weight: 600; color: ${severity.color}; margin-bottom: 8px;">
                            ${severity.icon} ${insight.title}
                        </div>
                        <div style="font-size: 14px; color: #333;">
                            ${insight.observation || insight.description || ''}
                        </div>
                    </div>
                `;
            }).join('');
        }
    }

    // Update PI information in the header/status bar
    if (data.current_pi || data.available_pis) {
        updatePIDisplay(data.current_pi, data.available_pis);
    }

    // Populate admin panel default filters
    // Use the full list of ARTs (unfiltered) instead of the filtered art_comparison
    if (data.available_pis && appState.allARTs && appState.allARTs.length > 0) {
        populateAdminDefaultFilters(data.available_pis, appState.allARTs);
    }

    updateStatusBar('Dashboard updated with real data');
}

// Helper function to adjust color brightness
function adjustColor(color, amount) {
    const num = parseInt(color.slice(1), 16);
    const r = Math.max(0, Math.min(255, (num >> 16) + amount));
    const g = Math.max(0, Math.min(255, ((num >> 8) & 0x00FF) + amount));
    const b = Math.max(0, Math.min(255, (num & 0x0000FF) + amount));
    return '#' + ((r << 16) | (g << 8) | b).toString(16).padStart(6, '0');
}

// Update PI display in the dashboard
function updatePIDisplay(currentPI, availablePIs) {
    // Update the PI selector if it exists
    const piSelector = document.getElementById('piSelector');
    if (piSelector && availablePIs && availablePIs.length > 0) {
        // Create multi-select with checkboxes
        piSelector.innerHTML = `
            <div style="max-height: 300px; overflow-y: auto; border: 1px solid #ddd; border-radius: 4px; padding: 8px; background: white;">
                <label style="display: block; padding: 4px; cursor: pointer; font-weight: 600;">
                    <input type="checkbox" id="selectAllPIs" style="margin-right: 8px;">
                    <span>Select All</span>
                </label>
                <hr style="margin: 8px 0; border: none; border-top: 1px solid #eee;">
                ${availablePIs.map(pi => `
                    <label style="display: block; padding: 4px; cursor: pointer;">
                        <input type="checkbox" class="pi-checkbox" value="${pi}" style="margin-right: 8px;" 
                               ${appState.selectedPIs.includes(pi) ? 'checked' : ''}>
                        <span>${pi}</span>
                    </label>
                `).join('')}
            </div>
        `;

        // Add event listeners after HTML is inserted
        const selectAll = document.getElementById('selectAllPIs');
        if (selectAll) {
            selectAll.addEventListener('change', function () {
                toggleAllPIs(this.checked);
            });
        }

        const checkboxes = document.querySelectorAll('.pi-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', handlePISelection);
        });
    }

    // PI info is now shown in Active Filters banner - no separate display needed
    console.log(`📅 PI Info - Current: ${currentPI}, Selected: ${appState.selectedPIs.length || 'All'}, Available: ${availablePIs?.length || 0}`);
}

// Handle PI checkbox selection
function handlePISelection() {
    const checkboxes = document.querySelectorAll('.pi-checkbox');
    appState.selectedPIs = Array.from(checkboxes)
        .filter(cb => cb.checked)
        .map(cb => cb.value);

    // Update "Select All" checkbox state
    const selectAll = document.getElementById('selectAllPIs');
    if (selectAll) {
        selectAll.checked = appState.selectedPIs.length === checkboxes.length;
    }

    console.log(`📅 PI selection changed: ${appState.selectedPIs.join(', ') || 'All PIs'}`);
    loadDashboardData();
    updateContext();
}

// Toggle all PIs
function toggleAllPIs(checked) {
    const checkboxes = document.querySelectorAll('.pi-checkbox');
    checkboxes.forEach(cb => cb.checked = checked);
    handlePISelection();
}

// Populate default filters in admin panel
function populateAdminDefaultFilters(availablePIs, availableARTs) {
    // Get saved defaults
    const savedDefaults = JSON.parse(localStorage.getItem('defaultFilters') || '{"pis":[],"arts":[]}');

    // Populate default PI selector
    const defaultPISelector = document.getElementById('defaultPISelector');
    if (defaultPISelector && availablePIs && availablePIs.length > 0) {
        defaultPISelector.innerHTML = `
            <label style="display: block; padding: 4px; cursor: pointer; font-weight: 600; border-bottom: 1px solid #eee; margin-bottom: 8px;">
                <input type="checkbox" id="selectAllDefaultPIs" style="margin-right: 8px;">
                <span>Select All</span>
            </label>
            ${availablePIs.map(pi => `
                <label style="display: block; padding: 4px; cursor: pointer;">
                    <input type="checkbox" class="default-pi-checkbox" value="${pi}" style="margin-right: 8px;" 
                           ${savedDefaults.pis.includes(pi) ? 'checked' : ''}>
                    <span>${pi}</span>
                </label>
            `).join('')}
        `;

        // Add select all handler
        const selectAllPIs = document.getElementById('selectAllDefaultPIs');
        if (selectAllPIs) {
            selectAllPIs.addEventListener('change', function () {
                document.querySelectorAll('.default-pi-checkbox').forEach(cb => cb.checked = this.checked);
            });
        }
    }

    // Populate default ART selector
    const defaultARTSelector = document.getElementById('defaultARTSelector');
    if (defaultARTSelector && availableARTs && availableARTs.length > 0) {
        defaultARTSelector.innerHTML = `
            <label style="display: block; padding: 4px; cursor: pointer; font-weight: 600; border-bottom: 1px solid #eee; margin-bottom: 8px;">
                <input type="checkbox" id="selectAllDefaultARTs" style="margin-right: 8px;">
                <span>Select All</span>
            </label>
            ${availableARTs.map(art => `
                <label style="display: block; padding: 4px; cursor: pointer;">
                    <input type="checkbox" class="default-art-checkbox" value="${art}" style="margin-right: 8px;" 
                           ${savedDefaults.arts.includes(art) ? 'checked' : ''}>
                    <span>${art}</span>
                </label>
            `).join('')}
        `;

        // Add select all handler
        const selectAllARTs = document.getElementById('selectAllDefaultARTs');
        if (selectAllARTs) {
            selectAllARTs.addEventListener('change', function () {
                document.querySelectorAll('.default-art-checkbox').forEach(cb => cb.checked = this.checked);
            });
        }
    }

    console.log('⚙️ Admin default filters populated');
}

// Scope Selection
function selectScope(scope) {
    appState.scope = scope;

    // When entering Portfolio view, ensure saved default filters are applied
    // (otherwise a previously selected ART in ART view can keep constraining the portfolio).
    if (scope === 'portfolio') {
        const defaults = getSavedDefaultFilters();
        appState.selectedPIs = defaults.pis;
        appState.selectedARTs = defaults.arts;

        // Clear any scope-specific selections when returning to portfolio
        appState.selectedART = '';
        appState.selectedTeam = '';

        const artSelector = document.getElementById('artSelector');
        if (artSelector) artSelector.value = '';
        const teamSelector = document.getElementById('teamSelector');
        if (teamSelector) teamSelector.value = '';
    }

    // Update button states
    document.querySelectorAll('.sidebar-section button').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');

    // Show/hide ART and Team selectors
    const artSelection = document.getElementById('artSelection');
    const teamSelection = document.getElementById('teamSelection');

    if (scope === 'art') {
        artSelection.style.display = 'block';
        teamSelection.style.display = 'none';
    } else if (scope === 'team') {
        artSelection.style.display = 'block';
        teamSelection.style.display = 'block';
    } else {
        artSelection.style.display = 'none';
        teamSelection.style.display = 'none';
    }

    // Update context and reload dashboard with new scope
    updateContext();
    loadDashboardData();
}

async function generateScorecard() {
    updateStatusBar('Generating scorecard...');

    try {
        const response = await fetch(`${API_BASE_URL}/v1/scorecard`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                scope: appState.scope,
                scope_id: appState.selectedART || appState.selectedTeam || null,
                time_range: appState.timeRange,
                metric_focus: appState.metricFocus
            })
        });

        if (response.ok) {
            const scorecard = await response.json();
            console.log('✅ Scorecard generated:', scorecard);

            const message = {
                type: 'agent',
                content: `📋 <strong>Scorecard Generated for ${capitalizeFirst(appState.scope)}</strong><br><br>
                    <strong>Overall Health Score:</strong> ${scorecard.overall_score.toFixed(0)}/100 (Healthy)<br><br>
                    <strong>Key Metrics:</strong><br>
                    ${scorecard.metrics.map(m => `• ${m.name}: ${m.value}${m.unit} (${m.status}) ${m.trend === 'up' ? '↑' : m.trend === 'down' ? '↓' : '→'}`).join('<br>')}<br><br>
                    <strong>Dimensions:</strong><br>
                    ${Object.entries(scorecard.dimension_scores).map(([dim, score]) => `• ${capitalizeFirst(dim)}: ${score.toFixed(0)}/100`).join('<br>')}`,
                timestamp: new Date()
            };

            if (appState.activeTab === 'chat') {
                addMessage(message);
            } else {
                appState.messages.push(message);
            }

            updateStatusBar('Scorecard generated successfully from API');
        }
    } catch (error) {
        console.error('Error generating scorecard:', error);
        // Fall back to demo response
        generateScorecardDemo();
    }
}

function generateScorecardDemo() {
    const message = {
        type: 'agent',
        content: `📋 <strong>Scorecard Generated for ${capitalizeFirst(appState.scope)}</strong><br><br>
            <strong>Overall Health Score:</strong> 78/100 (Healthy)<br><br>
            <strong>Key Metrics:</strong><br>
            • Flow Efficiency: 67% (Good) ↑<br>
            • Planning Accuracy: 82% (Excellent) ↑<br>
            • Average Lead-Time: 45 days (Good) →<br>
            • Quality (Defect Rate): 4.2% (Acceptable) ↓<br>
            • Team Stability: 89% (Excellent) →<br><br>
            <strong>Top Recommendation:</strong> Address high WIP in Customer Experience ART to improve flow efficiency further.`,
        timestamp: new Date()
    };

    if (appState.activeTab === 'chat') {
        addMessage(message);
    } else {
        appState.messages.push(message);
    }

    updateStatusBar('Scorecard generated (demo mode)');
}

// Metric Focus Selection
function setMetricFocus(focus) {
    appState.metricFocus = focus;

    // Update button states
    document.querySelectorAll('#metricFocusButtons .sidebar-button').forEach(btn => {
        btn.classList.remove('active');
    });
    if (event && event.target) {
        event.target.classList.add('active');
    }

    updateStatusBar(`Metric focus changed to ${focus}`);
    updateContext();
}

// Update context function
function updateContext() {
    const defaults = getSavedDefaultFilters();

    // In Portfolio view we always use the saved default filters,
    // regardless of what's currently selected in the (hidden) ART/Team dropdowns.
    if (appState.scope === 'portfolio') {
        appState.selectedART = '';
        appState.selectedTeam = '';
        appState.selectedARTs = defaults.arts;

        const artSelector = document.getElementById('artSelector');
        if (artSelector) artSelector.value = '';
        const teamSelector = document.getElementById('teamSelector');
        if (teamSelector) teamSelector.value = '';
    }

    // Update selected ART
    const artSelector = document.getElementById('artSelector');
    if (artSelector) {
        if (appState.scope !== 'portfolio') {
            appState.selectedART = artSelector.value;

            // If an ART is selected, update selectedARTs array for filtering
            if (artSelector.value) {
                appState.selectedARTs = [artSelector.value];
            } else {
                // If no ART selected, use default filters or all ARTs
                appState.selectedARTs = defaults.arts;
            }
        }
    }

    // Update selected team
    const teamSelector = document.getElementById('teamSelector');
    if (teamSelector) {
        if (appState.scope !== 'portfolio') {
            appState.selectedTeam = teamSelector.value;
        }
    }

    // Build simplified context without filter details (shown in Active Filters banner)
    let contextText = `Context: ${capitalizeFirst(appState.scope)}`;
    if (appState.selectedART) contextText += ` | ART: ${appState.selectedART}`;
    if (appState.selectedTeam) contextText += ` | Team: ${appState.selectedTeam}`;
    contextText += ` | Focus: ${capitalizeFirst(appState.metricFocus)}`;

    // Update context displays
    const activeContext = document.getElementById('activeContext');
    if (activeContext) {
        activeContext.innerHTML = contextText.replace(/Context: /, '').replace(/ \| /g, '<br>');
    }

    const inlineContext = document.getElementById('inlineContext');
    if (inlineContext) {
        inlineContext.textContent = contextText.replace(/Context: /, '');
    }

    // If on metrics tab, reload metrics with new filter
    if (appState.activeTab === 'metrics') {
        console.log('📊 Reloading metrics with updated filter:', appState.selectedARTs);
        loadMetricsCatalog();
    }

    console.log('📊 Context updated:', contextText, '| ARTs:', appState.selectedARTs);
}

// Display generated insights
function displayGeneratedInsights(insights) {
    const message = {
        type: 'agent',
        content: `💡 <strong>Top 3 Insights Generated</strong><br><br>
            <strong>1. Critical: High WIP in Customer Experience ART</strong><br>
            Confidence: 92% | Impact: Immediate<br>
            WIP ratio at 2.3 vs target 1.5. Recommend implementing hard WIP limits.<br><br>
            <strong>2. Warning: Increasing Defect Escape Rate</strong><br>
            Confidence: 87% | Impact: Within 2 sprints<br>
            Mobile Apps team at 7.2% escape rate. 68% lack test coverage.<br><br>
            <strong>3. Success: Excellent Flow Improvement</strong><br>
            Confidence: 95% | Impact: Sustained<br>
            Platform Engineering achieved 72% flow efficiency, up from 64%.<br><br>
            Switch to the <strong>Insights</strong> tab for detailed analysis and recommendations.`,
        timestamp: new Date()
    };

    if (appState.activeTab === 'chat') {
        addMessage(message);
    } else {
        appState.messages.push(message);
    }

    updateStatusBar('Insights generated - 3 actionable items found');
}

// Export Report
function exportReport() {
    updateStatusBar('Preparing report for export...');

    setTimeout(() => {
        alert('📥 Report Export\n\nYour report has been generated and would be downloaded as:\n\n"evaluation_coach_report_' + new Date().toISOString().split('T')[0] + '.pdf"\n\nContents:\n• Health Scorecard\n• Key Metrics Dashboard\n• Actionable Insights\n• Improvement Recommendations\n\n(Demo mode - actual export requires backend integration)');
        updateStatusBar('Report export completed');
    }, 1000);
}

async function sendMessage(event) {
    event.preventDefault();

    const input = document.getElementById('messageInput');
    const messageText = input.value.trim();

    if (!messageText) return;

    // Add user message
    const userMessage = {
        type: 'user',
        content: messageText,
        timestamp: new Date()
    };
    addMessage(userMessage);

    // Clear input
    input.value = '';

    // Disable send button
    const sendButton = document.getElementById('sendButton');
    sendButton.disabled = true;
    sendButton.textContent = 'Thinking...';

    try {
        // Send to API
        const response = await fetch(`${API_BASE_URL}/v1/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: messageText,
                session_id: appState.sessionId,
                context: {
                    scope: appState.scope,
                    scope_id: appState.selectedART || appState.selectedTeam,
                    time_range: appState.timeRange,
                    metric_focus: appState.metricFocus
                }
            })
        });

        if (response.ok) {
            const data = await response.json();
            const agentMessage = {
                type: 'agent',
                content: data.message,
                timestamp: new Date(data.timestamp)
            };
            addMessage(agentMessage);
        } else {
            throw new Error('API request failed');
        }
    } catch (error) {
        console.error('Error sending message:', error);
        // Fall back to local response
        const responseText = generateAIResponse(messageText);
        const agentMessage = {
            type: 'agent',
            content: responseText,
            timestamp: new Date()
        };
        addMessage(agentMessage);
    } finally {
        // Re-enable send button
        sendButton.disabled = false;
        sendButton.textContent = 'Send';
    }
}

// Main Tab Switching
function switchMainTab(tabName) {
    console.log('Switching to tab:', tabName);
    appState.activeTab = tabName;

    // Update tab button states
    document.querySelectorAll('.main-tab').forEach(tab => {
        tab.classList.remove('active');
    });

    // Add active class to the appropriate button
    const clickedButton = window.event?.target?.closest?.('.main-tab') ||
        document.querySelector(`.main-tab[onclick*="switchMainTab('${tabName}')"]`);
    if (clickedButton) {
        clickedButton.classList.add('active');
    }

    // Show/hide tab content
    const tabs = ['dashboard', 'chat', 'insights', 'metrics', 'admin'];
    tabs.forEach(tab => {
        const content = document.getElementById(`${tab}Content`);
        if (content) {
            content.style.display = tab === tabName ? 'flex' : 'none';
        }
    });

    // Load data when switching to specific tabs
    if (tabName === 'insights') {
        renderInsightsTab();
    } else if (tabName === 'metrics') {
        loadMetricsCatalog();
    } else if (tabName === 'admin') {
        loadStrategicTargets();
    }

    updateStatusBar(`Switched to ${tabName} view`);
}

// Render detailed insights in the Insights tab
function renderInsightsTab() {
    console.log('📊 Loading Insights tab...');

    const insightsContent = document.getElementById('insightsContent');
    if (!insightsContent) return;

    // Build filter info respecting scope priority
    const filterParts = [
        appState.scope.charAt(0).toUpperCase() + appState.scope.slice(1),
        appState.selectedPIs.length > 0 ? `PI: ${appState.selectedPIs.join(', ')}` : 'All PIs'
    ];

    // Add ART info based on scope
    if (appState.scope === 'art' && appState.selectedART) {
        filterParts.push(`ART: ${appState.selectedART}`);
    } else if (appState.selectedARTs && appState.selectedARTs.length > 0) {
        // If all ARTs are selected, show "All ARTs"
        if (appState.allARTs && appState.selectedARTs.length >= appState.allARTs.length) {
            filterParts.push('All ARTs');
        } else {
            const artText = appState.selectedARTs.length <= 5
                ? appState.selectedARTs.join(', ')
                : `${appState.selectedARTs.slice(0, 5).join(', ')} +${appState.selectedARTs.length - 5} more`;
            filterParts.push(`ARTs: ${artText}`);
        }
    } else {
        filterParts.push('All ARTs');
    }

    const filterInfo = filterParts.join(' | ');

    // Show initial view with Generate button
    insightsContent.innerHTML = `
        <div class="messages">
            <div class="active-context-inline">
                <div class="active-context-title-inline">📊 Active Filters</div>
                <div class="active-context-content-inline">
                    ${filterInfo}
                </div>
            </div>

            <div style="background: white; border-radius: 8px; padding: 40px; text-align: center;">
                <div style="font-size: 48px; margin-bottom: 16px;">🤖</div>
                <h2 style="margin-bottom: 16px; color: #333;">AI-Powered Expert Insights</h2>
                <p style="color: #666; margin-bottom: 24px; line-height: 1.6;">
                    Generate comprehensive insights using advanced AI analysis with 15+ years of industry experience.
                    <br>This will analyze your data patterns, bottlenecks, and provide actionable recommendations.
                </p>
                <button 
                    id="generateInsightsBtn"
                    onclick="generateInsights()" 
                    style="
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        border: none;
                        padding: 16px 32px;
                        font-size: 16px;
                        font-weight: 600;
                        border-radius: 8px;
                        cursor: pointer;
                        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
                        transition: all 0.3s ease;
                        display: inline-flex;
                        align-items: center;
                        gap: 8px;
                    "
                    onmouseover="if(!this.disabled) { this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 16px rgba(102, 126, 234, 0.5)'; }"
                    onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 12px rgba(102, 126, 234, 0.4)'"
                >
                    <span id="generateBtnIcon">🚀</span>
                    <span id="generateBtnText">Generate AI Insights</span>
                </button>
                <button 
                    id="cancelInsightsBtn"
                    onclick="cancelInsightsGeneration()" 
                    style="
                        background: #FF3B30;
                        color: white;
                        border: none;
                        padding: 16px 32px;
                        font-size: 16px;
                        font-weight: 600;
                        border-radius: 8px;
                        cursor: pointer;
                        box-shadow: 0 4px 12px rgba(255, 59, 48, 0.4);
                        transition: all 0.3s ease;
                        display: none;
                        align-items: center;
                        gap: 8px;
                        margin-left: 12px;
                    "
                    onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 16px rgba(255, 59, 48, 0.5)';"
                    onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 12px rgba(255, 59, 48, 0.4)'"
                >
                    🛑 Cancel
                </button>
                <div style="margin-top: 16px; font-size: 12px; color: #8E8E93;">
                    ⚠️ This may take a while as the AI analyzes your data
                </div>
            </div>
        </div>
    `;
}

// Generate insights using AI analysis
function generateInsights() {
    console.log('🤖 Generating AI insights...');

    // Cancel any existing request
    if (appState.insightsAbortController) {
        appState.insightsAbortController.abort();
    }

    // Create new abort controller
    appState.insightsAbortController = new AbortController();

    // Disable button and show spinner
    const btn = document.getElementById('generateInsightsBtn');
    const btnIcon = document.getElementById('generateBtnIcon');
    const btnText = document.getElementById('generateBtnText');

    if (btn) {
        btn.disabled = true;
        btn.style.opacity = '0.7';
        btn.style.cursor = 'not-allowed';
        if (btnIcon) {
            btnIcon.innerHTML = '<div style="width: 16px; height: 16px; border: 2px solid rgba(255,255,255,0.3); border-top: 2px solid white; border-radius: 50%; animation: spin 0.8s linear infinite;"></div>';
        }
        if (btnText) btnText.textContent = 'Generating...';
    }

    // Show cancel button
    const cancelBtn = document.getElementById('cancelInsightsBtn');
    if (cancelBtn) {
        cancelBtn.style.display = 'inline-block';
    }

    showLoadingOverlay('🤔 AI Coach analyzing your data...');

    const params = new URLSearchParams();
    params.append('scope', appState.scope);

    if (appState.selectedPIs.length > 0) {
        params.append('pis', appState.selectedPIs.join(','));
    }

    // Priority: scope-specific ART selection overrides default ARTs filter
    if (appState.scope === 'art' && appState.selectedART) {
        // ART View - analyze only the selected ART
        params.append('arts', appState.selectedART);
    } else if (appState.selectedARTs.length > 0) {
        // Portfolio View - analyze filtered ARTs
        params.append('arts', appState.selectedARTs.join(','));
    }

    // Add LLM configuration
    const llmConfig = getLLMConfig();
    params.append('model', llmConfig.model);
    params.append('temperature', llmConfig.temperature);
    params.append('enhance_with_llm', 'true');  // Enable LLM enhancement with RAG

    // Update message after 2 seconds (LLM processing)
    const llmTimer = setTimeout(() => {
        updateLoadingMessage(`🧠 Expert analysis in progress with ${llmConfig.model}...`);
    }, 2000);

    fetch(`${API_BASE_URL}/v1/insights/generate?${params.toString()}`, {
        method: 'POST',
        signal: appState.insightsAbortController.signal
    })
        .then(response => response.json())
        .then(data => {
            clearTimeout(llmTimer);
            const insights = data.insights || [];
            displayGeneratedInsights(insights);
            hideLoadingOverlay();

            // Hide cancel button on success
            const cancelBtn = document.getElementById('cancelInsightsBtn');
            if (cancelBtn) {
                cancelBtn.style.display = 'none';
            }

            appState.insightsAbortController = null;
        })
        .catch(error => {
            clearTimeout(llmTimer);

            // Check if request was cancelled
            if (error.name === 'AbortError') {
                console.log('🚫 Insights generation cancelled by user');
                const insightsContent = document.getElementById('insightsContent');
                if (insightsContent) {
                    insightsContent.innerHTML = `
                        <div class="messages">
                            <div style="background: white; border-radius: 8px; padding: 40px; text-align: center; color: #666;">
                                <div style="font-size: 48px; margin-bottom: 16px;">🚫</div>
                                <div style="font-size: 18px; margin-bottom: 8px;">Request Cancelled</div>
                                <div style="font-size: 14px; color: #666; margin-bottom: 24px;">Insight generation was cancelled</div>
                                <button onclick="renderInsightsTab()" style="
                                    background: #667eea;
                                    color: white;
                                    border: none;
                                    padding: 12px 24px;
                                    border-radius: 6px;
                                    cursor: pointer;
                                    font-weight: 600;
                                ">Generate Insights</button>
                            </div>
                        </div>
                    `;
                }
            } else {
                console.error('❌ Error generating insights:', error);
                const insightsContent = document.getElementById('insightsContent');
                if (insightsContent) {
                    insightsContent.innerHTML = `
                        <div class="messages">
                            <div style="background: white; border-radius: 8px; padding: 40px; text-align: center; color: #FF3B30;">
                                <div style="font-size: 48px; margin-bottom: 16px;">⚠️</div>
                                <div style="font-size: 18px; margin-bottom: 8px;">Error Generating Insights</div>
                                <div style="font-size: 14px; color: #666; margin-bottom: 24px;">${error.message}</div>
                                <button onclick="renderInsightsTab()" style="
                                    background: #667eea;
                                    color: white;
                                    border: none;
                                    padding: 12px 24px;
                                    border-radius: 6px;
                                    cursor: pointer;
                                    font-weight: 600;
                                ">Try Again</button>
                            </div>
                        </div>
                    `;
                }
            }

            // Re-enable button
            if (btn) {
                btn.disabled = false;
                btn.style.opacity = '1';
                btn.style.cursor = 'pointer';
                if (btnIcon) btnIcon.textContent = '🚀';
                if (btnText) btnText.textContent = 'Generate AI Insights';
            }

            // Hide cancel button
            const cancelBtn = document.getElementById('cancelInsightsBtn');
            if (cancelBtn) {
                cancelBtn.style.display = 'none';
            }

            hideLoadingOverlay();
            appState.insightsAbortController = null;
        });
}

// Display generated insights
function displayGeneratedInsights(insights) {
    const insightsContent = document.getElementById('insightsContent');
    if (!insightsContent) return;

    const severityConfig = {
        'critical': { color: '#FF3B30', label: 'CRITICAL', badge: '#FF3B30' },
        'warning': { color: '#FF9500', label: 'WARNING', badge: '#FF9500' },
        'info': { color: '#34C759', label: 'INFO', badge: '#34C759' }
    };

    // Build filter info respecting scope priority
    const filterParts = [
        appState.scope.charAt(0).toUpperCase() + appState.scope.slice(1),
        appState.selectedPIs.length > 0 ? `PI: ${appState.selectedPIs.join(', ')}` : 'All PIs'
    ];

    // Add ART info based on scope
    if (appState.scope === 'art' && appState.selectedART) {
        filterParts.push(`ART: ${appState.selectedART}`);
    } else if (appState.selectedARTs && appState.selectedARTs.length > 0) {
        // If all ARTs are selected, show "All ARTs"
        if (appState.allARTs && appState.selectedARTs.length >= appState.allARTs.length) {
            filterParts.push('All ARTs');
        } else {
            const artText = appState.selectedARTs.length <= 5
                ? appState.selectedARTs.join(', ')
                : `${appState.selectedARTs.slice(0, 5).join(', ')} +${appState.selectedARTs.length - 5} more`;
            filterParts.push(`ARTs: ${artText}`);
        }
    } else {
        filterParts.push('All ARTs');
    }

    const filterInfo = filterParts.join(' | ');

    const insightsHTML = `
        <div class="messages">
            <div class="active-context-inline">
                <div class="active-context-title-inline">📊 Active Filters</div>
                <div class="active-context-content-inline">
                    ${filterInfo}
                </div>
            </div>
            
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h2 style="margin: 0; color: #333;">AI Expert Insights (${insights.length})</h2>
                <div style="display: flex; gap: 12px;">
                    <button 
                        onclick="exportExecutiveSummary()" 
                        style="
                            background: linear-gradient(135deg, #007AFF 0%, #0051D5 100%);
                            color: white;
                            border: none;
                            padding: 10px 20px;
                            font-size: 14px;
                            font-weight: 600;
                            border-radius: 6px;
                            cursor: pointer;
                            box-shadow: 0 2px 8px rgba(0, 122, 255, 0.3);
                            display: inline-flex;
                            align-items: center;
                            gap: 6px;
                        "
                    >
                        <span>📊</span>
                        <span>Export to Excel</span>
                    </button>
                    <button 
                        onclick="printAllInsights()" 
                        style="
                            background: linear-gradient(135deg, #34C759 0%, #30B350 100%);
                            color: white;
                            border: none;
                            padding: 10px 20px;
                            font-size: 14px;
                            font-weight: 600;
                            border-radius: 6px;
                            cursor: pointer;
                            box-shadow: 0 2px 8px rgba(52, 199, 89, 0.3);
                            display: inline-flex;
                            align-items: center;
                            gap: 6px;
                        "
                    >
                        <span>🖨️</span>
                        <span>Print Report</span>
                    </button>
                    <button 
                        id="generateInsightsBtn"
                        onclick="generateInsights()" 
                        style="
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            color: white;
                            border: none;
                            padding: 10px 20px;
                            font-size: 14px;
                            font-weight: 600;
                            border-radius: 6px;
                            cursor: pointer;
                            box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
                            display: inline-flex;
                            align-items: center;
                            gap: 6px;
                        "
                    >
                        <span id="generateBtnIcon">🔄</span>
                        <span id="generateBtnText">Regenerate Insights</span>
                    </button>
                </div>
            </div>
            
            ${insights.length === 0 ? `
                <div style="background: white; border-radius: 8px; padding: 40px; text-align: center; color: #8E8E93;">
                    <div style="font-size: 48px; margin-bottom: 16px;">💡</div>
                    <div style="font-size: 18px; margin-bottom: 8px;">No insights available</div>
                    <div style="font-size: 14px;">Try adjusting your filters or generate new insights</div>
                </div>
            ` : insights.map((insight, index) => {
        const config = severityConfig[insight.severity] || severityConfig['info'];
        const confidence = Math.round((insight.confidence || 0) * 100);
        const actions = insight.recommended_actions || [];
        const rootCauses = insight.root_causes || [];
        const expectedOutcomes = insight.expected_outcomes || {};

        return `
                            <div style="background: white; border: 2px solid ${config.color}; border-radius: 8px; padding: 20px; margin-bottom: 16px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);">
                                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
                                    <h3 style="color: ${config.color}; margin: 0;">${insight.title}</h3>
                                    <span style="background: ${config.badge}; color: white; padding: 4px 12px; border-radius: 4px; font-size: 12px; font-weight: 600;">${config.label}</span>
                                </div>
                                
                                <div style="display: flex; gap: 16px; margin-bottom: 12px; font-size: 14px; color: #666;">
                                    <span>🎯 Confidence: <strong>${confidence}%</strong></span>
                                    <span>📊 Scope: <strong>${insight.scope || 'Portfolio'}</strong></span>
                                    <span>📈 Insights: <strong>#${index + 1}</strong></span>
                                </div>
                                
                                ${insight.observation ? `
                                    <p style="color: #333; margin-bottom: 12px; line-height: 1.6;">
                                        <strong>📋 Observation:</strong> ${insight.observation}
                                    </p>
                                ` : ''}
                                
                                ${insight.interpretation ? `
                                    <p style="color: #333; margin-bottom: 12px; line-height: 1.6;">
                                        <strong>💭 Interpretation:</strong> ${insight.interpretation}
                                    </p>
                                ` : ''}
                                
                                ${rootCauses.length > 0 ? `
                                    <div style="background: #f8f9fa; padding: 12px; border-radius: 6px; margin-bottom: 12px;">
                                        <strong style="display: block; margin-bottom: 8px; color: #667eea;">🔍 Root Causes:</strong>
                                        <ul style="padding-left: 20px; line-height: 1.8; color: #555; margin: 0;">
                                            ${rootCauses.map(rc => `
                                                <li>
                                                    <strong>${rc.description}</strong>
                                                    ${rc.evidence && rc.evidence.length > 0 ? `
                                                        <ul style="font-size: 13px; color: #666; margin-top: 4px;">
                                                            ${rc.evidence.map(e => `<li>${e}</li>`).join('')}
                                                        </ul>
                                                    ` : ''}
                                                    ${rc.confidence ? `<span style="font-size: 12px; color: #888;">(${Math.round(rc.confidence * 100)}% confidence)</span>` : ''}
                                                </li>
                                            `).join('')}
                                        </ul>
                                    </div>
                                ` : ''}
                                
                                ${actions.length > 0 ? `
                                    <div style="background: #e8f5e9; padding: 12px; border-radius: 6px; margin-bottom: 12px;">
                                        <strong style="display: block; margin-bottom: 8px; color: #2e7d32;">✅ Recommended Actions:</strong>
                                        <ul style="padding-left: 20px; line-height: 1.8; color: #333; margin: 0;">
                                            ${actions.map(action => `
                                                <li>
                                                    <strong>[${action.timeframe.replace('_', ' ').toUpperCase()}]</strong> ${action.description}
                                                    <div style="font-size: 13px; color: #666; margin-top: 4px;">
                                                        👤 Owner: ${action.owner || 'TBD'} | 
                                                        ⏱️ Effort: ${action.effort || 'TBD'}
                                                        ${action.success_signal ? `<br/>🎯 Success Signal: ${action.success_signal}` : ''}
                                                    </div>
                                                </li>
                                            `).join('')}
                                        </ul>
                                    </div>
                                ` : ''}
                                
                                ${expectedOutcomes.timeline || expectedOutcomes.metrics_to_watch ? `
                                    <div style="background: #fff9e6; padding: 12px; border-radius: 6px; margin-bottom: 12px;">
                                        <strong style="display: block; margin-bottom: 8px; color: #f57f17;">📊 Expected Outcomes:</strong>
                                        ${expectedOutcomes.timeline ? `<div style="font-size: 14px; color: #666; margin-bottom: 4px;">⏱️ Timeline: <strong>${expectedOutcomes.timeline}</strong></div>` : ''}
                                        ${expectedOutcomes.metrics_to_watch && expectedOutcomes.metrics_to_watch.length > 0 ? `
                                            <div style="font-size: 13px; color: #666;">
                                                📈 Metrics to Watch: ${expectedOutcomes.metrics_to_watch.join(', ')}
                                            </div>
                                        ` : ''}
                                        ${expectedOutcomes.leading_indicators && expectedOutcomes.leading_indicators.length > 0 ? `
                                            <div style="font-size: 13px; color: #666; margin-top: 4px;">
                                                ⚡ Leading Indicators: ${expectedOutcomes.leading_indicators.join(', ')}
                                            </div>
                                        ` : ''}
                                    </div>
                                ` : ''}
                                
                                <div style="display: flex; gap: 8px; margin-top: 16px;">
                                    <button class="template-action-btn" onclick="viewInsightDetails(${index})">📋 View Full Details</button>
                                    <button class="template-action-btn" style="background: #5856D6;" onclick="printInsight(${index})">🖨️ Print</button>
                                    <button class="template-action-btn" style="background: #34C759;" onclick="exportInsight(${index})">💾 Export</button>
                                </div>
                            </div>
                        `;
    }).join('')}
        </div>
    `;

    insightsContent.innerHTML = insightsHTML;

    // Store insights in appState for actions
    appState.currentInsights = insights;

    console.log(`✅ Displayed ${insights.length} AI-generated insights`);
}

// View insight details (placeholder for future modal/detail view)
function viewInsightDetails(index) {
    const insight = appState.currentInsights?.[index];
    if (!insight) return;

    console.log('📊 Viewing insight details:', insight);

    const modal = document.getElementById('insightDetailsModal');
    const titleEl = document.getElementById('insightDetailsTitle');
    const bodyEl = document.getElementById('insightDetailsBody');

    if (!modal || !titleEl || !bodyEl) {
        // Fallback if modal isn't present
        alert(`Insight Details:\n\nTitle: ${insight.title}`);
        return;
    }

    const confidencePct = Math.round((insight.confidence || 0) * 100);
    const rootCauses = insight.root_causes || [];
    const actions = insight.recommended_actions || [];
    const expected = insight.expected_outcomes || {};
    const evidence = insight.evidence || [];
    const metricRefs = insight.metric_references || [];

    titleEl.textContent = insight.title || 'Insight Details';

    bodyEl.innerHTML = `
        <div style="display:flex; gap: 12px; flex-wrap: wrap; margin-bottom: 12px; color:#666; font-size: 14px;">
            <div>🎯 Confidence: <strong>${confidencePct}%</strong></div>
            <div>📊 Scope: <strong>${insight.scope || 'Portfolio'}</strong></div>
            ${insight.severity ? `<div>⚠️ Severity: <strong>${insight.severity}</strong></div>` : ''}
        </div>

        ${insight.observation ? `
            <div style="margin-bottom: 14px;">
                <div style="font-weight: 700; margin-bottom: 6px;">📋 Observation</div>
                <div style="color:#333; line-height:1.6;">${insight.observation}</div>
            </div>
        ` : ''}

        ${insight.interpretation ? `
            <div style="margin-bottom: 14px;">
                <div style="font-weight: 700; margin-bottom: 6px;">💭 Interpretation</div>
                <div style="color:#333; line-height:1.6; white-space: pre-wrap;">${insight.interpretation}</div>
            </div>
        ` : ''}

        ${rootCauses.length ? `
            <div style="margin-bottom: 14px;">
                <div style="font-weight: 700; margin-bottom: 6px;">🔍 Root Causes</div>
                <ul style="margin: 0; padding-left: 18px; line-height: 1.7; color:#333;">
                    ${rootCauses.map(rc => `
                        <li style="margin-bottom: 8px;">
                            <div><strong>${rc.description || 'Root cause'}</strong>
                                ${rc.confidence ? ` <span style="color:#888; font-size: 12px;">(${Math.round((rc.confidence || 0) * 100)}% confidence)</span>` : ''}
                            </div>
                            ${rc.evidence && rc.evidence.length ? `
                                <ul style="margin-top: 4px; padding-left: 18px; color:#666; font-size: 13px;">
                                    ${rc.evidence.map(e => `<li>${e}</li>`).join('')}
                                </ul>
                            ` : ''}
                            ${rc.reference ? `<div style="color:#888; font-size: 12px; margin-top: 4px;">📎 Reference: ${rc.reference}</div>` : ''}
                        </li>
                    `).join('')}
                </ul>
            </div>
        ` : ''}

        ${actions.length ? `
            <div style="margin-bottom: 14px;">
                <div style="font-weight: 700; margin-bottom: 6px;">✅ Recommended Actions</div>
                <ul style="margin: 0; padding-left: 18px; line-height: 1.7; color:#333;">
                    ${actions.map(a => `
                        <li style="margin-bottom: 10px;">
                            <div>
                                ${a.timeframe ? `<strong>[${String(a.timeframe).replace('_', ' ').toUpperCase()}]</strong> ` : ''}
                                ${a.description || ''}
                            </div>
                            <div style="color:#666; font-size: 13px; margin-top: 4px;">
                                ${a.owner ? `👤 Owner: ${a.owner}` : '👤 Owner: TBD'}
                                ${a.effort ? ` | ⏱️ Effort: ${a.effort}` : ''}
                                ${a.dependencies && a.dependencies.length ? `<br/>🔗 Dependencies: ${a.dependencies.join(', ')}` : ''}
                                ${a.success_signal ? `<br/>🎯 Success Signal: ${a.success_signal}` : ''}
                            </div>
                        </li>
                    `).join('')}
                </ul>
            </div>
        ` : ''}

        ${(expected.timeline || (expected.metrics_to_watch && expected.metrics_to_watch.length)) ? `
            <div style="margin-bottom: 14px;">
                <div style="font-weight: 700; margin-bottom: 6px;">📊 Expected Outcomes</div>
                ${expected.timeline ? `<div style="color:#333; margin-bottom: 6px;">⏱️ Timeline: <strong>${expected.timeline}</strong></div>` : ''}
                ${expected.metrics_to_watch && expected.metrics_to_watch.length ? `<div style="color:#666; font-size: 13px;">📈 Metrics to Watch: ${expected.metrics_to_watch.join(', ')}</div>` : ''}
                ${expected.leading_indicators && expected.leading_indicators.length ? `<div style="color:#666; font-size: 13px; margin-top: 4px;">⚡ Leading Indicators: ${expected.leading_indicators.join(', ')}</div>` : ''}
                ${expected.lagging_indicators && expected.lagging_indicators.length ? `<div style="color:#666; font-size: 13px; margin-top: 4px;">📉 Lagging Indicators: ${expected.lagging_indicators.join(', ')}</div>` : ''}
                ${expected.risks && expected.risks.length ? `<div style="color:#666; font-size: 13px; margin-top: 4px;">⚠️ Risks: ${expected.risks.join(', ')}</div>` : ''}
            </div>
        ` : ''}

        ${metricRefs.length ? `
            <div style="margin-bottom: 14px;">
                <div style="font-weight: 700; margin-bottom: 6px;">🔗 Metric References</div>
                <div style="color:#666; font-size: 13px; line-height:1.6;">${metricRefs.join('<br/>')}</div>
            </div>
        ` : ''}

        ${evidence.length ? `
            <div style="margin-bottom: 0;">
                <div style="font-weight: 700; margin-bottom: 6px;">🧾 Evidence</div>
                <ul style="margin: 0; padding-left: 18px; line-height: 1.7; color:#333;">
                    ${evidence.map(ev => `<li>${ev}</li>`).join('')}
                </ul>
            </div>
        ` : ''}
    `;

    modal.style.display = 'block';
}

function closeInsightDetails() {
    const modal = document.getElementById('insightDetailsModal');
    if (modal) modal.style.display = 'none';
}

// Close insight details modal when clicking outside the dialog
window.addEventListener('click', (event) => {
    const modal = document.getElementById('insightDetailsModal');
    if (modal && event.target === modal) {
        closeInsightDetails();
    }
});

// Export insight (placeholder for future export functionality)
function exportInsight(index) {
    const insight = appState.currentInsights?.[index];
    if (insight) {
        console.log('💾 Exporting insight:', insight);
        const json = JSON.stringify(insight, null, 2);
        const blob = new Blob([json], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `insight-${insight.title.replace(/\s+/g, '-').toLowerCase()}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        updateStatusBar('Insight exported successfully');
    }
}

// Print a single insight as a formatted report
function printInsight(index) {
    const insight = appState.currentInsights?.[index];
    if (!insight) return;

    const printWindow = window.open('', '', 'width=800,height=600');
    const formattedReport = generateInsightHTML(insight, index + 1);

    printWindow.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
            <title>Insight Report - ${insight.title}</title>
            <style>
                ${getPrintStyles()}
            </style>
        </head>
        <body>
            ${generateReportHeader()}
            ${formattedReport}
            ${generateReportFooter()}
        </body>
        </html>
    `);

    printWindow.document.close();
    printWindow.focus();
    setTimeout(() => {
        printWindow.print();
        printWindow.close();
    }, 250);

    updateStatusBar('Insight report prepared for printing');
}

// Print all insights as a comprehensive report
function printAllInsights() {
    const insights = appState.currentInsights || [];
    if (insights.length === 0) {
        alert('No insights available to print');
        return;
    }

    const printWindow = window.open('', '', 'width=1024,height=768');
    const insightsHTML = insights.map((insight, index) =>
        generateEnhancedInsightHTML(insight, index + 1)
    ).join('<div style="page-break-after: always; margin: 30px 0;"></div>');

    printWindow.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
            <title>AI Expert Insights Report - ${new Date().toLocaleDateString()}</title>
            <style>
                ${getEnhancedPrintStyles()}
            </style>
        </head>
        <body>
            ${generateEnhancedReportHeader()}
            <div class="summary-section">
                <h2 style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 28px;">📊</span>
                    <span>Executive Summary</span>
                </h2>
                <div class="summary-grid">
                    <div class="summary-card">
                        <div class="summary-value">${insights.length}</div>
                        <div class="summary-label">Total Insights</div>
                    </div>
                    <div class="summary-card critical">
                        <div class="summary-value">${insights.filter(i => i.severity === 'critical').length}</div>
                        <div class="summary-label">Critical Issues</div>
                    </div>
                    <div class="summary-card warning">
                        <div class="summary-value">${insights.filter(i => i.severity === 'warning').length}</div>
                        <div class="summary-label">Warnings</div>
                    </div>
                    <div class="summary-card info">
                        <div class="summary-value">${insights.filter(i => i.severity === 'info').length}</div>
                        <div class="summary-label">Information</div>
                    </div>
                </div>
                <div class="context-info">
                    <div class="context-row">
                        <span class="context-label">📊 Scope:</span>
                        <span class="context-value">${appState.scope.charAt(0).toUpperCase() + appState.scope.slice(1)}</span>
                    </div>
                    <div class="context-row">
                        <span class="context-label">📅 PI(s):</span>
                        <span class="context-value">${appState.selectedPIs.length > 0 ? appState.selectedPIs.join(', ') : 'All PIs'}</span>
                    </div>
                    ${appState.selectedARTs && appState.selectedARTs.length > 0 ? `
                        <div class="context-row">
                            <span class="context-label">🔄 ART(s):</span>
                            <span class="context-value">${appState.selectedARTs.join(', ')}</span>
                        </div>
                    ` : ''}
                    <div class="context-row">
                        <span class="context-label">🕐 Generated:</span>
                        <span class="context-value">${new Date().toLocaleString()}</span>
                    </div>
                </div>
            </div>
            <div style="page-break-after: always;"></div>
            ${insightsHTML}
            ${generateReportFooter()}
        </body>
        </html>
    `);

    printWindow.document.close();
    printWindow.focus();
    setTimeout(() => {
        printWindow.print();
        printWindow.close();
    }, 250);

    updateStatusBar(`Complete insights report prepared for printing (${insights.length} insights)`);
}

// Generate HTML for a single insight (legacy version)
function generateInsightHTML(insight, number) {
    return generateEnhancedInsightHTML(insight, number);
}

// Generate enhanced HTML for a single insight with View Full Details styling
function generateEnhancedInsightHTML(insight, number) {
    const severityColors = {
        'critical': '#FF3B30',
        'warning': '#FF9500',
        'info': '#34C759'
    };
    const color = severityColors[insight.severity] || '#667eea';
    const confidence = Math.round((insight.confidence || 0) * 100);
    const actions = insight.recommended_actions || [];
    const rootCauses = insight.root_causes || [];
    const expectedOutcomes = insight.expected_outcomes || {};
    const evidence = insight.evidence || [];
    const metricRefs = insight.metric_references || [];

    return `
        <div class="insight-section">
            <div class="insight-header" style="border-left-color: ${color};">
                <div class="insight-title-group">
                    <div class="insight-number">#${number}</div>
                    <h2 style="color: ${color};">${insight.title}</h2>
                </div>
                <span class="severity-badge" style="background: ${color};">${insight.severity.toUpperCase()}</span>
            </div>
            
            <div class="metadata">
                <div class="meta-item">
                    <span class="meta-icon">🎯</span>
                    <span class="meta-label">Confidence:</span>
                    <span class="meta-value">${confidence}%</span>
                </div>
                <div class="meta-item">
                    <span class="meta-icon">📊</span>
                    <span class="meta-label">Scope:</span>
                    <span class="meta-value">${insight.scope || 'Portfolio'}</span>
                </div>
                ${insight.scope_id ? `
                    <div class="meta-item">
                        <span class="meta-icon">🔖</span>
                        <span class="meta-label">ID:</span>
                        <span class="meta-value">${insight.scope_id}</span>
                    </div>
                ` : ''}
            </div>
            
            ${insight.observation ? `
                <div class="section observation-section">
                    <h3><span class="section-icon">📋</span> Observation</h3>
                    <div class="section-content">${insight.observation}</div>
                </div>
            ` : ''}
            
            ${insight.interpretation ? `
                <div class="section interpretation-section">
                    <h3><span class="section-icon">💭</span> Interpretation</h3>
                    <div class="section-content">${insight.interpretation}</div>
                </div>
            ` : ''}
            
            ${rootCauses.length > 0 ? `
                <div class="section root-causes-section">
                    <h3><span class="section-icon">🔍</span> Root Causes</h3>
                    <ul class="fancy-list">
                        ${rootCauses.map(rc => `
                            <li class="fancy-list-item">
                                <div class="cause-header">
                                    <strong>${rc.description}</strong>
                                    ${rc.confidence ? `<span class="confidence-badge">${Math.round(rc.confidence * 100)}% confidence</span>` : ''}
                                </div>
                                ${rc.evidence && rc.evidence.length > 0 ? `
                                    <ul class="evidence-list">
                                        ${rc.evidence.map(e => `<li class="evidence-item">${e}</li>`).join('')}
                                    </ul>
                                ` : ''}
                                ${rc.reference ? `<div class="reference">📎 Reference: ${rc.reference}</div>` : ''}
                            </li>
                        `).join('')}
                    </ul>
                </div>
            ` : ''}
            
            ${actions.length > 0 ? `
                <div class="section actions-section">
                    <h3><span class="section-icon">✅</span> Recommended Actions</h3>
                    <ol class="actions-list">
                        ${actions.map(action => `
                            <li class="action-item">
                                <div class="action-header">
                                    <span class="timeframe-badge timeframe-${action.timeframe}">[${action.timeframe.replace('_', ' ').toUpperCase()}]</span>
                                    <span class="action-description">${action.description}</span>
                                </div>
                                <div class="action-details">
                                    <div class="action-detail">
                                        <span class="detail-icon">👤</span>
                                        <span class="detail-label">Owner:</span>
                                        <span class="detail-value">${action.owner || 'TBD'}</span>
                                    </div>
                                    ${action.effort ? `
                                        <div class="action-detail">
                                            <span class="detail-icon">⏱️</span>
                                            <span class="detail-label">Effort:</span>
                                            <span class="detail-value">${action.effort}</span>
                                        </div>
                                    ` : ''}
                                    ${action.success_signal ? `
                                        <div class="action-detail">
                                            <span class="detail-icon">🎯</span>
                                            <span class="detail-label">Success Signal:</span>
                                            <span class="detail-value">${action.success_signal}</span>
                                        </div>
                                    ` : ''}
                                    ${action.dependencies && action.dependencies.length ? `
                                        <div class="action-detail">
                                            <span class="detail-icon">🔗</span>
                                            <span class="detail-label">Dependencies:</span>
                                            <span class="detail-value">${action.dependencies.join(', ')}</span>
                                        </div>
                                    ` : ''}
                                </div>
                            </li>
                        `).join('')}
                    </ol>
                </div>
            ` : ''}
            
            ${(expectedOutcomes.timeline || (expectedOutcomes.metrics_to_watch && expectedOutcomes.metrics_to_watch.length)) ? `
                <div class="section outcomes-section">
                    <h3><span class="section-icon">📊</span> Expected Outcomes</h3>
                    <div class="outcomes-grid">
                        ${expectedOutcomes.timeline ? `
                            <div class="outcome-item">
                                <div class="outcome-icon">⏱️</div>
                                <div class="outcome-content">
                                    <div class="outcome-label">Timeline</div>
                                    <div class="outcome-value">${expectedOutcomes.timeline}</div>
                                </div>
                            </div>
                        ` : ''}
                        ${expectedOutcomes.metrics_to_watch && expectedOutcomes.metrics_to_watch.length > 0 ? `
                            <div class="outcome-item">
                                <div class="outcome-icon">📈</div>
                                <div class="outcome-content">
                                    <div class="outcome-label">Metrics to Watch</div>
                                    <div class="outcome-value">${expectedOutcomes.metrics_to_watch.join(', ')}</div>
                                </div>
                            </div>
                        ` : ''}
                        ${expectedOutcomes.leading_indicators && expectedOutcomes.leading_indicators.length > 0 ? `
                            <div class="outcome-item">
                                <div class="outcome-icon">⚡</div>
                                <div class="outcome-content">
                                    <div class="outcome-label">Leading Indicators</div>
                                    <div class="outcome-value">${expectedOutcomes.leading_indicators.join(', ')}</div>
                                </div>
                            </div>
                        ` : ''}
                        ${expectedOutcomes.lagging_indicators && expectedOutcomes.lagging_indicators.length > 0 ? `
                            <div class="outcome-item">
                                <div class="outcome-icon">📉</div>
                                <div class="outcome-content">
                                    <div class="outcome-label">Lagging Indicators</div>
                                    <div class="outcome-value">${expectedOutcomes.lagging_indicators.join(', ')}</div>
                                </div>
                            </div>
                        ` : ''}
                        ${expectedOutcomes.risks && expectedOutcomes.risks.length > 0 ? `
                            <div class="outcome-item">
                                <div class="outcome-icon">⚠️</div>
                                <div class="outcome-content">
                                    <div class="outcome-label">Risks</div>
                                    <div class="outcome-value">${expectedOutcomes.risks.join(', ')}</div>
                                </div>
                            </div>
                        ` : ''}
                    </div>
                </div>
            ` : ''}

            ${metricRefs.length > 0 ? `
                <div class="section references-section">
                    <h3><span class="section-icon">🔗</span> Metric References</h3>
                    <div class="references-list">
                        ${metricRefs.map(ref => `<div class="reference-item">${ref}</div>`).join('')}
                    </div>
                </div>
            ` : ''}

            ${evidence.length > 0 ? `
                <div class="section evidence-section">
                    <h3><span class="section-icon">🧾</span> Evidence</h3>
                    <ul class="evidence-main-list">
                        ${evidence.map(ev => `<li class="evidence-main-item">${ev}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
        </div>
    `;
}

// Generate enhanced report header with modern styling
function generateEnhancedReportHeader() {
    const now = new Date();
    return `
        <div class="report-header">
            <div class="header-content">
                <div class="header-logo">
                    <div class="logo-icon">🎯</div>
                    <div class="logo-text">
                        <h1>AI Expert Insights Report</h1>
                        <div class="subtitle">Evaluation Coach - Agile & SAFe Analytics Platform</div>
                    </div>
                </div>
                <div class="header-meta">
                    <div class="meta-badge">
                        <span class="badge-icon">📅</span>
                        <span class="badge-text">${now.toLocaleDateString()}</span>
                    </div>
                    <div class="meta-badge">
                        <span class="badge-icon">🕐</span>
                        <span class="badge-text">${now.toLocaleTimeString()}</span>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Generate report header (legacy version)
function generateReportHeader() {
    return generateEnhancedReportHeader();
}

// Generate report footer
function generateReportFooter() {
    return `
        <div class="report-footer">
            <p>This report was generated by Evaluation Coach - AI-Powered Agile & SAFe Analytics Platform</p>
            <p>© ${new Date().getFullYear()} - Confidential</p>
        </div>
    `;
}

// Get enhanced print-specific CSS styles with View Full Details look
function getEnhancedPrintStyles() {
    return `
        @media print {
            @page {
                size: A4;
                margin: 15mm;
            }
            .insight-section {
                page-break-inside: avoid;
            }
        }
        
        * {
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica', 'Arial', sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 210mm;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f7;
        }
        
        .report-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
        }
        
        .header-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 20px;
        }
        
        .header-logo {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .logo-icon {
            font-size: 48px;
            line-height: 1;
        }
        
        .logo-text h1 {
            margin: 0;
            font-size: 32px;
            font-weight: 700;
            letter-spacing: -0.5px;
        }
        
        .subtitle {
            font-size: 14px;
            opacity: 0.9;
            margin-top: 4px;
        }
        
        .header-meta {
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
        }
        
        .meta-badge {
            background: rgba(255, 255, 255, 0.2);
            backdrop-filter: blur(10px);
            padding: 8px 16px;
            border-radius: 20px;
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 13px;
            font-weight: 500;
        }
        
        .badge-icon {
            font-size: 16px;
        }
        
        .summary-section {
            background: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
        }
        
        .summary-section h2 {
            margin: 0 0 24px 0;
            color: #667eea;
            font-size: 24px;
            font-weight: 700;
        }
        
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }
        
        .summary-card {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            border: 2px solid #e0e0e0;
        }
        
        .summary-card.critical {
            background: linear-gradient(135deg, #FFE5E5 0%, #FFCCCC 100%);
            border-color: #FF3B30;
        }
        
        .summary-card.warning {
            background: linear-gradient(135deg, #FFF4E5 0%, #FFE5CC 100%);
            border-color: #FF9500;
        }
        
        .summary-card.info {
            background: linear-gradient(135deg, #E5F9F0 0%, #CCF2E0 100%);
            border-color: #34C759;
        }
        
        .summary-value {
            font-size: 36px;
            font-weight: 700;
            margin-bottom: 8px;
            line-height: 1;
        }
        
        .summary-label {
            font-size: 13px;
            color: #666;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .context-info {
            background: #f8f9fa;
            padding: 16px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        
        .context-row {
            display: flex;
            align-items: center;
            padding: 6px 0;
            gap: 10px;
        }
        
        .context-label {
            font-weight: 600;
            color: #666;
            min-width: 100px;
        }
        
        .context-value {
            color: #333;
        }
        
        .insight-section {
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
            border: 2px solid #e0e0e0;
        }
        
        .insight-header {
            border-left: 6px solid;
            padding-left: 20px;
            margin-bottom: 24px;
            display: flex;
            justify-content: space-between;
            align-items: start;
            gap: 16px;
        }
        
        .insight-title-group {
            display: flex;
            align-items: baseline;
            gap: 12px;
            flex: 1;
        }
        
        .insight-number {
            background: #667eea;
            color: white;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 18px;
            flex-shrink: 0;
        }
        
        .insight-header h2 {
            margin: 0;
            font-size: 22px;
            font-weight: 700;
            line-height: 1.3;
        }
        
        .severity-badge {
            color: white;
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.5px;
            white-space: nowrap;
            flex-shrink: 0;
        }
        
        .metadata {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            margin-bottom: 24px;
            padding-bottom: 16px;
            border-bottom: 2px solid #f0f0f0;
        }
        
        .meta-item {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 14px;
        }
        
        .meta-icon {
            font-size: 16px;
        }
        
        .meta-label {
            color: #888;
        }
        
        .meta-value {
            color: #333;
            font-weight: 600;
        }
        
        .section {
            margin-bottom: 28px;
        }
        
        .section h3 {
            color: #667eea;
            font-size: 18px;
            font-weight: 700;
            margin: 0 0 16px 0;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .section-icon {
            font-size: 20px;
        }
        
        .section-content {
            color: #333;
            line-height: 1.7;
            white-space: pre-wrap;
            background: #f8f9fa;
            padding: 16px;
            border-radius: 8px;
            border-left: 3px solid #667eea;
        }
        
        .observation-section .section-content {
            background: #E3F2FD;
            border-left-color: #2196F3;
        }
        
        .interpretation-section .section-content {
            background: #F3E5F5;
            border-left-color: #9C27B0;
        }
        
        .fancy-list {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        
        .fancy-list-item {
            background: #f8f9fa;
            padding: 16px;
            margin-bottom: 12px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        
        .cause-header {
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 8px;
            gap: 12px;
        }
        
        .confidence-badge {
            background: #667eea;
            color: white;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            white-space: nowrap;
        }
        
        .evidence-list {
            list-style: none;
            padding: 0;
            margin: 12px 0 0 0;
        }
        
        .evidence-item {
            color: #666;
            font-size: 14px;
            padding: 8px 12px;
            background: white;
            margin: 6px 0;
            border-radius: 4px;
            border-left: 2px solid #ccc;
        }
        
        .evidence-item:before {
            content: "▸";
            color: #667eea;
            margin-right: 8px;
            font-weight: bold;
        }
        
        .reference {
            color: #888;
            font-size: 12px;
            margin-top: 8px;
            font-style: italic;
        }
        
        .actions-section {
            background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
            padding: 20px;
            border-radius: 10px;
            border: 2px solid #4CAF50;
        }
        
        .actions-section h3 {
            color: #2E7D32;
        }
        
        .actions-list {
            list-style: none;
            counter-reset: action-counter;
            padding: 0;
            margin: 0;
        }
        
        .action-item {
            counter-increment: action-counter;
            background: white;
            padding: 16px;
            margin-bottom: 14px;
            border-radius: 8px;
            box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
        }
        
        .action-item:before {
            content: counter(action-counter);
            background: #4CAF50;
            color: white;
            width: 28px;
            height: 28px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            margin-right: 12px;
            font-size: 14px;
            float: left;
        }
        
        .action-header {
            display: flex;
            align-items: start;
            gap: 10px;
            margin-bottom: 12px;
        }
        
        .timeframe-badge {
            background: #FFC107;
            color: #000;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 700;
            white-space: nowrap;
            text-transform: uppercase;
            flex-shrink: 0;
        }
        
        .timeframe-immediate {
            background: #F44336;
            color: white;
        }
        
        .timeframe-short_term {
            background: #FF9800;
            color: white;
        }
        
        .timeframe-long_term {
            background: #2196F3;
            color: white;
        }
        
        .action-description {
            flex: 1;
            line-height: 1.5;
        }
        
        .action-details {
            background: #f8f9fa;
            padding: 12px;
            border-radius: 6px;
            margin-left: 40px;
        }
        
        .action-detail {
            display: flex;
            align-items: start;
            gap: 6px;
            margin: 6px 0;
            font-size: 13px;
        }
        
        .detail-icon {
            font-size: 14px;
            margin-top: 2px;
        }
        
        .detail-label {
            color: #666;
            font-weight: 600;
            min-width: 80px;
        }
        
        .detail-value {
            color: #333;
            flex: 1;
        }
        
        .outcomes-section {
            background: linear-gradient(135deg, #FFF9C4 0%, #FFF59D 100%);
            padding: 20px;
            border-radius: 10px;
            border: 2px solid #FBC02D;
        }
        
        .outcomes-section h3 {
            color: #F57F17;
        }
        
        .outcomes-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 14px;
        }
        
        .outcome-item {
            background: white;
            padding: 16px;
            border-radius: 8px;
            display: flex;
            align-items: start;
            gap: 12px;
            box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
        }
        
        .outcome-icon {
            font-size: 24px;
            flex-shrink: 0;
        }
        
        .outcome-content {
            flex: 1;
        }
        
        .outcome-label {
            font-size: 12px;
            color: #666;
            font-weight: 600;
            margin-bottom: 4px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .outcome-value {
            color: #333;
            font-size: 14px;
            line-height: 1.4;
        }
        
        .references-section, .evidence-section {
            background: #F5F5F5;
            padding: 16px;
            border-radius: 8px;
        }
        
        .references-list {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        
        .reference-item {
            background: white;
            padding: 10px 14px;
            border-radius: 6px;
            font-size: 13px;
            color: #666;
            border-left: 3px solid #667eea;
        }
        
        .evidence-main-list {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        
        .evidence-main-item {
            background: white;
            padding: 12px 16px;
            margin: 8px 0;
            border-radius: 6px;
            border-left: 3px solid #667eea;
            font-size: 14px;
            line-height: 1.6;
        }
        
        .evidence-main-item:before {
            content: "✓";
            color: #4CAF50;
            margin-right: 10px;
            font-weight: bold;
        }
        
        .report-footer {
            margin-top: 50px;
            padding: 30px 20px;
            border-top: 3px solid #667eea;
            text-align: center;
            background: white;
            border-radius: 12px;
        }
        
        .report-footer p {
            margin: 8px 0;
            color: #666;
            font-size: 13px;
        }
        
        .report-footer p:first-child {
            font-weight: 600;
            color: #333;
            font-size: 14px;
        }
    `;
}

// Get print-specific CSS styles (legacy version)
function getPrintStyles() {
    return getEnhancedPrintStyles();
}
@media print {
    @page {
        size: A4;
        margin: 15mm;
    }
}
        
        body {
    font - family: -apple - system, BlinkMacSystemFont, 'Segoe UI', system - ui, sans - serif;
    line - height: 1.6;
    color: #333;
    max - width: 210mm;
    margin: 0 auto;
    padding: 20px;
    background: white;
}
        
        .report - header {
    border - bottom: 3px solid #667eea;
    padding - bottom: 20px;
    margin - bottom: 30px;
}
        
        .report - header h1 {
    color: #667eea;
    margin: 0 0 10px 0;
    font - size: 28px;
}
        
        .report - meta {
    display: flex;
    justify - content: space - between;
    font - size: 12px;
    color: #666;
}
        
        .summary - section {
    background: #f8f9fa;
    padding: 20px;
    border - radius: 8px;
    margin - bottom: 30px;
}
        
        .summary - section h2 {
    margin - top: 0;
    color: #667eea;
}
        
        .summary - section p {
    margin: 8px 0;
}
        
        .insight - section {
    margin - bottom: 40px;
    page -break-inside: avoid;
}
        
        .insight - header {
    border - left: 4px solid;
    padding - left: 16px;
    margin - bottom: 16px;
    display: flex;
    justify - content: space - between;
    align - items: start;
}
        
        .insight - header h2 {
    margin: 0;
    font - size: 20px;
}
        
        .severity - badge {
    color: white;
    padding: 4px 12px;
    border - radius: 4px;
    font - size: 11px;
    font - weight: 600;
    white - space: nowrap;
}
        
        .metadata {
    color: #666;
    font - size: 13px;
    margin - bottom: 20px;
    padding - bottom: 10px;
    border - bottom: 1px solid #eee;
}
        
        .section {
    margin - bottom: 20px;
}
        
        .section h3 {
    color: #667eea;
    font - size: 16px;
    margin: 0 0 10px 0;
}
        
        .section p {
    margin: 8px 0;
}
        
        .section ul, .section ol {
    padding - left: 24px;
    margin: 8px 0;
}
        
        .section li {
    margin - bottom: 12px;
}
        
        .evidence - list {
    margin - top: 8px;
    font - size: 13px;
    color: #666;
}
        
        .evidence - list li {
    margin - bottom: 4px;
}
        
        .actions - section {
    background: #e8f5e9;
    padding: 15px;
    border - radius: 6px;
}
        
        .action - details {
    margin - top: 8px;
    padding - left: 16px;
    font - size: 13px;
    color: #666;
}
        
        .action - details div {
    margin: 4px 0;
}
        
        .outcomes - section {
    background: #fff9e6;
    padding: 15px;
    border - radius: 6px;
}
        
        .report - footer {
    margin - top: 40px;
    padding - top: 20px;
    border - top: 2px solid #eee;
    text - align: center;
    font - size: 11px;
    color: #999;
}
        
        .report - footer p {
    margin: 4px 0;
}
`;
}

// Add message to chat
function addMessage(message) {
    const messagesContainer = document.getElementById('chatMessages');

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${ message.type } `;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = message.content;

    messageDiv.appendChild(contentDiv);
    messagesContainer.appendChild(messageDiv);

    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    appState.messages.push(message);
}

// Generate AI response based on user input
function generateAIResponse(input) {
    const lowerInput = input.toLowerCase();

    // Keyword-based responses
    if (lowerInput.includes('wip') || lowerInput.includes('work in progress')) {
        return `📊 <strong>Work in Progress Analysis</strong><br><br>
            Current WIP across your ${appState.scope}:<br>
            • Average WIP ratio: 1.3x team size<br>
            • Target: ≤1.5x<br>
            • Status: <span style="color: #34C759;">✓ Healthy</span><br><br>
            However, Customer Experience ART shows 2.3x ratio, which requires attention. 
            Would you like me to generate specific recommendations for this ART?`;
    }

    if (lowerInput.includes('flow') || lowerInput.includes('efficiency')) {
        return `📈 <strong>Flow Efficiency Insights</strong><br><br>
            Your current flow efficiency: <strong>67%</strong><br>
            • Industry average: 15%<br>
            • High performer benchmark: 40%<br>
            • Your status: <span style="color: #34C759;">✓ Excellent!</span><br><br>
            You're significantly above high performer benchmarks. Main drivers:<br>
            • Reduced blocked time (28% decrease)<br>
            • Better dependency management<br>
            • Cross-team collaboration improvements<br><br>
            Platform Engineering ART is leading at 72%. Want to see their best practices?`;
    }

    if (lowerInput.includes('quality') || lowerInput.includes('defect')) {
        return `✅ <strong>Quality Metrics Overview</strong><br><br>
            Defect Escape Rate: <strong>4.2%</strong><br>
            • Target: <5%<br>
            • Status: <span style="color: #34C759;">✓ Acceptable</span><br><br>
            <span style="color: #FF9500;">⚠️ Warning:</span> Mobile Apps team at 7.2% with 68% stories lacking test coverage.<br><br>
            Recommendations:<br>
            1. Implement Definition of Done checklist<br>
            2. Set 80% test coverage target<br>
            3. Add automated testing pipeline<br><br>
            Would you like detailed analysis for Mobile Apps team?`;
    }

    if (lowerInput.includes('team') || lowerInput.includes('stability')) {
        return `👥 <strong>Team Stability Analysis</strong><br><br>
            Overall team stability: <strong>89%</strong><br>
            • Industry target: >85%<br>
            • Status: <span style="color: #34C759;">✓ Excellent</span><br><br>
            All ARTs show stable team composition with minimal turnover. 
            This is a key enabler for your strong flow efficiency results.<br><br>
            Want to see team-specific breakdowns?`;
    }

    if (lowerInput.includes('scorecard') || lowerInput.includes('health')) {
        return `📋 <strong>Health Scorecard Request</strong><br><br>
            I can generate a comprehensive scorecard for:<br>
            • Portfolio (all ARTs)<br>
            • Specific ART<br>
            • Individual Team<br><br>
            Your current context: <strong>${capitalizeFirst(appState.scope)}</strong><br><br>
            Use the <strong>"Generate Scorecard"</strong> button in the sidebar, or tell me which scope you'd like to analyze!`;
    }

    if (lowerInput.includes('improve') || lowerInput.includes('recommendation')) {
        return `💡 <strong>Improvement Recommendations</strong><br><br>
            Based on your current metrics, top 3 priorities:<br><br>
            <strong>1. Address High WIP (Critical)</strong><br>
            Customer Experience ART needs immediate WIP limit enforcement.<br><br>
            <strong>2. Improve Test Coverage (Warning)</strong><br>
            Mobile Apps team requires testing discipline improvements.<br><br>
            <strong>3. Scale Best Practices (Opportunity)</strong><br>
            Platform Engineering's success patterns can be shared across ARTs.<br><br>
            Click <strong>"Generate Insights"</strong> for detailed action plans!`;
    }

    // Default response
    return `🤔 <strong>I can help you with:</strong><br><br>
        • <strong>Metrics analysis</strong> - Ask about flow, quality, predictability, or WIP<br>
        • <strong>Scorecards</strong> - Generate health assessments for Portfolio/ART/Team<br>
        • <strong>Insights</strong> - Get evidence-based recommendations<br>
        • <strong>Trends</strong> - Understand changes over time<br>
        • <strong>Best practices</strong> - Learn from high-performing teams<br><br>
        Try asking: "What's our flow efficiency?" or "Show me quality metrics"`;
}

// Insight actions
function acceptInsight(id) {
    updateStatusBar(`Insight #${id} accepted and added to action tracker`);
    alert(`✓ Insight #${id} Accepted\n\nThis insight has been added to your action tracker. You'll be notified about progress and outcomes.\n\n(Demo mode - actual tracking requires backend integration)`);
}

function viewDetails(id) {
    updateStatusBar(`Opening detailed view for insight #${id}`);
    alert(`📋 Detailed Analysis - Insight #${id}\n\nThis would open a comprehensive view showing:\n\n• Full metric breakdown\n• Historical trend analysis\n• Evidence sources (Jira issues, sprint data)\n• Similar patterns in knowledge base\n• Success stories from other teams\n• Step-by-step implementation guide\n\n(Demo mode - full details require backend integration)`);
}

function dismissInsight(id) {
    if (confirm(`Are you sure you want to dismiss Insight #${id}?\n\nYou can provide optional feedback about why this insight isn't relevant.`)) {
        updateStatusBar(`Insight #${id} dismissed`);
    }
}

function shareSuccess(id) {
    updateStatusBar(`Preparing success story #${id} for sharing`);
    alert(`📤 Share Success Story\n\nThis would allow you to:\n\n• Export as presentation slides\n• Share with other ARTs via email\n• Add to organization knowledge base\n• Include in PI retrospectives\n• Post to internal communication channels\n\n(Demo mode - sharing requires backend integration)`);
}

// Metric category switching
function showMetricCategory(category) {
    // Update tab button states
    document.querySelectorAll('.action-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    event.target.classList.add('active');

    // Hide all metric categories
    const categories = ['flow', 'predictability', 'quality', 'structure'];
    categories.forEach(cat => {
        const element = document.getElementById(`${cat}Metrics`);
        if (element) {
            element.style.display = 'none';
        }
    });

    // Show selected category
    const selectedElement = document.getElementById(`${category}Metrics`);
    if (selectedElement) {
        selectedElement.style.display = 'block';
    }

    updateStatusBar(`Viewing ${category} metrics`);
}

// Load real metrics catalog
async function loadMetricsCatalog() {
    console.log('📊 Loading Metrics Catalog...');

    // Build query parameters
    const params = new URLSearchParams();
    if (appState.selectedARTs.length > 0) {
        params.append('arts', appState.selectedARTs.join(','));
    }
    if (appState.selectedPIs.length > 0) {
        params.append('pis', appState.selectedPIs.join(','));
    }

    try {
        const response = await fetch(`${API_BASE_URL}/metrics/catalog?${params.toString()}`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const metrics = await response.json();
        renderMetricsCatalog(metrics);

    } catch (error) {
        console.error('❌ Error loading metrics:', error);
        const flowMetricsDiv = document.getElementById('flowMetrics');
        if (flowMetricsDiv) {
            flowMetricsDiv.innerHTML = `
                <div style="background: #fff3cd; border: 1px solid #ffc107; border-radius: 8px; padding: 20px; text-align: center;">
                    <div style="font-size: 32px; margin-bottom: 12px;">⚠️</div>
                    <div style="font-size: 16px; font-weight: 600; margin-bottom: 8px;">Unable to Load Metrics</div>
                    <div style="font-size: 14px; color: #666;">${error.message}</div>
                </div>
            `;
        }
    }
}

// Render metrics catalog with real data
function renderMetricsCatalog(data) {
    const flowMetrics = data.flow_metrics;
    const predictabilityMetrics = data.predictability_metrics;
    const qualityMetrics = data.quality_metrics;
    const structureMetrics = data.structure_metrics;
    const scope = data.scope;

    // Helper function to get status color
    const getStatusColor = (status) => {
        switch (status) {
            case 'good': return '#34C759';
            case 'warning': return '#FF9500';
            case 'critical': return '#FF3B30';
            default: return '#667eea';
        }
    };

    // Helper function to create metric card
    const createMetricCard = (metric) => `
        <div style="background: white; border: 1px solid #e0e0e0; border-radius: 8px; padding: 20px; margin-bottom: 16px;">
            <h3 style="color: #667eea; margin-bottom: 12px;">${metric.name}</h3>
            <p style="margin-bottom: 12px; color: #555;">${metric.description}</p>
            <div style="background: #f8f9fa; padding: 12px; border-radius: 6px; margin-bottom: 12px; font-family: monospace; font-size: 13px;">
                Formula: ${metric.formula}
            </div>
            <div style="display: grid; grid-template-columns: repeat(${metric.avg_last_4_pis !== undefined ? '4' : '3'}, 1fr); gap: 12px; margin-bottom: 12px;">
                ${metric.industry_average !== undefined ? `
                <div>
                    <div style="font-size: 12px; color: #666; margin-bottom: 4px;">Industry Average</div>
                    <div style="font-size: 20px; font-weight: 600; color: #FF9500;">${metric.industry_average} ${metric.unit}</div>
                </div>
                ` : ''}
                ${metric.high_performer !== undefined ? `
                <div>
                    <div style="font-size: 12px; color: #666; margin-bottom: 4px;">High Performer</div>
                    <div style="font-size: 20px; font-weight: 600; color: #34C759;">${metric.high_performer} ${metric.unit}</div>
                </div>
                ` : ''}
                ${metric.target !== undefined && metric.industry_average === undefined ? `
                <div>
                    <div style="font-size: 12px; color: #666; margin-bottom: 4px;">Target</div>
                    <div style="font-size: 20px; font-weight: 600; color: #34C759;">${metric.target}</div>
                </div>
                ` : ''}
                ${metric.avg_last_4_pis !== undefined ? `
                <div>
                    <div style="font-size: 12px; color: #666; margin-bottom: 4px;">Avg Last 4 PIs</div>
                    <div style="font-size: 20px; font-weight: 600; color: #667eea;">${metric.avg_last_4_pis} ${metric.unit}</div>
                </div>
                ` : ''}
                <div>
                    <div style="font-size: 12px; color: #666; margin-bottom: 4px;">
                        ${appState.selectedPIs.length === 1 ? `${appState.selectedPIs[0]}` : appState.selectedPIs.length > 1 ? `Total (${appState.selectedPIs.length} PIs)` : 'Total (All PIs)'}
                    </div>
                    <div style="font-size: 20px; font-weight: 600; color: ${getStatusColor(metric.status)};">
                        ${metric.current_value} ${metric.unit}
                    </div>
                </div>
            </div>
            <div style="font-size: 13px; color: #666;">
                <strong>Jira Fields:</strong> ${(metric.jira_fields || []).map(f => `<code>${f}</code>`).join(', ')}
            </div>
            ${metric.stage_breakdown ? `
                <details style="margin-top: 12px;">
                    <summary style="cursor: pointer; color: #667eea; font-weight: 600;">View Stage Breakdown</summary>
                    <div style="margin-top: 8px; padding: 12px; background: #f8f9fa; border-radius: 6px;">
                        ${Object.entries(metric.stage_breakdown).map(([stage, stats]) => `
                            <div style="display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px solid #e0e0e0;">
                                <span style="font-weight: 600;">${stage.replace('_', ' ')}</span>
                                <span>${stats.mean} days (${stats.count} items)</span>
                            </div>
                        `).join('')}
                    </div>
                </details>
            ` : ''}
            ${metric.distribution ? `
                <details style="margin-top: 12px;">
                    <summary style="cursor: pointer; color: #667eea; font-weight: 600;">📊 View Flow Distribution</summary>
                    <div style="margin-top: 8px; padding: 12px; background: #f8f9fa; border-radius: 6px;">
                        ${Object.entries(metric.distribution).map(([type, percentage]) => `
                            <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #e0e0e0;">
                                <span style="font-weight: 600;">${type}</span>
                                <div>
                                    <span style="font-size: 20px; font-weight: 700; color: #667eea;">${percentage}%</span>
                                    <div style="width: 200px; height: 8px; background: #e0e0e0; border-radius: 4px; margin-top: 4px; overflow: hidden;">
                                        <div style="width: ${percentage}%; height: 100%; background: #667eea;"></div>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </details>
            ` : ''}
            ${metric.median !== undefined && metric.p85 !== undefined ? `
                <div style="margin-top: 12px; padding: 12px; background: #e7f3ff; border-radius: 6px;">
                    <div style="font-weight: 600; color: #667eea; margin-bottom: 8px;">📈 Statistical Distribution</div>
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px;">
                        <div>
                            <div style="font-size: 11px; color: #666; margin-bottom: 4px;">Median (P50)</div>
                            <div style="font-size: 18px; font-weight: 600;">${metric.median} ${metric.unit}</div>
                        </div>
                        <div>
                            <div style="font-size: 11px; color: #666; margin-bottom: 4px;">85th Percentile</div>
                            <div style="font-size: 18px; font-weight: 600;">${metric.p85} ${metric.unit}</div>
                        </div>
                        <div>
                            <div style="font-size: 11px; color: #666; margin-bottom: 4px;">Mean (Average)</div>
                            <div style="font-size: 18px; font-weight: 600;">${metric.mean} ${metric.unit}</div>
                        </div>
                    </div>
                </div>
            ` : ''}

            ${(metric.min !== undefined || metric.max !== undefined || metric.avg !== undefined) ? `
                <div style="margin-top: 12px; padding: 12px; background: #f0f4ff; border-radius: 6px;">
                    <div style="font-weight: 600; color: #667eea; margin-bottom: 8px;">📏 Distribution Summary</div>
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px;">
                        <div>
                            <div style="font-size: 11px; color: #666; margin-bottom: 4px;">Min</div>
                            <div style="font-size: 18px; font-weight: 600;">${metric.min !== undefined ? metric.min : '-'} ${metric.unit || ''}</div>
                        </div>
                        <div>
                            <div style="font-size: 11px; color: #666; margin-bottom: 4px;">Avg</div>
                            <div style="font-size: 18px; font-weight: 600;">${metric.avg !== undefined ? metric.avg : '-'} ${metric.unit || ''}</div>
                        </div>
                        <div>
                            <div style="font-size: 11px; color: #666; margin-bottom: 4px;">Max</div>
                            <div style="font-size: 18px; font-weight: 600;">${metric.max !== undefined ? metric.max : '-'} ${metric.unit || ''}</div>
                        </div>
                    </div>
                </div>
            ` : ''}
            ${metric.active_time !== undefined && metric.wait_time !== undefined ? `
                <div style="margin-top: 12px; padding: 12px; background: #fff3cd; border-radius: 6px;">
                    <div style="font-weight: 600; color: #856404; margin-bottom: 8px;">⏱️ Time Breakdown</div>
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px;">
                        <div>
                            <div style="font-size: 11px; color: #666; margin-bottom: 4px;">🟢 Active Work Time</div>
                            <div style="font-size: 18px; font-weight: 600;">${metric.active_time} days</div>
                        </div>
                        <div>
                            <div style="font-size: 11px; color: #666; margin-bottom: 4px;">🔴 Wait/Queue Time</div>
                            <div style="font-size: 18px; font-weight: 600;">${metric.wait_time} days</div>
                        </div>
                    </div>
                </div>
            ` : ''}
            ${metric.breakdown_by_stage ? `
                <details style="margin-top: 12px;">
                    <summary style="cursor: pointer; color: #667eea; font-weight: 600;">View WIP by Stage</summary>
                    <div style="margin-top: 8px; padding: 12px; background: #f8f9fa; border-radius: 6px;">
                        ${Object.entries(metric.breakdown_by_stage).map(([stage, count]) => `
                            <div style="display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px solid #e0e0e0;">
                                <span style="font-weight: 600;">${stage.replace('_', ' ')}</span>
                                <span>${count} items</span>
                            </div>
                        `).join('')}
                    </div>
                </details>
            ` : ''}
            ${metric.breakdown ? `
                <details style="margin-top: 12px;">
                    <summary style="cursor: pointer; color: #667eea; font-weight: 600;">View Waste Breakdown</summary>
                    <div style="margin-top: 8px; padding: 12px; background: #f8f9fa; border-radius: 6px;">
                        ${metric.breakdown.waiting_time ? `
                            <div style="margin-bottom: 12px;">
                                <div style="font-weight: 600; color: #667eea; margin-bottom: 8px;">⏱️ Waiting Time Waste</div>
                                ${Object.entries(metric.breakdown.waiting_time).map(([stage, days]) => `
                                    <div style="display: flex; justify-content: space-between; padding: 4px 0; padding-left: 16px; border-bottom: 1px solid #e0e0e0;">
                                        <span>${stage.replace('_', ' ')}</span>
                                        <span style="font-weight: 600; color: #FF9500;">${days.toFixed(1)} days</span>
                                    </div>
                                `).join('')}
                            </div>
                        ` : ''}
                        ${metric.breakdown.removed_work ? `
                            <div>
                                <div style="font-weight: 600; color: #667eea; margin-bottom: 8px;">🗑️ Removed Work</div>
                                ${Object.entries(metric.breakdown.removed_work).map(([type, count]) => `
                                    <div style="display: flex; justify-content: space-between; padding: 4px 0; padding-left: 16px; border-bottom: 1px solid #e0e0e0;">
                                        <span>${type.charAt(0).toUpperCase() + type.slice(1)}</span>
                                        <span style="font-weight: 600; color: #FF3B30;">${count} items</span>
                                    </div>
                                `).join('')}
                            </div>
                        ` : ''}
                    </div>
                </details>
            ` : ''}

            ${metric.breakdown_kv && Object.keys(metric.breakdown_kv).length ? `
                <details style="margin-top: 12px;">
                    <summary style="cursor: pointer; color: #667eea; font-weight: 600;">View Breakdown</summary>
                    <div style="margin-top: 8px; padding: 12px; background: #f8f9fa; border-radius: 6px;">
                        ${Object.entries(metric.breakdown_kv).map(([k, v]) => `
                            <div style="display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid #e0e0e0;">
                                <span style="font-weight: 600;">${k}</span>
                                <span>${v}</span>
                            </div>
                        `).join('')}
                    </div>
                </details>
            ` : ''}
            ${metric.trend_by_pi ? `
                <details style="margin-top: 12px;">
                    <summary style="cursor: pointer; color: #667eea; font-weight: 600;">View Throughput by PI</summary>
                    <div style="margin-top: 8px; padding: 12px; background: #f8f9fa; border-radius: 6px;">
                        ${metric.avg_last_4_pis !== undefined && metric.avg_last_4_pis > 0 ? `
                        <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 2px solid #667eea; background: #e7f3ff; margin: -12px -12px 8px -12px; padding: 12px;">
                            <span style="font-weight: 700; color: #667eea;">Avg Last 4 PIs</span>
                            <span style="font-weight: 700; color: #667eea;">${metric.avg_last_4_pis} ${metric.unit}</span>
                        </div>
                        ` : ''}
                        ${metric.prev_4_pis_data && Object.keys(metric.prev_4_pis_data).length > 0 ?
                Object.entries(metric.prev_4_pis_data).map(([pi, stats]) => `
                                <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #e0e0e0; background: #f0f4ff;">
                                    <span style="font-weight: 600; color: #667eea;">${pi}</span>
                                    <span style="color: #667eea;">${stats.throughput} features (${stats.avg_leadtime.toFixed(1)} days avg)</span>
                                </div>
                            `).join('') : ''
            }
                        ${Object.entries(metric.trend_by_pi).map(([pi, stats]) => `
                            <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #e0e0e0;">
                                <span style="font-weight: 600;">${pi}</span>
                                <span>${stats.throughput} features (${stats.avg_leadtime.toFixed(1)} days avg)</span>
                            </div>
                        `).join('')}
                    </div>
                </details>
            ` : ''}
        </div>
    `;

    // Update Flow Metrics
    const flowMetricsDiv = document.getElementById('flowMetrics');
    if (flowMetricsDiv && flowMetrics) {
        flowMetricsDiv.innerHTML = `
            <div style="background: #e7f3ff; border-left: 4px solid #667eea; padding: 12px; margin-bottom: 20px; border-radius: 4px;">
                <strong>📊 SAFe Flow Metrics for:</strong> ${scope.arts.join(', ')} | ${scope.pis.join(', ')}
            </div>
            ${flowMetrics.flow_time ? createMetricCard(flowMetrics.flow_time) : ''}
            ${flowMetrics.flow_efficiency ? createMetricCard(flowMetrics.flow_efficiency) : ''}
            ${flowMetrics.flow_distribution ? createMetricCard(flowMetrics.flow_distribution) : ''}
            ${flowMetrics.flow_load ? createMetricCard(flowMetrics.flow_load) : ''}
            ${flowMetrics.flow_velocity ? createMetricCard(flowMetrics.flow_velocity) : ''}
            ${flowMetrics.waste ? createMetricCard(flowMetrics.waste) : ''}
        `;
    }

    // Update Predictability Metrics
    const predictabilityMetricsDiv = document.getElementById('predictabilityMetrics');
    if (predictabilityMetricsDiv && predictabilityMetrics) {
        predictabilityMetricsDiv.innerHTML = `
            ${createMetricCard(predictabilityMetrics.planning_accuracy)}
            ${createMetricCard(predictabilityMetrics.velocity_stability)}
        `;
    }

    // Update Quality Metrics
    const qualityMetricsDiv = document.getElementById('qualityMetrics');
    if (qualityMetricsDiv && qualityMetrics) {
        qualityMetricsDiv.innerHTML = `
            ${createMetricCard(qualityMetrics.defect_rate)}
        `;
    }

    // Update Structure Metrics
    const structureMetricsDiv = document.getElementById('structureMetrics');
    if (structureMetricsDiv && structureMetrics) {
        structureMetricsDiv.innerHTML = `
            <div style="background: #f0f4ff; border-left: 4px solid #667eea; padding: 12px; margin-bottom: 20px; border-radius: 4px;">
                <strong>🏗️ Structure Metrics for:</strong> ${scope.arts.join(', ')} | ${scope.pis.join(', ')}
            </div>
            ${structureMetrics.art_count ? createMetricCard(structureMetrics.art_count) : ''}
            ${structureMetrics.team_count ? createMetricCard(structureMetrics.team_count) : ''}
            ${structureMetrics.teams_per_art ? createMetricCard(structureMetrics.teams_per_art) : ''}
            ${structureMetrics.team_ownership_coverage ? createMetricCard(structureMetrics.team_ownership_coverage) : ''}
            ${structureMetrics.delivery_concentration ? createMetricCard(structureMetrics.delivery_concentration) : ''}
        `;
    }

    updateStatusBar(`Metrics updated for ${scope.arts.join(', ')} | ${scope.pis.join(', ')}`);
}


// Update status bar
function updateStatusBar(message) {
    const statusText = document.getElementById('statusText');
    const now = new Date().toLocaleTimeString();
    statusText.textContent = `${message} | Last updated: ${now} | Data source: Jira Cloud`;
}

// Utility function
function capitalizeFirst(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

// Handle ART selection change
document.addEventListener('DOMContentLoaded', () => {
    const artSelector = document.getElementById('artSelector');
    if (artSelector) {
        artSelector.addEventListener('change', (e) => {
            appState.selectedART = e.target.value;
            updateContext();
            // Reload dashboard when ART is selected in ART view
            if (appState.scope === 'art') {
                loadDashboardData();
            }
        });
    }

    const teamSelector = document.getElementById('teamSelector');
    if (teamSelector) {
        teamSelector.addEventListener('change', (e) => {
            appState.selectedTeam = e.target.value;
            updateContext();
        });
    }

    const timeRange = document.getElementById('timeRange');
    if (timeRange) {
        timeRange.addEventListener('change', (e) => {
            appState.timeRange = e.target.value;
            updateContext();
        });
    }
});

// Auto-update status every 30 seconds
setInterval(() => {
    updateStatusBar('Ready');
}, 30000);

// ===========================
// Admin / Import Functions
// ===========================

let stagedData = [];
let currentEditingRow = null;

async function uploadExcelFile() {
    const fileInput = document.getElementById('excelFileInput');
    const file = fileInput.files[0];

    if (!file) {
        showImportStatus('Please select a file first', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
        updateStatusBar('Uploading file...');
        showImportStatus('Uploading and parsing Excel file...', 'info');

        const response = await fetch(`${API_BASE_URL}/v1/admin/import/upload`, {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.success) {
            showImportStatus(`✅ Successfully imported ${result.total_issues} issues! ${result.issues_with_errors} errors, ${result.issues_with_warnings} warnings.`, 'success');
            updateStatusBar(`Imported ${result.total_issues} issues for review`);

            // Load staged data
            await loadStagedData();
        } else {
            showImportStatus(`❌ Import failed: ${result.message}`, 'error');
        }
    } catch (error) {
        console.error('Upload error:', error);
        showImportStatus(`❌ Upload failed: ${error.message}`, 'error');
    }
}

function showImportStatus(message, type) {
    const statusDiv = document.getElementById('importStatus');
    statusDiv.style.display = 'block';
    statusDiv.innerHTML = message;

    const colors = {
        success: '#d4edda',
        error: '#f8d7da',
        info: '#d1ecf1',
        warning: '#fff3cd'
    };

    statusDiv.style.background = colors[type] || colors.info;
    statusDiv.style.border = `1px solid ${type === 'success' ? '#c3e6cb' : type === 'error' ? '#f5c6cb' : '#bee5eb'}`;
}

async function loadStagedData() {
    try {
        const response = await fetch(`${API_BASE_URL}/v1/admin/import/staged?limit=1000`);
        const result = await response.json();

        stagedData = result.issues;

        if (stagedData.length > 0) {
            document.getElementById('stagedDataSection').style.display = 'block';
            renderStagedIssues();
            renderStagedStats(result);
        } else {
            document.getElementById('stagedDataSection').style.display = 'none';
        }
    } catch (error) {
        console.error('Error loading staged data:', error);
    }
}

function renderStagedStats(result) {
    const statsDiv = document.getElementById('stagedDataStats');

    const validCount = stagedData.filter(issue => issue.validation_errors.length === 0).length;
    const errorCount = stagedData.filter(issue => issue.validation_errors.length > 0).length;
    const warningCount = stagedData.filter(issue => issue.validation_warnings.length > 0).length;

    statsDiv.innerHTML = `
        <div style="display: flex; gap: 24px; align-items: center;">
            <div>
                <strong>Total:</strong> ${result.total} issues
            </div>
            <div style="color: #34C759;">
                <strong>✅ Valid:</strong> ${validCount}
            </div>
            <div style="color: #FF3B30;">
                <strong>❌ Errors:</strong> ${errorCount}
            </div>
            <div style="color: #FF9500;">
                <strong>⚠️ Warnings:</strong> ${warningCount}
            </div>
        </div>
    `;
}

function renderStagedIssues() {
    const tbody = document.getElementById('stagedIssuesTable');
    tbody.innerHTML = '';

    stagedData.forEach(issue => {
        const row = document.createElement('tr');
        row.style.borderBottom = '1px solid #e9ecef';

        const hasErrors = issue.validation_errors.length > 0;
        const hasWarnings = issue.validation_warnings.length > 0;

        row.innerHTML = `
            <td style="padding: 12px;">${issue.row_number}</td>
            <td style="padding: 12px;"><code>${issue.issue_key || 'N/A'}</code></td>
            <td style="padding: 12px;">${issue.issue_type}</td>
            <td style="padding: 12px; max-width: 300px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${issue.summary || 'No summary'}</td>
            <td style="padding: 12px;">${issue.status}</td>
            <td style="padding: 12px;">
                ${hasErrors ? `<span style="background: #FF3B30; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px;">${issue.validation_errors.length} Errors</span>` : ''}
                ${hasWarnings ? `<span style="background: #FF9500; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px;">${issue.validation_warnings.length} Warnings</span>` : ''}
                ${!hasErrors && !hasWarnings ? '<span style="color: #34C759;">✓ Valid</span>' : ''}
            </td>
            <td style="padding: 12px; text-align: center;">
                <button onclick="editStagedIssue(${issue.row_number})" style="padding: 6px 12px; background: #007AFF; color: white; border: none; border-radius: 4px; cursor: pointer; margin-right: 4px;">
                    ✏️ Edit
                </button>
                <button onclick="deleteStagedIssue(${issue.row_number})" style="padding: 6px 12px; background: #FF3B30; color: white; border: none; border-radius: 4px; cursor: pointer;">
                    🗑️
                </button>
            </td>
        `;

        tbody.appendChild(row);
    });
}

function editStagedIssue(rowNumber) {
    const issue = stagedData.find(i => i.row_number === rowNumber);
    if (!issue) return;

    currentEditingRow = rowNumber;
    const modal = document.getElementById('issueEditorModal');
    const content = document.getElementById('issueEditorContent');

    content.innerHTML = `
        <form id="issueEditForm" style="display: grid; gap: 16px;">
            <div>
                <label style="display: block; font-weight: 600; margin-bottom: 4px;">Issue Key *</label>
                <input type="text" name="issue_key" value="${issue.issue_key || ''}" required
                    style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
            </div>
            
            <div>
                <label style="display: block; font-weight: 600; margin-bottom: 4px;">Issue Type *</label>
                <select name="issue_type" required style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                    <option value="Epic" ${issue.issue_type === 'Epic' ? 'selected' : ''}>Epic</option>
                    <option value="Feature" ${issue.issue_type === 'Feature' ? 'selected' : ''}>Feature</option>
                    <option value="Story" ${issue.issue_type === 'Story' ? 'selected' : ''}>Story</option>
                    <option value="Bug" ${issue.issue_type === 'Bug' ? 'selected' : ''}>Bug</option>
                    <option value="Task" ${issue.issue_type === 'Task' ? 'selected' : ''}>Task</option>
                </select>
            </div>
            
            <div>
                <label style="display: block; font-weight: 600; margin-bottom: 4px;">Summary *</label>
                <input type="text" name="summary" value="${issue.summary || ''}" required
                    style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
            </div>
            
            <div>
                <label style="display: block; font-weight: 600; margin-bottom: 4px;">Description</label>
                <textarea name="description" rows="4" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">${issue.description || ''}</textarea>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
                <div>
                    <label style="display: block; font-weight: 600; margin-bottom: 4px;">Status</label>
                    <input type="text" name="status" value="${issue.status || ''}"
                        style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                </div>
                <div>
                    <label style="display: block; font-weight: 600; margin-bottom: 4px;">Priority</label>
                    <select name="priority" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                        <option value="Critical" ${issue.priority === 'Critical' ? 'selected' : ''}>Critical</option>
                        <option value="High" ${issue.priority === 'High' ? 'selected' : ''}>High</option>
                        <option value="Medium" ${issue.priority === 'Medium' ? 'selected' : ''}>Medium</option>
                        <option value="Low" ${issue.priority === 'Low' ? 'selected' : ''}>Low</option>
                    </select>
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px;">
                <div>
                    <label style="display: block; font-weight: 600; margin-bottom: 4px;">Team</label>
                    <input type="text" name="team" value="${issue.team || ''}"
                        style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                </div>
                <div>
                    <label style="display: block; font-weight: 600; margin-bottom: 4px;">ART</label>
                    <input type="text" name="art" value="${issue.art || ''}"
                        style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                </div>
                <div>
                    <label style="display: block; font-weight: 600; margin-bottom: 4px;">Portfolio</label>
                    <input type="text" name="portfolio" value="${issue.portfolio || ''}"
                        style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                </div>
            </div>
            
            ${Object.keys(issue.custom_fields || {}).length > 0 ? `
                <div style="margin-top: 8px; padding: 16px; background: #f8f9fa; border-radius: 8px;">
                    <label style="display: block; font-weight: 600; margin-bottom: 12px; font-size: 14px;">📋 Custom Fields</label>
                    <div style="display: grid; gap: 12px;">
                        ${Object.entries(issue.custom_fields).map(([key, value]) => `
                            <div>
                                <label style="display: block; font-size: 12px; color: #666; margin-bottom: 4px;">${key}</label>
                                <textarea name="custom_field_${key}" rows="3" 
                                    style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 13px; background: white; font-family: inherit; resize: vertical;">${value || ''}</textarea>
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
            
            ${issue.validation_errors.length > 0 ? `
                <div style="background: #f8d7da; padding: 12px; border-radius: 4px; border: 1px solid #f5c6cb;">
                    <strong>Validation Errors:</strong>
                    <ul style="margin: 8px 0 0 20px;">
                        ${issue.validation_errors.map(err => `<li>${err}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
            
            <div style="display: flex; gap: 12px; justify-content: flex-end; margin-top: 16px;">
                <button type="button" onclick="closeIssueEditor()" 
                    style="padding: 10px 20px; background: #f0f0f0; border: none; border-radius: 8px; cursor: pointer;">
                    Cancel
                </button>
                <button type="submit" 
                    style="padding: 10px 20px; background: #990AE3; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: 600;">
                    💾 Save Changes
                </button>
            </div>
        </form>
    `;

    // Add form submit handler
    document.getElementById('issueEditForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        await saveIssueEdits(rowNumber, new FormData(e.target));
    });

    modal.style.display = 'block';
}

async function saveIssueEdits(rowNumber, formData) {
    const updates = {};
    const custom_fields = {};

    for (const [key, value] of formData.entries()) {
        // Handle custom fields separately
        if (key.startsWith('custom_field_')) {
            const fieldName = key.replace('custom_field_', '');
            custom_fields[fieldName] = value;
        } else {
            updates[key] = value;
        }
    }

    // Add custom fields to updates if any exist
    if (Object.keys(custom_fields).length > 0) {
        updates.custom_fields = custom_fields;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/v1/admin/import/staged/${rowNumber}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updates)
        });

        const result = await response.json();

        if (result.success) {
            showImportStatus('✅ Issue updated successfully', 'success');
            await loadStagedData();
            closeIssueEditor();
        } else {
            showImportStatus(`❌ Update failed: ${result.error}`, 'error');
        }
    } catch (error) {
        console.error('Error updating issue:', error);
        showImportStatus(`❌ Update failed: ${error.message}`, 'error');
    }
}

function closeIssueEditor() {
    document.getElementById('issueEditorModal').style.display = 'none';
    currentEditingRow = null;
}

async function deleteStagedIssue(rowNumber) {
    if (!confirm('Are you sure you want to remove this issue from staging?')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/v1/admin/import/staged/${rowNumber}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (result.success) {
            showImportStatus('✅ Issue removed from staging', 'success');
            await loadStagedData();
        }
    } catch (error) {
        console.error('Error deleting issue:', error);
        showImportStatus(`❌ Delete failed: ${error.message}`, 'error');
    }
}

async function commitAllIssues() {
    if (!confirm(`Commit all valid issues to the database? This action cannot be undone.`)) {
        return;
    }

    try {
        updateStatusBar('Committing issues to database...');
        showImportStatus('Committing issues to database...', 'info');

        const response = await fetch(`${API_BASE_URL}/v1/admin/import/commit`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const result = await response.json();

        if (result.success) {
            showImportStatus(`✅ Successfully committed ${result.committed} issues! ${result.skipped} skipped. ${result.remaining_staged} issues remain in staging.`, 'success');
            updateStatusBar(`Committed ${result.committed} issues to database`);

            if (result.remaining_staged === 0) {
                document.getElementById('stagedDataSection').style.display = 'none';
                document.getElementById('excelFileInput').value = '';
            } else {
                await loadStagedData();
            }
        } else {
            showImportStatus(`❌ Commit failed: ${result.message}`, 'error');
        }
    } catch (error) {
        console.error('Commit error:', error);
        showImportStatus(`❌ Commit failed: ${error.message}`, 'error');
    }
}

function clearStaging() {
    if (!confirm('Clear all staged data? This will discard all uploaded issues that haven\'t been committed.')) {
        return;
    }

    stagedData = [];
    document.getElementById('stagedDataSection').style.display = 'none';
    document.getElementById('excelFileInput').value = '';
    showImportStatus('✅ Staging cleared', 'success');
}

async function downloadTemplate() {
    try {
        const response = await fetch(`${API_BASE_URL}/v1/admin/import/template`);
        const result = await response.json();

        showImportStatus('✅ Template ready for download! Check the backend/data/templates folder.', 'success');
    } catch (error) {
        console.error('Template error:', error);
        showImportStatus(`❌ Template generation failed: ${error.message}`, 'error');
    }
}

function showTemplates() {
    showImportStatus(`📋 Template files available in backend/data/knowledge_base/:<br>
        - epic_template.txt<br>
        - feature_template.txt<br>
        - user_story_template.txt`, 'info');
}

// Cancel functions
function cancelInsightsGeneration() {
    if (appState.insightsAbortController) {
        appState.insightsAbortController.abort();
        console.log('🛑 Cancelling insights generation...');
    }
}

function cancelPIReportGeneration() {
    if (appState.piReportAbortController) {
        appState.piReportAbortController.abort();
        console.log('🛑 Cancelling PI report generation...');
    }
}

// Expose all functions needed by onclick handlers to global scope
window.switchMainTab = switchMainTab;
window.selectScope = selectScope;
window.setMetricFocus = setMetricFocus;
window.generateScorecard = generateScorecard;
window.generateInsights = generateInsights;
window.cancelInsightsGeneration = cancelInsightsGeneration;
window.cancelPIReportGeneration = cancelPIReportGeneration;
window.exportReport = exportReport;
window.acceptInsight = acceptInsight;
window.viewDetails = viewDetails;
window.dismissInsight = dismissInsight;
window.shareSuccess = shareSuccess;
window.showMetricCategory = showMetricCategory;
window.viewInsightDetails = viewInsightDetails;
window.exportInsight = exportInsight;
window.uploadExcelFile = uploadExcelFile;
window.loadStagedData = loadStagedData;
window.editStagedIssue = editStagedIssue;
window.deleteStagedIssue = deleteStagedIssue;
window.commitAllIssues = commitAllIssues;
window.clearStaging = clearStaging;
window.downloadTemplate = downloadTemplate;
window.showTemplates = showTemplates;
window.closeIssueEditor = closeIssueEditor;

// PI Report Functions
let currentPIReport = null;

// Open PI Report generation dialog
async function openPIReportDialog() {
    const dialog = document.getElementById('piReportDialog');
    dialog.style.display = 'block';

    // Load available PIs
    try {
        const response = await fetch(`${API_BASE_URL}/v1/dashboard?scope=portfolio`);
        const data = await response.json();

        const container = document.getElementById('piReportSelect');
        if (data.available_pis && data.available_pis.length > 0) {
            container.innerHTML = '';
            data.available_pis.forEach(pi => {
                const checkboxWrapper = document.createElement('div');
                checkboxWrapper.style.cssText = 'padding: 8px; margin: 4px 0; border-radius: 4px; transition: background 0.2s;';
                checkboxWrapper.onmouseover = () => checkboxWrapper.style.background = '#f5f5f5';
                checkboxWrapper.onmouseout = () => checkboxWrapper.style.background = 'transparent';

                const label = document.createElement('label');
                label.style.cssText = 'display: flex; align-items: center; cursor: pointer;';

                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.className = 'pi-checkbox';
                checkbox.value = pi;
                checkbox.style.cssText = 'margin-right: 8px; width: 18px; height: 18px; cursor: pointer;';
                checkbox.onchange = updatePISelectionCount;

                const text = document.createElement('span');
                text.textContent = pi;
                text.style.cssText = 'color: #333; font-size: 14px;';

                if (pi === data.current_pi) {
                    checkbox.checked = true;
                    const badge = document.createElement('span');
                    badge.textContent = 'Current';
                    badge.style.cssText = 'margin-left: 8px; padding: 2px 8px; background: #007AFF; color: white; border-radius: 10px; font-size: 11px; font-weight: 600;';
                    text.appendChild(badge);
                }

                label.appendChild(checkbox);
                label.appendChild(text);
                checkboxWrapper.appendChild(label);
                container.appendChild(checkboxWrapper);
            });
            updatePISelectionCount();
        }
    } catch (error) {
        console.error('Error loading PIs:', error);
        updateStatusBar('Error loading PIs');
    }

    // Load available AI models
    await loadAvailableModels();
}

// Load available AI models
async function loadAvailableModels() {
    try {
        const response = await fetch(`${API_BASE_URL}/v1/models/available`);
        const data = await response.json();

        const select = document.getElementById('piReportModel');
        select.innerHTML = '<option value="">Default (gpt-4o-mini)</option>';

        // Add OpenAI models
        if (data.models.openai && data.models.openai.length > 0) {
            const openaiGroup = document.createElement('optgroup');
            openaiGroup.label = 'OpenAI Models';
            data.models.openai.forEach(model => {
                const option = document.createElement('option');
                option.value = model.id;
                option.textContent = `${model.name} (${model.description})`;
                openaiGroup.appendChild(option);
            });
            select.appendChild(openaiGroup);
        }

        // Add Ollama models (only if available)
        if (data.models.ollama && data.models.ollama.length > 0) {
            const ollamaGroup = document.createElement('optgroup');
            ollamaGroup.label = `Ollama Models (${data.models.ollama.length} installed)`;
            data.models.ollama.forEach(model => {
                const option = document.createElement('option');
                option.value = model.id;
                option.textContent = `${model.name} (${model.description})`;
                ollamaGroup.appendChild(option);
            });
            select.appendChild(ollamaGroup);
        }

        // Update help text based on available models
        const helpText = select.parentElement.querySelector('div[style*="font-size: 11px"]');
        if (helpText) {
            const hasOpenAI = data.models.openai && data.models.openai.length > 0;
            const hasOllama = data.models.ollama && data.models.ollama.length > 0;

            if (hasOpenAI && hasOllama) {
                helpText.innerHTML = `💡 OpenAI: Fast cloud models | Ollama: ${data.models.ollama.length} free local models`;
            } else if (hasOpenAI) {
                helpText.innerHTML = '💡 OpenAI models available. Install Ollama for free local models.';
            } else if (hasOllama) {
                helpText.innerHTML = `💡 ${data.models.ollama.length} Ollama models available. Add OPENAI_API_KEY for cloud models.`;
            } else {
                helpText.innerHTML = '⚠️ No AI models available. Configure OPENAI_API_KEY or install Ollama.';
            }
        }
    } catch (error) {
        console.error('Error loading AI models:', error);
    }
}

// Close PI Report dialog
function closePIReportDialog() {
    document.getElementById('piReportDialog').style.display = 'none';
}

// Generate PI Report
async function generatePIReport() {
    const checkboxes = document.querySelectorAll('.pi-checkbox:checked');
    const selectedPIs = Array.from(checkboxes).map(cb => cb.value);

    if (selectedPIs.length === 0) {
        alert('Please select at least one PI to analyze');
        return;
    }

    // Cancel any existing request
    if (appState.piReportAbortController) {
        appState.piReportAbortController.abort();
    }

    // Create new abort controller
    appState.piReportAbortController = new AbortController();

    const compareWithPrevious = document.getElementById('comparePrevious').checked;
    const selectedModel = document.getElementById('piReportModel').value;
    const generateBtn = document.getElementById('generatePIReportBtn');

    // Disable button and show loading
    generateBtn.disabled = true;
    generateBtn.textContent = '⏳ Generating Report...';
    const piText = selectedPIs.length === 1 ? selectedPIs[0] : `${selectedPIs.length} PIs`;

    // Show cancel button
    const cancelBtn = document.getElementById('cancelPIReportBtn');
    if (cancelBtn) {
        cancelBtn.style.display = 'inline-block';
    }

    // Show model info in status if non-default
    const modelInfo = selectedModel ? ` using ${selectedModel}` : '';
    updateStatusBar(`Generating comprehensive report for ${piText}${modelInfo}... This may take 30-60 seconds.`);

    try {
        const requestBody = {
            pis: selectedPIs,
            compare_with_previous: compareWithPrevious,
        };

        // Add model if selected
        if (selectedModel) {
            requestBody.model = selectedModel;
        }

        const response = await fetch(`${API_BASE_URL}/v1/insights/pi-report`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody),
            signal: appState.piReportAbortController.signal
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const reportData = await response.json();
        currentPIReport = reportData;

        // Close dialog and show report
        closePIReportDialog();
        displayPIReport(reportData);

        updateStatusBar(`Report for ${piText} generated successfully`);

        // Hide cancel button on success
        const cancelBtn = document.getElementById('cancelPIReportBtn');
        if (cancelBtn) {
            cancelBtn.style.display = 'none';
        }

        appState.piReportAbortController = null;
    } catch (error) {
        // Check if request was cancelled
        if (error.name === 'AbortError') {
            console.log('🚫 PI Report generation cancelled by user');
            updateStatusBar('Report generation cancelled');
        } else {
            console.error('Error generating PI report:', error);

            // Show more user-friendly error message
            let errorMsg = `Failed to generate PI report: ${error.message}`;

            if (error.message.includes('timeout') || error.message.includes('timed out')) {
                errorMsg = `⏱️ The report generation timed out.\n\n` +
                    `Try these solutions:\n` +
                    `• Select "gpt-4o-mini" model for faster generation\n` +
                    `• Select fewer PIs (e.g., single quarter instead of full year)\n` +
                    `• Wait a moment and try again`;
            } else if (error.message.includes('500')) {
                errorMsg = `Server error occurred. Check the backend logs for details.\n` +
                    `Try: Select a faster model (gpt-4o-mini) or fewer PIs.`;
            }

            alert(errorMsg);
            updateStatusBar('❌ Error generating PI report');
        }
    } finally {
        generateBtn.disabled = false;
        generateBtn.textContent = 'Generate Report';

        // Hide cancel button
        const cancelBtn = document.getElementById('cancelPIReportBtn');
        if (cancelBtn) {
            cancelBtn.style.display = 'none';
        }

        appState.piReportAbortController = null;
    }
}

// Display PI Report in modal
function displayPIReport(reportData) {
    const modal = document.getElementById('piReportModal');
    const body = document.getElementById('piReportBody');
    const title = document.getElementById('piReportTitle');

    const piDisplay = Array.isArray(reportData.pis) ? reportData.pis.join(', ') : reportData.pi;
    title.textContent = `📊 ${Array.isArray(reportData.pis) && reportData.pis.length > 1 ? 'Multi-PI' : 'PI'} ${piDisplay} Management Report`;

    // Convert markdown-style content to HTML
    let htmlContent = reportData.report_content
        .replace(/### (.*)/g, '<h3 style="color: #667eea; margin-top: 24px; margin-bottom: 12px;">$1</h3>')
        .replace(/## (.*)/g, '<h2 style="color: #5856D6; margin-top: 32px; margin-bottom: 16px;">$1</h2>')
        .replace(/# (.*)/g, '<h1 style="color: #5856D6; margin-top: 0; margin-bottom: 20px;">$1</h1>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/^- (.*)$/gm, '<li>$1</li>')
        .replace(/(<li>.*<\/li>)/s, '<ul style="margin: 12px 0; padding-left: 24px; line-height: 1.8;">$1</ul>')
        .replace(/^\d+\. (.*)$/gm, '<li>$1</li>')
        .replace(/\n\n/g, '</p><p style="margin: 12px 0; line-height: 1.6; color: #333;">')
        .replace(/^(?!<[h|u|l|p])/gm, '<p style="margin: 12px 0; line-height: 1.6; color: #333;">');

    // Get metrics for display (handle both single and multi-PI reports)
    const isMultiPI = Array.isArray(reportData.pis) && reportData.pis.length > 1;
    let displayMetrics = reportData.current_metrics;

    if (isMultiPI && reportData.all_pi_metrics) {
        // For multi-PI, calculate aggregate metrics
        const allMetrics = Object.values(reportData.all_pi_metrics);
        const flowEffValues = allMetrics.map(m => m.flow_efficiency).filter(v => v != null);
        const leadtimeValues = allMetrics.map(m => m.avg_leadtime).filter(v => v != null);
        const planningValues = allMetrics.map(m => m.planning_accuracy).filter(v => v != null);
        const throughputTotal = allMetrics.reduce((sum, m) => sum + (m.throughput || 0), 0);

        displayMetrics = {
            flow_efficiency: flowEffValues.length > 0 ? Math.round(flowEffValues.reduce((a, b) => a + b, 0) / flowEffValues.length * 10) / 10 : null,
            avg_leadtime: leadtimeValues.length > 0 ? Math.round(leadtimeValues.reduce((a, b) => a + b, 0) / leadtimeValues.length * 10) / 10 : null,
            planning_accuracy: planningValues.length > 0 ? Math.round(planningValues.reduce((a, b) => a + b, 0) / planningValues.length * 10) / 10 : null,
            throughput: throughputTotal
        };
    }

    // Only show metrics card if we have metrics to display
    let metricsCard = '';
    if (displayMetrics && displayMetrics.flow_efficiency !== null) {
        metricsCard = `
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 24px; border-radius: 12px; margin-bottom: 32px; box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);">
                <h3 style="margin: 0 0 20px 0; color: white;">📊 Key Metrics Summary ${isMultiPI ? '(Aggregate)' : ''}</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px;">
                    <div style="background: rgba(255,255,255,0.1); padding: 16px; border-radius: 8px;">
                        <div style="font-size: 12px; opacity: 0.9; margin-bottom: 4px;">Flow Efficiency</div>
                        <div style="font-size: 28px; font-weight: 700;">${displayMetrics.flow_efficiency || 'N/A'}%</div>
                        ${reportData.previous_metrics ? `<div style="font-size: 13px; opacity: 0.9; margin-top: 4px;">${getChangeIndicator(displayMetrics.flow_efficiency, reportData.previous_metrics.flow_efficiency, true)}</div>` : ''}
                    </div>
                    <div style="background: rgba(255,255,255,0.1); padding: 16px; border-radius: 8px;">
                        <div style="font-size: 12px; opacity: 0.9; margin-bottom: 4px;">Avg Lead-Time</div>
                        <div style="font-size: 28px; font-weight: 700;">${displayMetrics.avg_leadtime || 'N/A'}<span style="font-size: 14px; font-weight: 400;"> days</span></div>
                        ${reportData.previous_metrics ? `<div style="font-size: 13px; opacity: 0.9; margin-top: 4px;">${getChangeIndicator(displayMetrics.avg_leadtime, reportData.previous_metrics.avg_leadtime, false)}</div>` : ''}
                    </div>
                    <div style="background: rgba(255,255,255,0.1); padding: 16px; border-radius: 8px;">
                        <div style="font-size: 12px; opacity: 0.9; margin-bottom: 4px;">Planning Accuracy</div>
                        <div style="font-size: 28px; font-weight: 700;">${displayMetrics.planning_accuracy || 'N/A'}%</div>
                        ${reportData.previous_metrics ? `<div style="font-size: 13px; opacity: 0.9; margin-top: 4px;">${getChangeIndicator(displayMetrics.planning_accuracy, reportData.previous_metrics.planning_accuracy, true)}</div>` : ''}
                    </div>
                    <div style="background: rgba(255,255,255,0.1); padding: 16px; border-radius: 8px;">
                        <div style="font-size: 12px; opacity: 0.9; margin-bottom: 4px;">Features Delivered</div>
                        <div style="font-size: 28px; font-weight: 700;">${displayMetrics.throughput || 'N/A'}</div>
                        ${reportData.previous_metrics ? `<div style="font-size: 13px; opacity: 0.9; margin-top: 4px;">${getChangeIndicator(displayMetrics.throughput, reportData.previous_metrics.throughput, true, '')}</div>` : ''}
                    </div>
                </div>
            </div>
        `;
    }

    body.innerHTML = metricsCard + '<div style="color: #333; font-size: 15px;">' + htmlContent + '</div>';
    modal.style.display = 'block';
}

// Helper function to get change indicator
function getChangeIndicator(current, previous, higherIsBetter, suffix = '%') {
    if (!current || !previous) return '';

    const change = current - previous;
    const isPositive = higherIsBetter ? change > 0 : change < 0;
    const arrow = isPositive ? '↑' : '↓';
    const color = isPositive ? '#34C759' : '#FF3B30';

    return `<span style="color: ${color};">${arrow} ${Math.abs(change).toFixed(1)}${suffix} from previous PI</span>`;
}

// Close PI Report modal
function closePIReport() {
    document.getElementById('piReportModal').style.display = 'none';
}

// Print PI Report
function printPIReport() {
    if (!currentPIReport) return;

    const printWindow = window.open('', '', 'width=1000,height=800');
    const reportHTML = document.getElementById('piReportBody').innerHTML;

    const piDisplay = Array.isArray(currentPIReport.pis)
        ? currentPIReport.pis.join(', ')
        : currentPIReport.pi;
    const reportType = Array.isArray(currentPIReport.pis) && currentPIReport.pis.length > 1
        ? 'Multi-PI Management Report'
        : 'Program Increment Management Report';

    printWindow.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
            <title>${reportType} - ${piDisplay}</title>
            <style>
                @media print {
                    @page { size: A4; margin: 20mm; }
                }
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 210mm;
                    margin: 0 auto;
                    padding: 20px;
                }
                h1 { color: #5856D6; page-break-after: avoid; }
                h2 { color: #5856D6; margin-top: 32px; page-break-after: avoid; }
                h3 { color: #667eea; margin-top: 24px; page-break-after: avoid; }
                ul, ol { margin: 12px 0; padding-left: 24px; }
                li { margin-bottom: 8px; }
                p { margin: 12px 0; }
                .page-break { page-break-after: always; }
            </style>
        </head>
        <body>
            <div style="text-align: center; margin-bottom: 40px;">
                <h1>${reportType}</h1>
                <h2>${piDisplay}</h2>
                <p>Generated: ${new Date(currentPIReport.generated_at).toLocaleString()}</p>
            </div>
            ${reportHTML}
            <div style="margin-top: 60px; padding-top: 20px; border-top: 2px solid #eee; text-align: center; font-size: 11px; color: #999;">
                <p>This report was generated by Evaluation Coach - AI-Powered Agile & SAFe Analytics Platform</p>
                <p>© ${new Date().getFullYear()} - Confidential</p>
            </div>
        </body>
        </html>
    `);

    printWindow.document.close();
    printWindow.focus();
    setTimeout(() => {
        printWindow.print();
        printWindow.close();
    }, 250);
}

// Helper functions for PI selection
function updatePISelectionCount() {
    const checkboxes = document.querySelectorAll('.pi-checkbox:checked');
    const count = checkboxes.length;
    const countElement = document.getElementById('piSelectionCount');
    if (countElement) {
        countElement.textContent = `${count} PI${count !== 1 ? 's' : ''} selected`;
        countElement.style.color = count > 0 ? '#007AFF' : '#8E8E93';
        countElement.style.fontWeight = count > 0 ? '600' : 'normal';
    }
}

function selectAllPIs() {
    const checkboxes = document.querySelectorAll('.pi-checkbox');
    checkboxes.forEach(cb => cb.checked = true);
    updatePISelectionCount();
}

function deselectAllPIs() {
    const checkboxes = document.querySelectorAll('.pi-checkbox');
    checkboxes.forEach(cb => cb.checked = false);
    updatePISelectionCount();
}

function selectYear2025() {
    const checkboxes = document.querySelectorAll('.pi-checkbox');
    checkboxes.forEach(cb => {
        cb.checked = cb.value.startsWith('25Q');
    });
    updatePISelectionCount();
}

// Export Executive Summary to Excel
async function exportExecutiveSummary() {
    try {
        showLoadingOverlay('Exporting executive summary to Excel...');

        // Build query parameters based on current filters
        const params = new URLSearchParams();

        if (appState.selectedPIs && appState.selectedPIs.length > 0) {
            params.append('pis', appState.selectedPIs.join(','));
        }

        if (appState.selectedARTs && appState.selectedARTs.length > 0) {
            // Don't send ARTs filter if all ARTs are selected
            if (!appState.allARTs || appState.selectedARTs.length < appState.allARTs.length) {
                params.append('arts', appState.selectedARTs.join(','));
            }
        }

        // Fetch Excel file
        const response = await fetch(`${API_BASE_URL}/v1/insights/export-summary?${params.toString()}`);

        if (!response.ok) {
            throw new Error(`Export failed: ${response.statusText}`);
        }

        // Get the blob and download it
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;

        // Extract filename from Content-Disposition header
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = 'executive_summary.xlsx';
        if (contentDisposition) {
            const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(contentDisposition);
            if (matches != null && matches[1]) {
                filename = matches[1].replace(/['"]/g, '');
            }
        }

        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        hideLoadingOverlay();

        // Show success message
        alert('✅ Executive summary exported successfully!');
    } catch (error) {
        console.error('Error exporting executive summary:', error);
        hideLoadingOverlay();
        alert(`❌ Error exporting: ${error.message}`);
    }
}


// Export functions to window
window.openPIReportDialog = openPIReportDialog;
window.closePIReportDialog = closePIReportDialog;
window.generatePIReport = generatePIReport;
window.closePIReport = closePIReport;
window.printPIReport = printPIReport;
window.updatePISelectionCount = updatePISelectionCount;
window.selectAllPIs = selectAllPIs;
window.deselectAllPIs = deselectAllPIs;
window.selectYear2025 = selectYear2025;
window.exportExecutiveSummary = exportExecutiveSummary;

console.log('📊 Evaluation Coach app.js loaded successfully');
