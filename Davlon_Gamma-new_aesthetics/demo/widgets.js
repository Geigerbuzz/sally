// --- Widgets Page Logic ---
// Handles Drag & Drop, Auto-Arrange, Real-Time Updates, and Add Widget Modal

document.addEventListener('DOMContentLoaded', () => {
    // Only run if we are on the dashboard
    const grid = document.getElementById('widget-grid');
    if (!grid) return;

    // --- 1. Drag & Drop Engine ---
    let draggedItem = null;
    let clickOffset = { x: 0, y: 0 };

    // Grid Constants (Must match CSS)
    const COL_WIDTH = 160;
    const GAP = 24;
    const CELL_SIZE = COL_WIDTH + GAP;

    grid.addEventListener('dragstart', (e) => {
        if (e.target.classList.contains('widget')) {
            draggedItem = e.target;
            const rect = draggedItem.getBoundingClientRect();
            clickOffset.x = e.clientX - rect.left;
            clickOffset.y = e.clientY - rect.top;

            e.target.classList.add('dragging');
            e.dataTransfer.effectAllowed = 'move';
        }
    });

    grid.addEventListener('dragend', (e) => {
        if (e.target.classList.contains('widget')) {
            e.target.classList.remove('dragging');
            draggedItem = null;
        }
    });

    grid.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
    });

    grid.addEventListener('drop', (e) => {
        e.preventDefault();
        if (!draggedItem) return;

        const gridRect = grid.getBoundingClientRect();
        const dropX = e.clientX - gridRect.left + grid.scrollLeft - clickOffset.x;
        const dropY = e.clientY - gridRect.top + grid.scrollTop - clickOffset.y;

        let spanCol = 1, spanRow = 1;
        if (draggedItem.classList.contains('w-2x2')) { spanCol = 2; spanRow = 2; }
        else if (draggedItem.classList.contains('w-2x3')) { spanCol = 2; spanRow = 3; }
        else if (draggedItem.classList.contains('w-1x2')) { spanCol = 1; spanRow = 2; }
        else if (draggedItem.classList.contains('w-2x1')) { spanCol = 2; spanRow = 1; }

        let targetCol = Math.round(dropX / CELL_SIZE) + 1;
        let targetRow = Math.round(dropY / CELL_SIZE) + 1;

        if (targetCol < 1) targetCol = 1;
        if (targetRow < 1) targetRow = 1;

        draggedItem.style.gridColumn = `${targetCol} / span ${spanCol}`;
        draggedItem.style.gridRow = `${targetRow} / span ${spanRow}`;
    });


    // --- 2. Auto Arrange Logic ---
    const autoArrangeBtn = document.getElementById('auto-arrange-btn');

    function performAutoArrange() {
        // Sort widgets by area (largest to smallest) for dense packing
        const widgets = Array.from(grid.querySelectorAll('.widget'));

        widgets.sort((a, b) => {
            const getArea = (el) => {
                let w = 1, h = 1;
                if (el.classList.contains('w-2x2')) { w = 2; h = 2; }
                else if (el.classList.contains('w-2x3')) { w = 2; h = 3; }
                else if (el.classList.contains('w-1x2')) { w = 1; h = 2; }
                else if (el.classList.contains('w-2x1')) { w = 2; h = 1; }
                return w * h;
            };
            return getArea(b) - getArea(a);
        });

        // 1. Reset positions and re-append in sorted order (Dense Flow)
        widgets.forEach(widget => {
            widget.style.gridColumn = '';
            widget.style.gridRow = '';
            grid.appendChild(widget);
        });

        // Temporarily enable dense auto-flow handled by CSS/Browser
        grid.style.gridAutoFlow = 'dense';

        // 2. Lock them in place after a brief timeout (simulating the packing)
        setTimeout(() => {
            lockWidgets();
            grid.style.gridAutoFlow = ''; // Remove auto-flow so user can drag freely again
        }, 100);
    }

    if (autoArrangeBtn) {
        autoArrangeBtn.addEventListener('click', performAutoArrange);
    }

    function lockWidgets() {
        const widgets = grid.querySelectorAll('.widget');
        widgets.forEach(widget => {
            if (widget.style.gridColumnStart) return; // Already locked?

            const rect = widget.getBoundingClientRect();
            const gridRect = grid.getBoundingClientRect();

            const relativeX = rect.left - gridRect.left + grid.scrollLeft;
            const relativeY = rect.top - gridRect.top + grid.scrollTop;

            let col = Math.round(relativeX / CELL_SIZE) + 1;
            let row = Math.round(relativeY / CELL_SIZE) + 1;

            if (col < 1) col = 1;
            if (row < 1) row = 1;

            let spanCol = 1, spanRow = 1;
            if (widget.classList.contains('w-2x2')) { spanCol = 2; spanRow = 2; }
            else if (widget.classList.contains('w-2x3')) { spanCol = 2; spanRow = 3; }
            else if (widget.classList.contains('w-1x2')) { spanCol = 1; spanRow = 2; }
            else if (widget.classList.contains('w-2x1')) { spanCol = 2; spanRow = 1; }

            widget.style.gridColumn = `${col} / span ${spanCol}`;
            widget.style.gridRow = `${row} / span ${spanRow}`;
        });
    }

    // --- 3. Run on Load (Default Configuration) ---
    // User requested "Default configuration should be the auto-arrange result"
    setTimeout(() => {
        performAutoArrange();
        initRealTimeData();
    }, 100);


    // --- 4. Real-Time Data Simulation ---
    function initRealTimeData() {
        const revenueChart = document.querySelector('#w-revenue .chart-mini');
        if (revenueChart && revenueChart.childElementCount === 0) {
            for (let i = 0; i < 15; i++) {
                const bar = document.createElement('div');
                bar.style.width = '6px';
                bar.style.borderRadius = '2px';
                bar.style.backgroundColor = (i === 14) ? '#32d74b' : 'var(--accent)';
                bar.style.opacity = (i === 14) ? '1' : '0.5';
                bar.style.height = Math.floor(Math.random() * 80 + 20) + '%';
                bar.style.transition = 'height 0.4s ease';
                revenueChart.appendChild(bar);
            }
        }
        setInterval(simulateUpdates, 2000);
    }

    function simulateUpdates() {
        // Randomly update numbers
        document.querySelectorAll('.live-num').forEach(el => {
            if (Math.random() > 0.8) {
                let current = parseInt(el.innerText);
                let change = Math.floor(Math.random() * 3) - 1;
                el.innerText = Math.max(0, current + change);
                el.style.color = change > 0 ? '#32d74b' : (change < 0 ? '#ff453a' : '');
                setTimeout(() => el.style.color = '', 500);
            }
        });

        // Animate Revenue Chart
        const bars = document.querySelectorAll('#w-revenue .chart-mini div');
        if (bars.length) {
            bars.forEach(bar => {
                if (Math.random() > 0.7) {
                    let h = parseInt(bar.style.height);
                    let newH = h + (Math.random() * 20 - 10);
                    bar.style.height = Math.max(10, Math.min(100, newH)) + '%';
                }
            });
        }
    }


    // --- 5. Add Widget Modal Logic ---
    const fab = document.getElementById('add-widget-btn');
    const modalOverlay = document.getElementById('ai-modal-overlay');

    if (fab && modalOverlay) {
        const modalCloseBtn = modalOverlay.querySelector('.close-btn');
        const aiInput = modalOverlay.querySelector('.ai-input');

        const autoResize = () => {
            aiInput.style.height = 'auto';
            aiInput.style.height = aiInput.scrollHeight + 'px';
        };

        aiInput.addEventListener('input', autoResize);

        fab.addEventListener('click', () => {
            modalOverlay.classList.add('active');
            fab.style.display = 'none';
            aiInput.value = '';
            aiInput.style.height = 'auto';
            aiInput.focus();
        });

        const closeModal = () => {
            modalOverlay.classList.remove('active');
            fab.style.display = 'flex';
        };

        modalCloseBtn.addEventListener('click', closeModal);

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && modalOverlay.classList.contains('active')) {
                closeModal();
            }
        });
    }
});
