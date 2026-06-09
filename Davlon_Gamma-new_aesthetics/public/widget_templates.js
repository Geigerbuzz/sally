
// WidgetRenderer - strict template enforcement for AI widgets

class WidgetRenderer {
    static render(payload) {
        // Validation: Verify payload has required fields
        if (!payload || !payload.template || !payload.id) {
            console.error("Invalid widget payload:", payload);
            return this.renderError("Invalid Data");
        }

        switch (payload.template) {
            case 'kpi-card':
                return this.renderKPICard(payload);
            case 'bar-chart':
            case 'line-chart':
                return this.renderChartWidget(payload);
            case 'data-table':
                return this.renderTableWidget(payload);
            default:
                console.error("Unknown template:", payload.template);
                return this.renderError("Unknown Template");
        }
    }

    static createBaseWidget(payload, classes = []) {
        const widget = document.createElement('div');
        widget.className = `widget ${classes.join(' ')}`;
        widget.id = payload.id;
        widget.setAttribute('draggable', 'true');

        // Size enforcement via CSS classes matching payload instruction or defaults
        // Note: The Grid System handles the actual sizing based on these classes.
        if (payload.dimension) {
            widget.classList.add(`w-${payload.dimension}`);
        } else {
            // Defaults based on template
            if (payload.template === 'kpi-card') widget.classList.add('w-1x1');
            else if (payload.template.includes('chart')) widget.classList.add('w-2x1');
            else if (payload.template === 'data-table') widget.classList.add('w-2x2');
        }

        return widget;
    }

    static renderKPICard(payload) {
        const widget = this.createBaseWidget(payload);
        const { title, data } = payload;

        // KPI Structure: Icon (opt) + Title + Big Value + Trend (opt)
        let trendHtml = '';
        if (data.trend) {
            const trendIcon = data.trend === 'up' ? 'ri-arrow-up-line' : (data.trend === 'down' ? 'ri-arrow-down-line' : 'ri-subtract-line');
            const trendColor = data.trend === 'up' ? '#32d74b' : (data.trend === 'down' ? '#ff453a' : 'var(--text-secondary)');
            trendHtml = `<span style="color: ${trendColor}; font-size: 14px; display: flex; align-items: center; gap: 4px;">
                            <i class="${trendIcon}"></i> ${data.trendValue || ''}
                         </span>`;
        }

        const iconHtml = data.icon ? `<i class="${data.icon}" style="font-size: 28px; margin-bottom: 8px; color: var(--accent);"></i>` : '';

        widget.innerHTML = `
            ${iconHtml}
            <h3 class="widget-title" title="${title}">${title}</h3>
            <p class="live-num" style="font-size: 32px;">${data.value}</p>
            ${trendHtml}
        `;

        return widget;
    }

    static renderChartWidget(payload) {
        const widget = this.createBaseWidget(payload, ['widget-chart-container']);
        const { title, template, data } = payload;

        // Random Canvas ID
        const canvasId = `chart-${Math.random().toString(36).substr(2, 9)}`;

        widget.innerHTML = `
            <div style="width: 100%; display: flex; flex-direction: column; height: 100%;">
                <h3 class="widget-title" title="${title}">${title}</h3>
                <div style="flex: 1; position: relative; width: 100%; min-height: 0;">
                    <canvas id="${canvasId}"></canvas>
                </div>
            </div>
        `;

        // Defer Chart initialization to allow DOM insertion first
        setTimeout(() => {
            const ctx = document.getElementById(canvasId);
            if (ctx) {
                new Chart(ctx, {
                    type: template === 'bar-chart' ? 'bar' : 'line',
                    data: {
                        labels: data.labels,
                        datasets: data.datasets.map(ds => ({
                            label: ds.label,
                            data: ds.values,
                            backgroundColor: ds.color || 'rgba(10, 132, 255, 0.5)', // var(--accent) with opacity
                            borderColor: ds.color || '#0a84ff', // var(--accent)
                            borderWidth: 1,
                            tension: 0.4 // Smooth lines
                        }))
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: data.datasets.length > 1 }, // Hide legend if only 1 dataset
                            title: { display: false } // We use HTML title
                        },
                        scales: {
                            y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' } },
                            x: { grid: { display: false } }
                        }
                    }
                });
            }
        }, 100);

        return widget;
    }

    static renderTableWidget(payload) {
        const widget = this.createBaseWidget(payload, ['widget-table']);
        const { title, data } = payload;

        const headers = data.headers.map(h => `<th>${h}</th>`).join('');
        const rows = data.rows.map(row =>
            `<tr>${row.map(cell => `<td>${cell}</td>`).join('')}</tr>`
        ).join('');

        widget.innerHTML = `
            <h3 class="widget-title" title="${title}" style="margin-bottom: 12px;">${title}</h3>
            <div class="table-wrapper">
                <table>
                    <thead><tr>${headers}</tr></thead>
                    <tbody>${rows}</tbody>
                </table>
            </div>
        `;

        return widget;
    }

    static renderError(msg) {
        const widget = document.createElement('div');
        widget.className = 'widget w-1x1';
        widget.innerHTML = `<i class="ri-error-warning-line" style="color: #ff453a; font-size: 24px;"></i><p>${msg}</p>`;
        return widget;
    }

    // --- Mock Generator for Verification ---
    static generateMockPayload(prompt) {
        // Simple logic to pick a template based on keywords in strict mock mode
        const p = prompt.toLowerCase();

        if (p.includes('chart') || p.includes('graph')) {
            return {
                id: `w-${Date.now()}`,
                title: "Generated Sales Data",
                template: p.includes('bar') ? 'bar-chart' : 'line-chart',
                dimension: '2x1',
                data: {
                    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
                    datasets: [{
                        label: 'Sales',
                        values: [12, 19, 3, 5, 2],
                        color: '#0a84ff'
                    }]
                }
            };
        } else if (p.includes('list') || p.includes('table')) {
            return {
                id: `w-${Date.now()}`,
                title: "Recent Transactions",
                template: 'data-table',
                dimension: '2x2', // Lists are typically 2x2 or 1x2.
                data: {
                    headers: ['Agent', 'Amount', 'Status'],
                    rows: [
                        ['Dora', '$500k', 'Closed'],
                        ['Boots', '$320k', 'Pending'],
                        ['Swiper', '$150k', 'Active']
                    ]
                }
            };
        } else {
            // Default to KPI
            return {
                id: `w-${Date.now()}`,
                title: "New KPI Widget",
                template: 'kpi-card',
                // dimension: '1x1', // implied default
                data: {
                    value: "42",
                    trend: "up",
                    trendValue: "+15%",
                    subtitle: "vs last month",
                    icon: "ri-lightbulb-line"
                }
            };
        }
    }
}

// Make accessible globally
window.WidgetRenderer = WidgetRenderer;
