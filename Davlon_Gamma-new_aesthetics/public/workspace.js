// Workspace Listings Page Logic

document.addEventListener('DOMContentLoaded', async () => {
    const grid = document.getElementById('listing-grid');
    if (!grid) return;

    try {
        const response = await fetch('/api/listings');
        const data = await response.json();

        // Clear loading state
        grid.innerHTML = '';

        if (!data.listings || data.listings.length === 0) {
            // Empty state
            grid.innerHTML = `
                <div class="listing-empty-state" style="grid-column: 1 / -1; text-align: center; padding: 60px 20px;">
                    <i class="ri-home-4-line" style="font-size: 64px; color: var(--text-secondary); opacity: 0.5;"></i>
                    <h3 style="margin-top: 16px; color: var(--text-primary);">No Listings Yet</h3>
                    <p style="color: var(--text-secondary); margin-top: 8px;">
                        Upload property documents in Data Sources to create listings automatically.
                    </p>
                </div>
            `;
            return;
        }

        // Render each listing
        data.listings.forEach(listing => {
            const card = createListingCard(listing);
            grid.appendChild(card);
        });

    } catch (e) {
        console.error('Failed to load listings:', e);
        grid.innerHTML = `
            <div class="listing-empty-state" style="grid-column: 1 / -1; text-align: center; padding: 60px 20px;">
                <i class="ri-error-warning-line" style="font-size: 64px; color: #ff453a;"></i>
                <p style="color: var(--text-secondary); margin-top: 16px;">Failed to load listings.</p>
            </div>
        `;
    }
});

function createListingCard(listing) {
    const card = document.createElement('div');
    card.className = 'listing-card';
    card.dataset.id = listing.id;

    // Format address for display
    const addressParts = listing.address.split(',');
    const formattedAddress = addressParts.length > 1
        ? `${addressParts[0].trim()},<br>${addressParts.slice(1).join(',').trim()}`
        : listing.address;

    // Format price
    const formattedPrice = listing.price
        ? `$${(listing.price / 1000).toFixed(0)}k`
        : '';

    // Bonuses (if any)
    const bonusesHtml = Array.isArray(listing.bonuses) && listing.bonuses.length > 0
        ? `<div class="listing-bonuses">${listing.bonuses.map(b => `<span class="bonus-badge">${b}</span>`).join('')}</div>`
        : '';

    card.innerHTML = `
        <div class="listing-header">
            <div class="traffic-light">
                <div class="status-dot-lg" data-status="red" title="None Interested"></div>
                <div class="status-dot-lg" data-status="yellow" title="Some Potential"></div>
                <div class="status-dot-lg" data-status="green" title="Sale in Progress"></div>
            </div>
            ${formattedPrice ? `<span class="listing-price">${formattedPrice}</span>` : ''}
        </div>
        <div class="listing-image">
            <div class="listing-image-placeholder">
                <i class="ri-home-4-line"></i>
            </div>
        </div>
        <div class="listing-content">
            <div class="listing-address">${formattedAddress}</div>
            <div class="listing-specs">
                ${listing.beds ? `<span class="spec-item"><i class="ri-hotel-bed-line"></i> ${listing.beds}</span>` : ''}
                ${listing.baths ? `<span class="spec-item"><i class="ri-drop-line"></i> ${listing.baths}</span>` : ''}
                ${listing.sqft ? `<span class="spec-item"><i class="ri-ruler-line"></i> ${listing.sqft.toLocaleString()} sqft</span>` : ''}
            </div>
            ${bonusesHtml}
        </div>
    `;

    // Add click handlers for traffic light
    const trafficLight = card.querySelector('.traffic-light');
    trafficLight.querySelectorAll('.status-dot-lg').forEach(dot => {
        dot.style.cursor = 'pointer';
        dot.addEventListener('click', (e) => {
            e.stopPropagation(); // Don't trigger card click

            const status = dot.dataset.status;
            const isActive = dot.classList.contains(status);

            // Clear all dots first
            trafficLight.querySelectorAll('.status-dot-lg').forEach(d => {
                d.classList.remove('red', 'yellow', 'green');
            });

            // Toggle: if was active, leave all off. Otherwise activate this one.
            if (!isActive) {
                dot.classList.add(status);
            }

            // TODO: Persist to backend if needed
        });
    });

    return card;
}
