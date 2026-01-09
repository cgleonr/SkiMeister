/**
 * SkiMeister - Ski Resort Finder
 * Main application logic
 */

const API_BASE = 'http://localhost:5000/api';

// State
let userLocation = null;
let allResorts = [];
let filters = {
    radius: 200,
    minSnow: 0,
    maxPrice: 200,
    minSlopes: 0,
    sort: 'distance',
    country: 'Switzerland'
};

// DOM Elements
const loadingEl = document.getElementById('loading');
const resortsGrid = document.getElementById('resorts-grid');
const emptyState = document.getElementById('empty-state');
const totalResortsEl = document.getElementById('total-resorts');
const nearbyCountEl = document.getElementById('nearby-count');
const resortModal = document.getElementById('resort-modal');
const modalBody = document.getElementById('modal-body');
const closeModal = document.querySelector('.close-modal');

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    initializeFilters();
    getUserLocation();
    setupEventListeners();
    updateStats();
});

const countrySelect = document.getElementById('country-select');

/**
 * Update stats and populate country dropdown
 */
async function updateStats() {
    try {
        const response = await fetch(`${API_BASE}/stats`);
        const data = await response.json();
        if (data.success) {
            totalResortsEl.textContent = data.stats.total_resorts;
            populateCountryDropdown(data.stats.countries);
        }
    } catch (error) {
        console.error('Error fetching stats:', error);
    }
}

/**
 * Populate country dropdown with available countries
 */
function populateCountryDropdown(countries) {
    if (!countries || countries.length === 0) {
        countrySelect.innerHTML = '<option value="">No countries found</option>';
        return;
    }

    const currentCountry = filters.country;
    countrySelect.innerHTML = countries
        .sort()
        .map(country => `<option value="${country}" ${country === currentCountry ? 'selected' : ''}>${country}</option>`)
        .join('');

    // If no country was selected but we have countries, pick the first one
    if (!filters.country && countries.length > 0) {
        filters.country = countries[0];
        searchNearbyResorts();
    }
}

/**
 * Get user's geolocation
 */
function getUserLocation() {
    if (!navigator.geolocation) {
        console.error('Geolocation not supported');
        searchNearbyResorts();
        return;
    }

    showLoading();

    navigator.geolocation.getCurrentPosition(
        (position) => {
            userLocation = {
                lat: position.coords.latitude,
                lng: position.coords.longitude
            };
            console.log('User location:', userLocation);
            searchNearbyResorts();
        },
        (error) => {
            console.error('Geolocation error:', error);
            // Fall back to showing resorts without distance
            searchNearbyResorts();
        }
    );
}

/**
 * Search for nearby resorts based on user location
 */
async function searchNearbyResorts() {
    showLoading();

    try {
        const params = new URLSearchParams({
            radius: filters.radius,
            sort: filters.sort
        });

        // Only add country if it's explicitly selected or if we don't have location
        if (filters.country) {
            params.append('country', filters.country);
        }

        if (userLocation) {
            params.append('lat', userLocation.lat);
            params.append('lng', userLocation.lng);
        }

        // Add optional filters
        if (filters.minSnow > 0) {
            params.append('min_snow', filters.minSnow);
        }
        if (filters.maxPrice < 200) {
            params.append('max_price', filters.maxPrice);
        }
        if (filters.minSlopes > 0) {
            params.append('min_slopes', filters.minSlopes);
        }

        // Use /search if we have location, else /resorts
        const endpoint = userLocation ? `${API_BASE}/search` : `${API_BASE}/resorts`;
        const response = await fetch(`${endpoint}?${params}`);
        const data = await response.json();

        if (data.success) {
            allResorts = data.resorts;
            nearbyCountEl.textContent = data.count;

            // If the API returned a country (via reverse geocode), update our filter
            if (data.country && !filters.country) {
                updateCountryFilter(data.country);
            }

            renderResorts(data.resorts);
        } else {
            console.error('API error:', data.error);
            showEmptyState();
        }
    } catch (error) {
        console.error('Fetch error:', error);
        showEmptyState();
    }
}

/**
 * Helper to update country filter UI
 */
function updateCountryFilter(country) {
    filters.country = country;
    if (countrySelect) {
        // Add the country to the dropdown if it's not there
        const exists = Array.from(countrySelect.options).some(opt => opt.value === country);
        if (!exists) {
            const option = document.createElement('option');
            option.value = country;
            option.textContent = country;
            countrySelect.appendChild(option);
        }
        countrySelect.value = country;
    }
}

/**
 * Render resort cards
 */
function renderResorts(resorts) {
    hideLoading();

    if (!resorts || resorts.length === 0) {
        showEmptyState();
        return;
    }

    hideEmptyState();
    resortsGrid.innerHTML = resorts.map(resort => createResortCard(resort)).join('');
}

