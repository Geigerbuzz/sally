// --- Widgets Page Logic ---
// Handles Drag & Drop, Auto-Arrange, Real-Time Updates, and Add Widget Modal

document.addEventListener('DOMContentLoaded', () => {
    // Only run if we are on the dashboard
    const grid = document.getElementById('widget-grid');
    if (!grid) return;

    // --- Tab Switching Logic ---
    let teamHTML = grid.innerHTML; // Capture initial state (Team)
    const personalHTML = `
        <div class="widget w-2x1">
             <h3 style="margin-bottom: 8px;">Personal Dashboard</h3>
             <p style="color: var(--text-secondary); font-size: 14px;">Add your personal widgets here.</p>
        </div>
    `;

    const environmentHTML = `
        <!-- 1. Carbon Footprint (1x1) -->
        <div class="widget w-1x1" draggable="true" id="w-carbon">
            <i class="ri-leaf-line" style="font-size: 28px; margin-bottom: 8px; color: #32d74b;"></i>
            <h3 style="font-size: 14px;">Carbon Footprint</h3>
            <p class="live-num" style="font-size: 24px;">1,240 <span style="font-size: 12px; color: var(--text-secondary);">tCO2e</span></p>
        </div>

        <!-- 2. Compliance Score (2x1) -->
        <div class="widget w-2x1" draggable="true" id="w-compliance">
            <h3 style="margin-bottom: 8px;">ESG Compliance</h3>
            <div style="display: flex; align-items: center; gap: 16px;">
                <div style="font-size: 32px; font-weight: 600; color: #32d74b;">98%</div>
                <p style="font-size: 12px; color: var(--text-secondary);">On track for 2025 net-zero goals.</p>
            </div>
            <div style="width: 100%; height: 4px; background: rgba(255,255,255,0.1); margin-top: 12px; border-radius: 2px;">
                <div style="width: 98%; height: 100%; background: #32d74b; border-radius: 2px;"></div>
            </div>
        </div>

        <!-- 3. Energy Usage (1x1) -->
        <div class="widget w-1x1" draggable="true" id="w-energy">
            <i class="ri-flashlight-line" style="font-size: 28px; margin-bottom: 8px; color: #bf5af2;"></i>
            <h3 style="font-size: 14px;">Renewable Energy</h3>
            <p class="live-num" style="font-size: 24px;">85%</p>
        </div>
    `;

    const tabTeam = document.getElementById('tab-team');
    const tabPersonal = document.getElementById('tab-personal');
    const tabEnvironment = document.getElementById('tab-environment');

    function switchTab(activeTab, htmlContent) {
        [tabTeam, tabPersonal, tabEnvironment].forEach(t => t && t.classList.remove('active'));
        if (activeTab) activeTab.classList.add('active');

        grid.innerHTML = htmlContent;
        initShineEffect();

        // Re-attach drag events to new widgets if necessary or rely on bubbling (bubbling works for grid events, 
        // but new widgets don't have specialized event listeners if they were attached individually. 
        // Currently drag logic is on grid, so it should be fine.)
    }

    if (tabTeam && tabEnvironment && tabPersonal) {
        tabTeam.addEventListener('click', () => {
            if (activeTabIs(tabTeam)) return;
            switchTab(tabTeam, teamHTML);
        });

        tabPersonal.addEventListener('click', () => {
            if (activeTabIs(tabPersonal)) return;
            if (activeTabIs(tabTeam)) teamHTML = grid.innerHTML; // Save Team state
            switchTab(tabPersonal, personalHTML);
        });

        tabEnvironment.addEventListener('click', () => {
            if (activeTabIs(tabEnvironment)) return;
            if (activeTabIs(tabTeam)) teamHTML = grid.innerHTML; // Save Team state
            switchTab(tabEnvironment, environmentHTML);
        });
    }

    function activeTabIs(tab) {
        return tab.classList.contains('active');
    }

    // --- 1. Drag & Drop Engine (Unified Mouse & Touch + Ghost) ---
    let draggedItem = null;
    let clickOffset = { x: 0, y: 0 };
    let ghost = null;

    // Grid Constants (Must match CSS)
    const getGap = () => window.innerWidth <= 768 ? 12 : 24;

    const getMaxCols = () => {
        const w = window.innerWidth;
        if (w <= 768) return 2;   // Mobile
        if (w <= 1024) return 4;  // Tablet
        return 6;                 // Desktop
    };

    const getColWidth = () => {
        const cols = getMaxCols();
        const gap = getGap();
        const gridStyle = window.getComputedStyle(grid);
        const paddingLeft = parseFloat(gridStyle.paddingLeft) || 0;
        const paddingRight = parseFloat(gridStyle.paddingRight) || 0;

        // Use getBoundingClientRect().width for sub-pixel precision vs clientWidth (integer)
        const totalWidth = grid.getBoundingClientRect().width;
        const availableWidth = totalWidth - paddingLeft - paddingRight;

        const totalGapSpace = (cols - 1) * gap;
        return (availableWidth - totalGapSpace) / cols;
    };

    // Unified Grid Dimension Updates
    function updateGridDimensions() {
        const size = getColWidth();
        const gap = getGap();
        grid.style.setProperty('--cell-size', `${size}px`);
        grid.style.setProperty('--grid-gap', `${gap}px`);
        grid.style.setProperty('--bg-pitch', `${size + gap}px`);
        drawPegs(); // Redraw pegs on resize
    }

    // --- Draw Grid Pegs (DOM-based for precision) ---
    function drawPegs() {
        // Remove existing pegs
        grid.querySelectorAll('.grid-peg').forEach(p => p.remove());

        const widgets = grid.querySelectorAll('.widget');
        if (widgets.length === 0) return;

        const gridRect = grid.getBoundingClientRect();
        const gap = getGap();
        const halfGap = gap / 2;

        // Use a Set to deduplicate peg positions (widgets share corners)
        const pegPositions = new Set();

        widgets.forEach(widget => {
            const rect = widget.getBoundingClientRect();

            // Peg position = exact bottom-right corner of widget (where 4 widgets would meet)
            const pegX = rect.right - gridRect.left;
            const pegY = rect.bottom - gridRect.top;

            // Only add if within grid bounds (skip rightmost/bottommost edge widgets)
            if (pegX < gridRect.width - 10 && pegY < gridRect.height - 10) {
                // Round to avoid floating point duplicates
                const key = `${Math.round(pegX)},${Math.round(pegY)}`;
                pegPositions.add(key);
            }
        });

        // Create peg elements
        pegPositions.forEach(key => {
            const [x, y] = key.split(',').map(Number);
            const peg = document.createElement('div');
            peg.className = 'grid-peg';
            peg.style.left = `${x - 2}px`; // Center 4px dot
            peg.style.top = `${y - 2}px`;
            grid.appendChild(peg);
        });
    }

    // Call on load and resize
    updateGridDimensions();
    window.addEventListener('resize', updateGridDimensions);

    const getCellSize = () => getColWidth() + getGap();
    const USER_WIDGETS_KEY = 'davlon_user_widgets';

    // --- Sound Manager (Synthesized SFX) ---
    // Uses global SoundManager from sound_manager.js
    // Ensure SoundManager is initialized if not already
    if (window.SoundManager && !window.SoundManager.isReady) {
        // Warmup handled globally by sound_manager.js
    }

    // Persistence Helpers
    function saveUserWidget(widgetData) {
        const saved = JSON.parse(localStorage.getItem(USER_WIDGETS_KEY) || '[]');
        saved.push(widgetData);
        localStorage.setItem(USER_WIDGETS_KEY, JSON.stringify(saved));
    }

    function loadUserWidgets() {
        if (typeof WidgetRenderer === 'undefined') return;
        const saved = JSON.parse(localStorage.getItem(USER_WIDGETS_KEY) || '[]');
        saved.forEach(widgetData => {
            // Avoid duplicates if ID collision (e.g. static widgets vs saved)
            if (document.getElementById(widgetData.id)) return;
            try {
                const newWidget = WidgetRenderer.render(widgetData);
                grid.appendChild(newWidget);
                attachShineToWidget(newWidget);
            } catch (e) {
                console.error("Failed to restore widget", e);
            }
        });
    }

    // --- FLIP Animation Helper ---
    function animateGridChange(changeFn) {
        const widgets = Array.from(grid.querySelectorAll('.widget:not(.widget-ghost):not(.dragging)'));
        const firstPositions = new Map();

        widgets.forEach(w => {
            const rect = w.getBoundingClientRect();
            firstPositions.set(w, { left: rect.left, top: rect.top });
        });

        changeFn();

        requestAnimationFrame(() => {
            widgets.forEach(w => {
                const first = firstPositions.get(w);
                if (!first) return; // New widget or removed

                const rect = w.getBoundingClientRect();
                const deltaX = first.left - rect.left;
                const deltaY = first.top - rect.top;

                if (deltaX !== 0 || deltaY !== 0) {
                    w.style.transform = `translate(${deltaX}px, ${deltaY}px)`;
                    w.style.transition = 'transform 0s';

                    requestAnimationFrame(() => {
                        w.style.transform = '';
                        w.style.transition = 'transform 0.4s cubic-bezier(0.34, 1.3, 0.64, 1)'; // Spring snap
                    });
                }
            });
        });
    }

    // --- Confetti Effect for New Widgets ---
    function triggerConfetti(startX, startY) {
        const colors = ['#32d74b', '#ff9f0a', '#0a84ff', '#ff375f', '#bf5af2', '#ffd60a'];
        const particleCount = 30;

        for (let i = 0; i < particleCount; i++) {
            const particle = document.createElement('div');
            particle.style.position = 'fixed';
            particle.style.width = '6px';
            particle.style.height = '6px';
            particle.style.borderRadius = '50%';
            particle.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
            particle.style.left = startX + 'px';
            particle.style.top = startY + 'px';
            particle.style.pointerEvents = 'none';
            particle.style.zIndex = '9999';
            document.body.appendChild(particle);

            // Physics
            const angle = Math.random() * Math.PI * 2;
            const velocity = 2 + Math.random() * 4;
            let vx = Math.cos(angle) * velocity;
            let vy = Math.sin(angle) * velocity;
            let life = 1.0;

            const animate = () => {
                life -= 0.02;
                if (life <= 0) {
                    particle.remove();
                    return;
                }

                vy += 0.2; // Gravity
                vx *= 0.98; // Drag

                const currentLeft = parseFloat(particle.style.left);
                const currentTop = parseFloat(particle.style.top);

                particle.style.left = (currentLeft + vx) + 'px';
                particle.style.top = (currentTop + vy) + 'px';
                particle.style.opacity = life;

                requestAnimationFrame(animate);
            };
            requestAnimationFrame(animate);
        }
    }

    // --- Shine Effect (Mouse-following border glow) ---
    function initShineEffect() {
        const widgets = grid.querySelectorAll('.widget');
        widgets.forEach(widget => {
            widget.addEventListener('mousemove', (e) => {
                const rect = widget.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                widget.style.setProperty('--mouse-x', `${x}px`);
                widget.style.setProperty('--mouse-y', `${y}px`);
            });
        });
    }

    // Re-init shine effect when new widgets are added (call after widget creation)
    function attachShineToWidget(widget) {
        widget.addEventListener('mousemove', (e) => {
            const rect = widget.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            widget.style.setProperty('--mouse-x', `${x}px`);
            widget.style.setProperty('--mouse-y', `${y}px`);
        });
    }

    // Init shine effect on page load
    initShineEffect();

    // Ghost Management
    function createGhost(widget) {
        if (ghost) removeGhost();
        ghost = document.createElement('div');
        ghost.className = 'widget widget-ghost ' + Array.from(widget.classList).filter(c => c.startsWith('w-')).join(' ');

        // Copy width/height styles if needed for standard sizing
        const span = getWidgetSpan(widget);

        grid.appendChild(ghost);
        return ghost;
    }

    function updateGhost(x, y) {
        if (!ghost) return;

        const gridRect = grid.getBoundingClientRect();
        // Calculate grid cell relative to grid content
        // x,y are client coordinates of the POINTER/TOUCH
        const relX = x - gridRect.left + grid.scrollLeft - clickOffset.x;
        const relY = y - gridRect.top + grid.scrollTop - clickOffset.y;

        let col = Math.floor((relX + 5) / getCellSize()) + 1;
        let row = Math.floor((relY + 5) / getCellSize()) + 1;

        if (col < 1) col = 1;
        if (row < 1) row = 1;

        const span = getWidgetSpan(ghost);

        // Clamp column to maxCols to prevent overflow
        const maxCols = getMaxCols();
        if (col + span.cols - 1 > maxCols) {
            col = Math.max(1, maxCols - span.cols + 1);
        }
        ghost.style.gridColumn = `${col} / span ${span.cols}`;
        ghost.style.gridRow = `${row} / span ${span.rows}`;

        return { col, row };
    }

    function removeGhost() {
        if (ghost && ghost.parentNode) {
            ghost.parentNode.removeChild(ghost);
        }
        ghost = null;
    }

    function finalizeDrop(item, col, row) {
        animateGridChange(() => {
            const span = getWidgetSpan(item);
            resolveCollisions(item, col, row);
            item.style.gridColumn = `${col} / span ${span.cols}`;
            item.style.gridRow = `${row} / span ${span.rows}`;
        });
    }

    // Live Reordering State
    let dragStartSnapshot = new Map();
    let isDropped = false;
    let lastDragUpdate = 0;
    let lastPreviewCol = -1;
    let lastPreviewRow = -1;

    // --- Mouse Events ---
    grid.addEventListener('dragstart', (e) => {
        if (e.target.classList.contains('widget')) {
            draggedItem = e.target;
            const rect = draggedItem.getBoundingClientRect();
            clickOffset.x = e.clientX - rect.left;
            clickOffset.y = e.clientY - rect.top;

            // Play Sound based on dimensions
            const span = getWidgetSpan(draggedItem);
            SoundManager.playPop(span.cols, span.rows);

            // Capture Snapshot
            dragStartSnapshot.clear();
            isDropped = false;
            lastPreviewCol = -1;
            lastPreviewRow = -1;
            grid.querySelectorAll('.widget:not(.widget-ghost)').forEach(w => {
                dragStartSnapshot.set(w, {
                    col: w.style.gridColumn,
                    row: w.style.gridRow
                });
            });

            createGhost(draggedItem);

            setTimeout(() => e.target.classList.add('dragging'), 0);
            e.dataTransfer.effectAllowed = 'move';
        }
    });

    grid.addEventListener('dragend', (e) => {
        if (draggedItem) {
            draggedItem.classList.remove('dragging');

            // If NOT dropped, revert all positions
            if (!isDropped) {
                animateGridChange(() => {
                    dragStartSnapshot.forEach((styles, w) => {
                        w.style.gridColumn = styles.col;
                        w.style.gridRow = styles.row;
                    });
                });
            }

            removeGhost();
            draggedItem = null;
            dragStartSnapshot.clear();
        }
    });

    grid.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';

        // Throttle updates (50ms)
        const now = Date.now();
        if (now - lastDragUpdate < 50) return;
        lastDragUpdate = now;

        const targetPos = updateGhost(e.clientX, e.clientY);

        // Live Layout Preview
        if (targetPos && draggedItem) {
            // Only update if logical position changed (prevents jitter)
            if (targetPos.col === lastPreviewCol && targetPos.row === lastPreviewRow) return;
            lastPreviewCol = targetPos.col;
            lastPreviewRow = targetPos.row;

            animateGridChange(() => {
                // 1. Reset to original snapshot (so we calculate from clean state)
                dragStartSnapshot.forEach((styles, w) => {
                    // Don't reset dragged item (visual only) or ghost
                    if (w !== draggedItem) {
                        w.style.gridColumn = styles.col;
                        w.style.gridRow = styles.row;
                    }
                });
                // 2. Apply collisions for current potential drop
                resolveCollisions(draggedItem, targetPos.col, targetPos.row);
            });
        }
    });

    grid.addEventListener('drop', (e) => {
        e.preventDefault();
        if (!draggedItem) return;

        const targetPos = updateGhost(e.clientX, e.clientY); // Snap to final position
        if (targetPos) {
            isDropped = true; // Flag success

            const span = getWidgetSpan(draggedItem);
            SoundManager.playSnap(span.cols, span.rows);

            finalizeDrop(draggedItem, targetPos.col, targetPos.row);
        }
    });

    // --- Touch Events (Mobile Support) ---
    // --- Touch Events (Mobile Support: Long Press to Drag) ---
    let longPressTimer = null;
    let longPressStartPos = { x: 0, y: 0 };

    grid.addEventListener('touchstart', (e) => {
        let target = e.target;
        while (target && target !== grid && !target.classList.contains('widget')) {
            target = target.parentNode;
        }

        if (target && target.classList.contains('widget')) {
            const touch = e.touches[0];
            longPressStartPos = { x: touch.clientX, y: touch.clientY };

            // Start Long Press Timer (500ms)
            longPressTimer = setTimeout(() => {
                // TIMER FIRED: Enter Drag Mode
                draggedItem = target;
                const rect = draggedItem.getBoundingClientRect();
                clickOffset.x = touch.clientX - rect.left;
                clickOffset.y = touch.clientY - rect.top;

                // Visual Feedback
                draggedItem.classList.add('widget-long-press-active'); // Add pulse effect
                // Play Sound
                requestAnimationFrame(() => {
                    const s = getWidgetSpan(target);
                    SoundManager.playPop(s.cols, s.rows);
                });

                // Capture Snapshot for Revert
                dragStartSnapshot.clear();
                isDropped = false;
                lastPreviewCol = -1;
                lastPreviewRow = -1;

                grid.querySelectorAll('.widget:not(.widget-ghost)').forEach(w => {
                    dragStartSnapshot.set(w, {
                        col: w.style.gridColumn,
                        row: w.style.gridRow
                    });
                });

                createGhost(draggedItem);
                draggedItem.classList.add('dragging');

                // Haptic feedback if available (Mobile)
                if (navigator.vibrate) navigator.vibrate(50);

            }, 500); // 500ms hold required
        }
    }, { passive: true }); // Passive true allows scrolling to start immediately

    grid.addEventListener('touchmove', (e) => {
        const touch = e.touches[0];

        // If dragging hasn't started yet (timer running), check for scroll movement
        if (!draggedItem && longPressTimer) {
            const dist = Math.hypot(touch.clientX - longPressStartPos.x, touch.clientY - longPressStartPos.y);
            if (dist > 10) {
                // User moved finger > 10px before timer fired -> It's a scroll
                clearTimeout(longPressTimer);
                longPressTimer = null;
            }
            return; // Let native scroll happen
        }

        // If we ARE dragging (timer fired), handle drag logic
        if (draggedItem) {
            e.preventDefault(); // Stop scrolling while dragging

            const now = Date.now();
            if (now - lastDragUpdate < 50) return;
            lastDragUpdate = now;

            const targetPos = updateGhost(touch.clientX, touch.clientY);

            if (targetPos && draggedItem) {
                if (targetPos.col === lastPreviewCol && targetPos.row === lastPreviewRow) return;
                lastPreviewCol = targetPos.col;
                lastPreviewRow = targetPos.row;

                animateGridChange(() => {
                    dragStartSnapshot.forEach((styles, w) => {
                        if (w !== draggedItem) {
                            w.style.gridColumn = styles.col;
                            w.style.gridRow = styles.row;
                        }
                    });
                    resolveCollisions(draggedItem, targetPos.col, targetPos.row);
                });
            }
        }
    }, { passive: false }); // Passive false required to use preventDefault() in drag mode

    grid.addEventListener('touchend', (e) => {
        // Cancel timer if finger lifts early (Tap)
        if (longPressTimer) {
            clearTimeout(longPressTimer);
            longPressTimer = null;
        }

        if (draggedItem) {
            // Handle Drop
            const touch = e.changedTouches[0];
            const targetPos = updateGhost(touch.clientX, touch.clientY);

            if (targetPos) {
                isDropped = true;
                const span = getWidgetSpan(draggedItem);
                SoundManager.playSnap(span.cols, span.rows);
                finalizeDrop(draggedItem, targetPos.col, targetPos.row);
            }

            draggedItem.classList.remove('dragging');
            draggedItem.classList.remove('widget-long-press-active');
            removeGhost();
            draggedItem = null;
            dragStartSnapshot.clear();
        }
    });

    grid.addEventListener('touchcancel', (e) => {
        if (longPressTimer) {
            clearTimeout(longPressTimer);
            longPressTimer = null;
        }
        // ... cleanup cleanup ... 
        if (draggedItem) {
            draggedItem.classList.remove('dragging');
            removeGhost();
            draggedItem = null;
        }
    });

    grid.addEventListener('touchmove', (e) => {
        if (!draggedItem) return;
        e.preventDefault(); // Stop scrolling while dragging header/widget

        const now = Date.now();
        // Throttle updates (50ms)
        if (now - lastDragUpdate < 50) return;
        lastDragUpdate = now;

        const touch = e.touches[0];
        const targetPos = updateGhost(touch.clientX, touch.clientY);

        // Live Layout Preview (Touch)
        if (targetPos && draggedItem) {
            // Only update if logical position changed (prevents jitter)
            if (targetPos.col === lastPreviewCol && targetPos.row === lastPreviewRow) return;
            lastPreviewCol = targetPos.col;
            lastPreviewRow = targetPos.row;

            animateGridChange(() => {
                dragStartSnapshot.forEach((styles, w) => {
                    if (w !== draggedItem) {
                        w.style.gridColumn = styles.col;
                        w.style.gridRow = styles.row;
                    }
                });
                resolveCollisions(draggedItem, targetPos.col, targetPos.row);
            });
        }
    }, { passive: false });

    grid.addEventListener('touchend', (e) => {
        if (!draggedItem) return;

        // Use ghost position as final target
        let dropped = false;
        if (ghost) {
            const colStyle = ghost.style.gridColumn;
            const rowStyle = ghost.style.gridRow;
            const col = parseInt(colStyle.split('/')[0].trim());
            const row = parseInt(rowStyle.split('/')[0].trim());

            const span = getWidgetSpan(draggedItem);
            SoundManager.playSnap(span.cols, span.rows);
            dropped = true;
            isDropped = true;
            finalizeDrop(draggedItem, col, row);
        }

        if (!dropped) {
            animateGridChange(() => {
                dragStartSnapshot.forEach((styles, w) => {
                    w.style.gridColumn = styles.col;
                    w.style.gridRow = styles.row;
                });
            });
        }

        draggedItem.classList.remove('dragging');
        removeGhost();
        draggedItem = null;
        dragStartSnapshot.clear();
    });

    // --- Helper: Get widget span dimensions ---
    function getWidgetSpan(widget) {
        if (widget.classList.contains('w-2x2')) return { cols: 2, rows: 2 };
        if (widget.classList.contains('w-2x3')) return { cols: 2, rows: 3 };
        if (widget.classList.contains('w-1x2')) return { cols: 1, rows: 2 };
        if (widget.classList.contains('w-2x1')) return { cols: 2, rows: 1 };
        return { cols: 1, rows: 1 };
    }

    // --- Helper: Get widget's current grid position (always use DOM for accuracy) ---
    function getWidgetPosition(widget) {
        const span = getWidgetSpan(widget);

        // First try to get from explicit styles
        const colStyle = widget.style.gridColumn;
        const rowStyle = widget.style.gridRow;

        if (colStyle && rowStyle) {
            // Parse "2 / span 2" format
            const colMatch = colStyle.match(/(\d+)\s*\/\s*span\s*(\d+)/);
            const rowMatch = rowStyle.match(/(\d+)\s*\/\s*span\s*(\d+)/);

            if (colMatch && rowMatch) {
                return {
                    col: parseInt(colMatch[1]),
                    row: parseInt(rowMatch[1]),
                    spanCol: parseInt(colMatch[2]),
                    spanRow: parseInt(rowMatch[2])
                };
            }

            // Parse simple "2" format (just start position)
            const simpleCol = parseInt(colStyle);
            const simpleRow = parseInt(rowStyle);
            if (!isNaN(simpleCol) && !isNaN(simpleRow)) {
                return {
                    col: simpleCol,
                    row: simpleRow,
                    spanCol: span.cols,
                    spanRow: span.rows
                };
            }
        }

        // Fallback: calculate from DOM position using floor for consistency
        const rect = widget.getBoundingClientRect();
        const gridRect = grid.getBoundingClientRect();
        const relX = rect.left - gridRect.left + grid.scrollLeft;
        const relY = rect.top - gridRect.top + grid.scrollTop;

        // Use floor + 1 offset for more accurate cell detection
        // Adding small offset (5px) to avoid edge cases at cell boundaries
        const col = Math.floor((relX + 5) / getCellSize()) + 1;
        const row = Math.floor((relY + 5) / getCellSize()) + 1;

        return {
            col: Math.max(1, col),
            row: Math.max(1, row),
            spanCol: span.cols,
            spanRow: span.rows
        };
    }

    // --- Helper: Check if two widget positions overlap ---
    function positionsOverlap(pos1, pos2) {
        const left1 = pos1.col;
        const right1 = pos1.col + pos1.spanCol - 1;
        const top1 = pos1.row;
        const bottom1 = pos1.row + pos1.spanRow - 1;

        const left2 = pos2.col;
        const right2 = pos2.col + pos2.spanCol - 1;
        const top2 = pos2.row;
        const bottom2 = pos2.row + pos2.spanRow - 1;

        return !(right1 < left2 || left1 > right2 || bottom1 < top2 || top1 > bottom2);
    }

    // --- Helper: Find first available row for a widget ---
    function findNextAvailableRow(widget, allPositions, minRow = 1) {
        const span = getWidgetSpan(widget);
        let testRow = minRow;
        const maxIterations = 50; // Safety limit

        for (let i = 0; i < maxIterations; i++) {
            const testPos = { col: 1, row: testRow, spanCol: span.cols, spanRow: span.rows };
            let hasCollision = false;

            // Check all columns that could work
            for (let testCol = 1; testCol <= 6; testCol++) {
                testPos.col = testCol;
                hasCollision = allPositions.some(p => positionsOverlap(testPos, p));
                if (!hasCollision) return { col: testCol, row: testRow };
            }

            testRow++;
        }

        return { col: 1, row: testRow };
    }

    // --- Collision Resolution: Push overlapping widgets using cell tracking ---
    function resolveCollisions(droppedWidget, targetCol, targetRow) {
        const droppedSpan = getWidgetSpan(droppedWidget);

        // Track all cells that will be occupied by the dropped widget
        const droppedCells = new Set();
        for (let c = targetCol; c < targetCol + droppedSpan.cols; c++) {
            for (let r = targetRow; r < targetRow + droppedSpan.rows; r++) {
                droppedCells.add(`${c},${r}`);
            }
        }

        const widgets = Array.from(grid.querySelectorAll('.widget'));
        const otherWidgets = widgets.filter(w => w !== droppedWidget && !w.classList.contains('widget-ghost'));

        // Find widgets that overlap with dropped position
        const overlapping = [];
        const nonOverlapping = [];

        otherWidgets.forEach(w => {
            const pos = getWidgetPosition(w);
            let hasOverlap = false;

            // Check each cell of this widget against dropped cells
            for (let c = pos.col; c < pos.col + pos.spanCol && !hasOverlap; c++) {
                for (let r = pos.row; r < pos.row + pos.spanRow && !hasOverlap; r++) {
                    if (droppedCells.has(`${c},${r}`)) {
                        hasOverlap = true;
                    }
                }
            }

            if (hasOverlap) {
                overlapping.push(w);
            } else {
                nonOverlapping.push(w);
            }
        });

        if (overlapping.length === 0) return;

        // Build occupied cells set from dropped widget and non-overlapping widgets
        const occupiedCells = new Set(droppedCells);

        nonOverlapping.forEach(w => {
            const pos = getWidgetPosition(w);
            for (let c = pos.col; c < pos.col + pos.spanCol; c++) {
                for (let r = pos.row; r < pos.row + pos.spanRow; r++) {
                    occupiedCells.add(`${c},${r}`);
                }
            }
        });

        // Helper to find available position
        function findAvailablePosition(spanCol, spanRow) {
            const maxCols = getMaxCols();
            const effectiveMaxCols = Math.max(spanCol, maxCols);

            for (let row = 1; row <= 100; row++) {
                for (let col = 1; col <= effectiveMaxCols - spanCol + 1; col++) {
                    let isFree = true;
                    for (let c = col; c < col + spanCol && isFree; c++) {
                        for (let r = row; r < row + spanRow && isFree; r++) {
                            if (occupiedCells.has(`${c},${r}`)) {
                                isFree = false;
                            }
                        }
                    }
                    if (isFree) return { col, row };
                }
            }
            return { col: 1, row: 100 };
        }

        // Relocate each overlapping widget
        overlapping.forEach(widget => {
            const span = getWidgetSpan(widget);
            const newPos = findAvailablePosition(span.cols, span.rows);

            // Mark cells as occupied
            for (let c = newPos.col; c < newPos.col + span.cols; c++) {
                for (let r = newPos.row; r < newPos.row + span.rows; r++) {
                    occupiedCells.add(`${c},${r}`);
                }
            }

            // Apply position
            widget.style.gridColumn = `${newPos.col} / span ${span.cols}`;
            widget.style.gridRow = `${newPos.row} / span ${span.rows}`;
        });
    }

    grid.addEventListener('drop', (e) => {
        e.preventDefault();
        if (!draggedItem) return;

        const gridRect = grid.getBoundingClientRect();
        const dropX = e.clientX - gridRect.left + grid.scrollLeft - clickOffset.x;
        const dropY = e.clientY - gridRect.top + grid.scrollTop - clickOffset.y;

        const span = getWidgetSpan(draggedItem);

        // Calculate target grid cell
        let targetCol = Math.floor((dropX + 5) / getCellSize()) + 1;
        let targetRow = Math.floor((dropY + 5) / getCellSize()) + 1;

        if (targetCol < 1) targetCol = 1;
        if (targetRow < 1) targetRow = 1;

        // Clamp column to maxCols
        const maxCols = getMaxCols();
        if (targetCol + span.cols - 1 > maxCols) {
            targetCol = Math.max(1, maxCols - span.cols + 1);
        }

        // First resolve collisions (this will move other widgets out of the way)
        resolveCollisions(draggedItem, targetCol, targetRow);

        // Then place the dragged widget
        draggedItem.style.gridColumn = `${targetCol} / span ${span.cols}`;
        draggedItem.style.gridRow = `${targetRow} / span ${span.rows}`;
    });


    // --- 2. Auto Arrange Logic ---
    const autoArrangeBtn = document.getElementById('auto-arrange-btn');

    function performAutoArrange() {
        SoundManager.playPop(2, 2); // Generic "Medium" pop for button

        // Animate the entire grid rearrangement
        animateGridChange(() => {
            // Use bin-packing to calculate new positions
            lockWidgets();

            // After positions update, save state
            setTimeout(() => {
                SoundManager.playSuccess(); // Special "Ta-da" arpeggio
            }, 300); // Sync with animation end
        });
    }

    if (autoArrangeBtn) {
        autoArrangeBtn.addEventListener('click', performAutoArrange);
    }

    function lockWidgets() {
        const widgets = Array.from(grid.querySelectorAll('.widget'));

        // Track occupied cells using a Set of "col,row" strings
        const occupiedCells = new Set();

        // Helper to get widget span
        function getSpan(widget) {
            if (widget.classList.contains('w-2x2')) return { cols: 2, rows: 2 };
            if (widget.classList.contains('w-2x3')) return { cols: 2, rows: 3 };
            if (widget.classList.contains('w-1x2')) return { cols: 1, rows: 2 };
            if (widget.classList.contains('w-2x1')) return { cols: 2, rows: 1 };
            return { cols: 1, rows: 1 };
        }

        // Helper to mark cells as occupied
        function markOccupied(col, row, spanCol, spanRow) {
            for (let c = col; c < col + spanCol; c++) {
                for (let r = row; r < row + spanRow; r++) {
                    occupiedCells.add(`${c},${r}`);
                }
            }
        }

        // Helper to check if cells are free (ignores maxCols bounds - overflow is OK)
        function areCellsFree(col, row, spanCol, spanRow) {
            for (let c = col; c < col + spanCol; c++) {
                for (let r = row; r < row + spanRow; r++) {
                    if (occupiedCells.has(`${c},${r}`)) return false;
                }
            }
            return true;
        }

        // Helper to find first available position
        function findFirstAvailable(spanCol, spanRow, maxCols) {
            // Effective columns: at least spanCol to ensure widget can be placed
            const effectiveMaxCols = Math.max(spanCol, maxCols);

            for (let row = 1; row <= 100; row++) {
                for (let col = 1; col <= effectiveMaxCols - spanCol + 1; col++) {
                    if (areCellsFree(col, row, spanCol, spanRow)) {
                        return { col, row };
                    }
                }
            }
            // Absolute fallback: find any row that's completely free
            let fallbackRow = 1;
            while (fallbackRow <= 100) {
                if (areCellsFree(1, fallbackRow, spanCol, spanRow)) {
                    return { col: 1, row: fallbackRow };
                }
                fallbackRow++;
            }
            return { col: 1, row: fallbackRow };
        }

        // Calculate actual number of columns based on grid width
        const gridWidth = grid.clientWidth;
        // N * (COL_WIDTH + GAP) - GAP = gridWidth
        // N = (gridWidth + GAP) / (COL_WIDTH + GAP)
        // N * (COL_WIDTH + GAP) - GAP = gridWidth
        // N = (gridWidth + GAP) / (COL_WIDTH + GAP)
        const maxCols = getMaxCols();

        // Sort widgets: largest area first for better packing
        widgets.sort((a, b) => {
            const spanA = getSpan(a);
            const spanB = getSpan(b);
            return (spanB.cols * spanB.rows) - (spanA.cols * spanA.rows);
        });

        // Clear any existing positions first
        widgets.forEach(widget => {
            widget.style.gridColumn = '';
            widget.style.gridRow = '';
        });

        // Place each widget using bin-packing
        widgets.forEach(widget => {
            const span = getSpan(widget);

            // Find the first available position
            const pos = findFirstAvailable(span.cols, span.rows, maxCols);

            // Mark cells as occupied
            markOccupied(pos.col, pos.row, span.cols, span.rows);

            // Set explicit grid position
            widget.style.gridColumn = `${pos.col} / span ${span.cols}`;
            widget.style.gridRow = `${pos.row} / span ${span.rows}`;
        });
    }

    // --- 3. Run on Load (Default Configuration) ---
    // Use requestAnimationFrame to ensure DOM is fully rendered
    function initializeWidgets() {
        const gridWidth = grid.clientWidth;
        if (gridWidth < 100) {
            // Grid not ready yet, retry
            requestAnimationFrame(initializeWidgets);
            return;
        }
        loadUserWidgets(); // Restore saved widgets before arranging
        performAutoArrange();
        updateMobileCanvasHeight();
    }

    // --- Dynamic Canvas Height for Mobile ---
    // Prevents widget collisions by ensuring canvas is tall enough
    function updateMobileCanvasHeight() {
        const isMobile = window.innerWidth <= 768;

        if (!isMobile) {
            // Reset min-height on desktop
            grid.style.minHeight = '';
            return;
        }

        const widgets = Array.from(grid.querySelectorAll('.widget'));
        const GAP_MOBILE = getGap(); // Mobile gap
        const ROW_HEIGHT = getColWidth();

        // Calculate total height based on widget row spans
        let totalHeight = 0;
        widgets.forEach(widget => {
            let rowSpan = 1;
            if (widget.classList.contains('w-2x3')) rowSpan = 3;
            else if (widget.classList.contains('w-1x2') || widget.classList.contains('w-2x2')) rowSpan = 2;

            // Height = (rowSpan * ROW_HEIGHT) + ((rowSpan - 1) * GAP for internal gaps)
            const widgetHeight = rowSpan * ROW_HEIGHT + (rowSpan - 1) * GAP_MOBILE;
            totalHeight += widgetHeight + GAP_MOBILE; // Add gap between widgets
        });

        // Add one extra row for safety (prevents collision issues)
        const extraRow = ROW_HEIGHT + GAP_MOBILE;
        const minHeight = totalHeight + extraRow;

        grid.style.minHeight = `${minHeight}px`;
    }

    // Update canvas height on window resize
    window.addEventListener('resize', updateMobileCanvasHeight);

    // Start initialization after DOM is ready
    requestAnimationFrame(initializeWidgets);

    // --- 4. Real-Time Data Fetching ---
    // Fetches live data from backend and updates default widgets

    async function fetchAndUpdateWidgets() {
        try {
            const response = await fetch('/api/widgets/data');
            if (!response.ok) {
                console.warn('Widget data API returned:', response.status);
                return;
            }
            const data = await response.json();
            console.log('Widget data received:', data);

            // Update Active Listings widget
            const listingsWidget = document.getElementById('w-listings');
            if (listingsWidget && data.listings) {
                const numEl = listingsWidget.querySelector('.live-num');
                if (numEl) {
                    animateNumber(numEl, data.listings.active);
                }
            }

            // Update Revenue YTD widget
            const revenueWidget = document.getElementById('w-revenue');
            if (revenueWidget && data.revenue) {
                const currencyEl = revenueWidget.querySelector('.live-currency');
                if (currencyEl) {
                    currencyEl.textContent = `$${data.revenue.current}${data.revenue.unit}`;
                }
                // Update mini chart
                const chartContainer = revenueWidget.querySelector('.chart-mini');
                if (chartContainer && data.revenueChart && data.revenueChart.values.length > 0) {
                    renderMiniChart(chartContainer, data.revenueChart.values);
                }
            }

            // Update New Leads widget
            const leadsWidget = document.getElementById('w-leads');
            if (leadsWidget && data.leads) {
                const numEl = leadsWidget.querySelector('.live-num');
                if (numEl) {
                    animateNumber(numEl, data.leads.new);
                }
            }

            // Update Avg Days on Market widget
            const domWidget = document.getElementById('w-marketdays');
            if (domWidget && data.avgDOM) {
                const numEl = domWidget.querySelector('.live-num');
                if (numEl) {
                    animateNumber(numEl, data.avgDOM.days);
                }
            }

            // Update Pipeline Stages widget
            const pipelineWidget = document.getElementById('w-pipeline');
            if (pipelineWidget && data.pipeline && data.pipeline.stages.length > 0) {
                renderPipelineStages(pipelineWidget, data.pipeline.stages);
            }

            // Update Recent Sales widget
            const salesWidget = document.getElementById('w-sales');
            if (salesWidget && data.recentSales && data.recentSales.length > 0) {
                renderRecentSales(salesWidget, data.recentSales);
            }

        } catch (e) {
            console.error('Failed to fetch widget data:', e);
        }
    }

    // Helper: Animate number change
    function animateNumber(element, targetValue) {
        const currentValue = parseInt(element.textContent) || 0;
        if (currentValue === targetValue) return;

        const duration = 500;
        const startTime = performance.now();

        function update(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3); // Ease out cubic
            const value = Math.round(currentValue + (targetValue - currentValue) * eased);
            element.textContent = value;

            if (progress < 1) {
                requestAnimationFrame(update);
            }
        }
        requestAnimationFrame(update);
    }

    // Helper: Render mini bar chart
    function renderMiniChart(container, values) {
        const max = Math.max(...values);
        container.innerHTML = values.map(v => {
            const height = max > 0 ? (v / max * 100) : 0;
            return `<div style="flex: 1; height: ${height}%; background: linear-gradient(to top, var(--accent), rgba(10,132,255,0.3)); border-radius: 3px; min-height: 4px;"></div>`;
        }).join('');
    }

    // Helper: Render pipeline stages
    function renderPipelineStages(widget, stages) {
        const contentArea = widget.querySelector('div[style*="flex: 1"]') || widget.querySelector('div:last-child');
        if (!contentArea) return;

        const total = stages.reduce((sum, s) => sum + s.count, 0);

        contentArea.innerHTML = stages.map(stage => {
            const pct = total > 0 ? (stage.count / total * 100) : 0;
            return `
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 12px; color: var(--text-secondary); width: 80px;">${stage.name}</span>
                    <div style="flex: 1; height: 8px; background: rgba(255,255,255,0.1); border-radius: 4px; overflow: hidden;">
                        <div style="width: ${pct}%; height: 100%; background: ${stage.color}; border-radius: 4px; transition: width 0.5s ease;"></div>
                    </div>
                    <span style="font-size: 12px; font-weight: 600; color: var(--text-primary); width: 30px; text-align: right;">${stage.count}</span>
                </div>
            `;
        }).join('');
    }

    // Helper: Render recent sales
    function renderRecentSales(widget, sales) {
        const contentArea = widget.querySelector('div[style*="flex-direction: column"]');
        if (!contentArea) return;

        contentArea.innerHTML = sales.map(sale => `
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.05);">
                <div>
                    <div style="font-size: 13px; color: var(--text-primary);">${sale.address}</div>
                    <div style="font-size: 11px; color: var(--text-secondary);">${sale.daysAgo}d ago</div>
                </div>
                <span style="font-size: 14px; font-weight: 600; color: #30d158;">${sale.price}</span>
            </div>
        `).join('');
    }

    // Initial fetch + polling every 5 seconds
    fetchAndUpdateWidgets();
    setInterval(fetchAndUpdateWidgets, 5000);


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

        // --- 6. Generate Button Logic (Real API Call) ---
        const generateBtn = document.getElementById('ai-generate-action');
        if (generateBtn) {
            generateBtn.addEventListener('click', async () => {
                const prompt = aiInput.value.trim();
                if (!prompt) return;

                // Disable button while loading
                generateBtn.disabled = true;
                generateBtn.innerHTML = '<i class="ri-loader-4-line" style="animation: spin 1s linear infinite;"></i> Generating...';

                try {
                    const response = await fetch('/api/generate-widget', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ prompt })
                    });

                    const result = await response.json();

                    if (result.status === 'success' && result.widget) {
                        // Render the widget using WidgetRenderer
                        const newWidget = WidgetRenderer.render(result.widget);
                        grid.appendChild(newWidget);

                        // Attach shine effect to new widget
                        attachShineToWidget(newWidget);

                        // Trigger Confetti
                        // Calculate center of the new widget for the blast origin
                        setTimeout(() => {
                            const rect = newWidget.getBoundingClientRect();
                            const centerX = rect.left + rect.width / 2;
                            const centerY = rect.top + rect.height / 2;
                            triggerConfetti(centerX, centerY);
                        }, 100); // Wait for render/animation to settle slightly

                        // Persist
                        saveUserWidget(result.widget);

                        // Close modal and re-arrange
                        closeModal();
                        setTimeout(() => {
                            performAutoArrange();
                            updateMobileCanvasHeight();
                        }, 100);
                    } else {
                        alert('Widget generation failed: ' + (result.message || 'Unknown error'));
                    }
                } catch (e) {
                    console.error('Widget generation error:', e);
                    alert('Failed to generate widget. Check console for details.');
                } finally {
                    // Re-enable button
                    generateBtn.disabled = false;
                    generateBtn.innerHTML = '<i class="ri-magic-line"></i> Generate';
                }
            });
        }
    }
});
