document.addEventListener('DOMContentLoaded', () => {
    // --- Elements ---
    const themeToggle = document.getElementById('theme-toggle'); // Dock button
    const themeToggleSetting = document.getElementById('theme-toggle-setting'); // Settings checkbox
    const soundToggleSetting = document.getElementById('sound-toggle-setting'); // NEW
    const dockPosToggle = document.getElementById('dock-pos-toggle');
    const dockMobilePosToggle = document.getElementById('dock-mobile-pos-toggle');
    const body = document.body;
    const themeIcon = themeToggle ? themeToggle.querySelector('i') : null;

    // --- State & Persistence ---
    const savedTheme = localStorage.getItem('theme') || 'dark';
    const savedDockPos = localStorage.getItem('dockPos') || 'left';
    const savedDockMobilePos = localStorage.getItem('dockMobilePos') || 'bottom';
    const savedSound = localStorage.getItem('soundEnabled') !== 'false'; // Default true

    // --- Initialization ---
    applyTheme(savedTheme);
    applyDockPos(savedDockPos);
    applyDockMobilePos(savedDockMobilePos);

    // Apply sound setting globally if SoundManager exists
    if (window.SoundManager) {
        window.SoundManager.setMuted(!savedSound);
    }

    // --- Functions ---
    function applyTheme(theme) {
        body.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);

        // Update dock button icon
        if (themeIcon) {
            if (theme === 'dark') {
                themeIcon.classList.remove('ri-sun-line');
                themeIcon.classList.add('ri-moon-line');
            } else {
                themeIcon.classList.remove('ri-moon-line');
                themeIcon.classList.add('ri-sun-line');
            }
        }

        // Sync settings checkbox if present
        if (themeToggleSetting) {
            themeToggleSetting.checked = (theme === 'dark');
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

    function applyDockMobilePos(pos) {
        if (pos === 'top') {
            body.classList.add('dock-top');
            if (dockMobilePosToggle) dockMobilePosToggle.checked = true;
        } else {
            body.classList.remove('dock-top');
            if (dockMobilePosToggle) dockMobilePosToggle.checked = false;
        }
        localStorage.setItem('dockMobilePos', pos);
    }

    // --- Event Listeners ---

    // Theme Toggle (Dock button - desktop only visible)
    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const currentTheme = body.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            applyTheme(newTheme);
        });
    }

    // Theme Toggle (Settings checkbox)
    if (themeToggleSetting) {
        themeToggleSetting.addEventListener('change', (e) => {
            const newTheme = e.target.checked ? 'dark' : 'light';
            applyTheme(newTheme);
            if (e.target.checked) window.SoundManager?.playToggleOn();
            else window.SoundManager?.playToggleOff();
        });
    }

    // Dock Position Toggle (Desktop - left/right)
    if (dockPosToggle) {
        dockPosToggle.addEventListener('change', (e) => {
            const newPos = e.target.checked ? 'right' : 'left';
            applyDockPos(newPos);
            if (e.target.checked) window.SoundManager?.playToggleOn();
            else window.SoundManager?.playToggleOff();
        });
    }

    // Dock Position Toggle (Mobile - top/bottom)
    if (dockMobilePosToggle) {
        dockMobilePosToggle.addEventListener('change', (e) => {
            const newPos = e.target.checked ? 'top' : 'bottom';
            applyDockMobilePos(newPos);
            if (e.target.checked) window.SoundManager?.playToggleOn();
            else window.SoundManager?.playToggleOff();
        });
    }

    // Sound Toggle
    if (soundToggleSetting) {
        soundToggleSetting.checked = savedSound;
        soundToggleSetting.addEventListener('change', (e) => {
            const isEnabled = e.target.checked;
            localStorage.setItem('soundEnabled', isEnabled);

            if (window.SoundManager) {
                window.SoundManager.setMuted(!isEnabled);
                if (isEnabled) window.SoundManager.playToggleOn();
                // No sound for off
            }
        });
    }
});

