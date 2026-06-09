/**
 * Universal Popup/Modal System
 * 
 * Usage:
 *   Popup.error('Something went wrong.', { context: 'upload' });
 *   Popup.success('File uploaded!');
 *   Popup.confirm({ title: 'Delete?', message: 'This cannot be undone.', onConfirm: () => {...} });
 */

const Popup = (() => {
    let container = null;

    // Create container on first use
    function ensureContainer() {
        if (container) return container;

        container = document.createElement('div');
        container.id = 'popup-container';
        container.innerHTML = `
            <div class="popup-overlay"></div>
            <div class="popup-box">
                <div class="popup-icon"></div>
                <h3 class="popup-title"></h3>
                <p class="popup-message"></p>
                <div class="popup-report-form" style="display: none;">
                    <p class="popup-report-label">Please describe what you were doing when this happened:</p>
                    <textarea class="popup-report-input" placeholder="e.g. I was uploading a PDF file..." rows="3"></textarea>
                </div>
                <div class="popup-actions"></div>
            </div>
        `;
        document.body.appendChild(container);

        // Don't close on overlay click for errors
        container.querySelector('.popup-overlay').addEventListener('click', (e) => {
            const box = container.querySelector('.popup-box');
            if (!box.classList.contains('popup-error')) {
                hide();
            }
        });

        return container;
    }

    function show(options = {}) {
        const {
            type = 'info',        // 'error', 'success', 'warning', 'info', 'confirm'
            title = '',
            message = '',
            autoDismiss = null,   // ms to auto-close (null = manual)
            actions = null,       // Custom actions array [{label, onClick, primary}]
            context = ''          // Error context for reporting
        } = options;

        ensureContainer();

        const box = container.querySelector('.popup-box');
        const iconEl = container.querySelector('.popup-icon');
        const titleEl = container.querySelector('.popup-title');
        const messageEl = container.querySelector('.popup-message');
        const actionsEl = container.querySelector('.popup-actions');
        const reportForm = container.querySelector('.popup-report-form');
        const reportInput = container.querySelector('.popup-report-input');

        // Set content
        titleEl.textContent = title;
        messageEl.textContent = message;

        // Set icon based on type
        const icons = {
            error: '✕',
            success: '✓',
            warning: '⚠',
            info: 'ℹ',
            confirm: '?'
        };
        iconEl.textContent = icons[type] || icons.info;

        // Apply type class
        box.className = 'popup-box popup-' + type;

        // Show/hide report form for errors
        reportForm.style.display = type === 'error' ? 'block' : 'none';
        reportInput.value = '';

        // Store context for error reporting
        container.dataset.errorContext = context;
        container.dataset.errorMessage = message;

        // Build actions
        actionsEl.innerHTML = '';

        if (type === 'error') {
            // Error: Must submit report to close
            const btn = document.createElement('button');
            btn.textContent = 'Send Report & Close';
            btn.className = 'popup-btn popup-btn-primary';
            btn.onclick = () => submitErrorReport();
            actionsEl.appendChild(btn);
        } else {
            const defaultActions = actions || [{ label: 'OK', onClick: hide, primary: true }];

            defaultActions.forEach(action => {
                const btn = document.createElement('button');
                btn.textContent = action.label;
                btn.className = action.primary ? 'popup-btn popup-btn-primary' : 'popup-btn';
                btn.onclick = () => {
                    if (action.onClick) action.onClick();
                    hide();
                };
                actionsEl.appendChild(btn);
            });
        }

        // Show
        container.classList.add('popup-visible');

        // Auto dismiss (not for errors)
        if (autoDismiss && type !== 'error') {
            setTimeout(hide, autoDismiss);
        }
    }

    async function submitErrorReport() {
        const reportInput = container.querySelector('.popup-report-input');
        const userDescription = reportInput.value.trim();

        // Description is optional - still send the report
        const report = {
            timestamp: new Date().toISOString(),
            userDescription: userDescription || '(No description provided)',
            errorMessage: container.dataset.errorMessage || '',
            context: container.dataset.errorContext || '',
            userAgent: navigator.userAgent,
            url: window.location.href
        };

        // Send to backend
        try {
            await fetch('/api/error-report', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(report)
            });
        } catch (e) {
            // Log locally if backend fails
            console.error('Error report:', report);
        }

        // Close and show thank you
        hide();
        setTimeout(() => {
            success('Thank you for the report!', 'Report Sent');
        }, 200);
    }

    function hide() {
        if (container) {
            container.classList.remove('popup-visible');
        }
    }

    function confirm(options = {}) {
        const { onConfirm, onCancel, confirmLabel = 'Confirm', cancelLabel = 'Cancel' } = options;

        show({
            ...options,
            type: 'confirm',
            actions: [
                { label: cancelLabel, onClick: onCancel, primary: false },
                { label: confirmLabel, onClick: onConfirm, primary: true }
            ]
        });
    }

    // Quick helpers
    function error(message, options = {}) {
        const title = options.title || 'Error';
        show({ type: 'error', title, message, context: options.context || '' });
    }

    function success(message, title = 'Success') {
        show({ type: 'success', title, message, autoDismiss: 3000 });
    }

    function warning(message, title = 'Warning') {
        show({ type: 'warning', title, message });
    }

    return { show, hide, confirm, error, success, warning };
})();

// Export for module systems
if (typeof module !== 'undefined') module.exports = Popup;