/**
 * Create HTML for a resort card
 */
function createResortCard(resort) {
    const conditions = resort.conditions || {};
    const pricing = resort.pricing || {};

    const distanceBadge = resort.distance_km
        ? `<div class="distance-badge">${resort.distance_km} km</div>`
        : '';

    const statusBadge = conditions.status
        ? `<div class="status-badge ${conditions.status}">${conditions.status}</div>`
        : '';

    const snowDepth = conditions.snow_depth_mountain || 0;
    const snowClass = snowDepth > 100 ? 'good' : snowDepth > 50 ? 'warning' : '';

    const slopesOpen = conditions.slopes_open_km || 0;
    const slopesTotal = conditions.slopes_total_km || 0;
    const slopesPercent = slopesTotal > 0 ? Math.round((slopesOpen / slopesTotal) * 100) : 0;

    const price = pricing.adult_day_pass
        ? `<div class="price-tag">
             <span class="price-label">Day Pass</span>
             <span class="price-value">${pricing.adult_day_pass} ${pricing.currency || 'CHF'}</span>
           </div>`
        : '';

    return `
        <div class="resort-card" onclick="openResortDetails(${resort.id})">
            ${statusBadge}
            <div class="resort-header">
                <div>
                    <div class="resort-name">${resort.name}</div>
                    <div class="resort-location">📍 ${resort.region || resort.country}</div>
                </div>
                ${distanceBadge}
            </div>
            
            <div class="resort-stats">
                <div class="stat">
                    <span class="stat-label">Snow Depth</span>
                    <span class="stat-value-large ${snowClass}">${snowDepth}cm</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Fresh Snow</span>
                    <span class="stat-value-large">${conditions.fresh_snow_24h || 0}cm</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Open Slopes</span>
                    <span class="stat-value-large">${slopesOpen}km</span>
                </div>
                <div class="stat">
                    <span class="stat-label">% Open</span>
                    <span class="stat-value-large">${slopesPercent}%</span>
                </div>
            </div>
            
            <div class="resort-conditions">
                ${conditions.temperature_mountain !== undefined ? `<span class="condition-tag">🌡️ ${conditions.temperature_mountain}°C</span>` : ''}
                ${conditions.wind_speed ? `<span class="condition-tag">💨 ${conditions.wind_speed} km/h</span>` : ''}
                ${conditions.visibility ? `<span class="condition-tag">👁️ ${conditions.visibility}</span>` : ''}
                ${conditions.lifts_open ? `<span class="condition-tag">🚡 ${conditions.lifts_open}/${conditions.lifts_total} lifts</span>` : ''}
            </div>
            
            ${price}
        </div>
    `;
}

/**
 * Initialize filter values
 */
function initializeFilters() {
    document.getElementById('radius').value = filters.radius;
    document.getElementById('radius-value').textContent = `${filters.radius} km`;

    document.getElementById('min-snow').value = filters.minSnow;
    document.getElementById('min-snow-value').textContent = `${filters.minSnow} cm`;

    document.getElementById('max-price').value = filters.maxPrice;
    document.getElementById('max-price-value').textContent = `${filters.maxPrice} CHF`;

    document.getElementById('min-slopes').value = filters.minSlopes;
    document.getElementById('min-slopes-value').textContent = `${filters.minSlopes} km`;
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Radius filter
    document.getElementById('radius').addEventListener('input', (e) => {
        filters.radius = parseInt(e.target.value);
        document.getElementById('radius-value').textContent = `${filters.radius} km`;
        debouncedSearch();
    });

    // Min snow filter
    document.getElementById('min-snow').addEventListener('input', (e) => {
        filters.minSnow = parseInt(e.target.value);
        document.getElementById('min-snow-value').textContent = `${filters.minSnow} cm`;
        debouncedSearch();
    });

    // Max price filter
    document.getElementById('max-price').addEventListener('input', (e) => {
        filters.maxPrice = parseInt(e.target.value);
        document.getElementById('max-price-value').textContent = `${filters.maxPrice} CHF`;
        debouncedSearch();
    });

    // Min slopes filter
    document.getElementById('min-slopes').addEventListener('input', (e) => {
        filters.minSlopes = parseInt(e.target.value);
        document.getElementById('min-slopes-value').textContent = `${filters.minSlopes} km`;
        debouncedSearch();
    });

    // Sort buttons
    document.querySelectorAll('.sort-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.sort-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            filters.sort = e.target.dataset.sort;
            searchNearbyResorts();
        });
    });

    // Country selection change
    countrySelect.addEventListener('change', (e) => {
        filters.country = e.target.value;
        searchNearbyResorts();
    });

    // Modal close
    closeModal.onclick = () => {
        resortModal.style.display = 'none';
    };

    window.onclick = (event) => {
        if (event.target == resortModal) {
            resortModal.style.display = 'none';
        }
    };
}

