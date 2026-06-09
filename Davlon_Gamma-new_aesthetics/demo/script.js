document.addEventListener('DOMContentLoaded', () => {
    // --- Elements ---
    const themeToggle = document.getElementById('theme-toggle');
    const dockPosToggle = document.getElementById('dock-pos-toggle');
    const body = document.body;
    const themeIcon = themeToggle ? themeToggle.querySelector('i') : null;

    // --- State & Persistence ---
    const savedTheme = localStorage.getItem('theme') || 'dark';
    const savedDockPos = localStorage.getItem('dockPos') || 'left';

    // --- Initialization ---
    applyTheme(savedTheme);
    applyDockPos(savedDockPos);

    // --- Functions ---
    function applyTheme(theme) {
        body.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);

        if (themeIcon) {
            // Update Icon
            if (theme === 'dark') {
                themeIcon.classList.remove('ri-sun-line');
                themeIcon.classList.add('ri-moon-line');
            } else {
                themeIcon.classList.remove('ri-moon-line');
                themeIcon.classList.add('ri-sun-line');
            }
        }
    }

    function applyDockPos(pos) {
        if (pos === 'right') {
            body.classList.add('dock-right');
            if (dockPosToggle) dockPosToggle.checked = true;
        } else {
            body.classList.remove('dock-right');
            if (dockPosToggle) dockPosToggle.checked = false;
        }
        localStorage.setItem('dockPos', pos);
    }

    // --- Event Listeners ---

    // Theme Toggle
    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const currentTheme = body.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            applyTheme(newTheme);
        });
    }

    // Dock Position Toggle (Only active on settings page)
    if (dockPosToggle) {
        dockPosToggle.addEventListener('change', (e) => {
            const newPos = e.target.checked ? 'right' : 'left';
            applyDockPos(newPos);
        });
    }
});