/**
 * Debounced search
 */
let searchTimeout;
function debouncedSearch() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        searchNearbyResorts();
    }, 300);
}

/**
 * Open resort details modal
 */
async function openResortDetails(resortId) {
    showLoading();
    try {
        const response = await fetch(`${API_BASE}/resort/${resortId}`);
        const data = await response.json();

        if (data.success) {
            renderResortDetails(data.resort);
            resortModal.style.display = 'block';
        }
    } catch (error) {
        console.error('Error fetching resort details:', error);
    } finally {
        hideLoading();
    }
}

/**
 * Render resort details in modal
 */
function renderResortDetails(resort) {
    const conditions = resort.conditions || {};
    const pricing = resort.pricing || {};
    const forecasts = resort.forecasts || [];

    modalBody.innerHTML = `
        <div class="resort-detail-header">
            <div class="resort-detail-title">
                <h2>${resort.name}</h2>
                <div class="resort-location">📍 ${resort.region}, ${resort.country}</div>
            </div>
            <div class="resort-status-badge ${conditions.status || 'unknown'}">
                ${conditions.status || 'unknown'}
            </div>
        </div>

        <div class="resort-detail-info">
            <div class="detail-card">
                <h4>❄️ Snow Report</h4>
                <p>Mountain: <strong>${conditions.snow_depth_mountain || 0}cm</strong></p>
                <p>Valley: <strong>${conditions.snow_depth_valley || 0}cm</strong></p>
                <p>Fresh (24h): <strong>${conditions.fresh_snow_24h || 0}cm</strong></p>
            </div>
            <div class="detail-card">
                <h4>🎿 Slopes & Lifts</h4>
                <p>Open Slopes: <strong>${conditions.slopes_open_km || 0}/${conditions.slopes_total_km || 0} km</strong></p>
                <p>Open Lifts: <strong>${conditions.lifts_open || 0}/${conditions.lifts_total || 0}</strong></p>
            </div>
            <div class="detail-card">
                <h4>🌡️ Current Weather</h4>
                <p>Mountain: <strong>${conditions.temperature_mountain || '--'}°C</strong></p>
                <p>Valley: <strong>${conditions.temperature_valley || '--'}°C</strong></p>
                <p>Wind: <strong>${conditions.wind_speed || 0} km/h</strong></p>
            </div>
            <div class="detail-card">
                <h4>💰 Pricing</h4>
                <p>Adult: <strong>${pricing.adult_day_pass || '--'} ${pricing.currency}</strong></p>
                <p>Child: <strong>${pricing.child_day_pass || '--'} ${pricing.currency}</strong></p>
            </div>
        </div>

        <div class="resort-description">
            <p>${resort.description || 'No description available.'}</p>
            ${resort.website ? `<p><a href="${resort.website}" target="_blank" class="website-link">Visit Website 🔗</a></p>` : ''}
        </div>

        <div class="forecast-section">
            <h3>📅 7-Day Forecast</h3>
            <div class="forecast-grid">
                ${forecasts.map(f => `
                    <div class="forecast-day">
                        <div class="forecast-date">${formatDate(f.date)}</div>
                        <div class="forecast-icon">${getWeatherIcon(f.symbol)}</div>
                        <div class="forecast-temps">
                            <span class="temp-max">${Math.round(f.temp_max)}°</span>
                            <span class="temp-min">${Math.round(f.temp_min)}°</span>
                        </div>
                        ${f.snow_forecast_cm > 0 ? `<div class="forecast-snow">❄️ ${f.snow_forecast_cm}cm</div>` : ''}
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

/**
 * Helper: Format date
 */
function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { weekday: 'short', day: 'numeric' });
}

/**
 * Helper: Get weather icon from symbol
 */
function getWeatherIcon(symbol) {
    if (!symbol) return '☀️';
    const s = symbol.toLowerCase();
    if (s.includes('snow')) return '❄️';
    if (s.includes('rain')) return '🌧️';
    if (s.includes('cloud')) return '☁️';
    if (s.includes('sun')) return '☀️';
    if (s.includes('storm')) return '⚡';
    return '⛅';
}

/**
 * Loading state
 */
function showLoading() {
    loadingEl.style.display = 'block';
}

function hideLoading() {
    loadingEl.style.display = 'none';
}

/**
 * Empty state
 */
function showEmptyState() {
    resortsGrid.style.display = 'none';
    emptyState.style.display = 'block';
}

function hideEmptyState() {
    resortsGrid.style.display = 'grid';
    emptyState.style.display = 'none';
}
