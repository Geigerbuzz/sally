// --- Shared Sound Manager ---
// Centralized audio engine for consistent SFX across the app

const SoundManager = {
    ctx: null,
    masterGain: null,
    isReady: false,

    init: function () {
        if (!this.ctx) {
            this.ctx = new (window.AudioContext || window.webkitAudioContext)();
            this.masterGain = this.ctx.createGain();
            this.masterGain.gain.value = 0.5; // Master volume
            this.masterGain.connect(this.ctx.destination);
        }
        if (this.ctx.state === 'suspended') {
            this.ctx.resume().then(() => { this.isReady = true; });
        } else {
            this.isReady = true;
        }
    },

    muted: false,

    setMuted: function (isMuted) {
        this.muted = isMuted;
    },

    playTone: function (freq, startTime, duration) {
        if (this.muted) return;

        // Safety delay to ensure scheduling works during wake-up
        const t = startTime || this.ctx.currentTime;
        const safeStart = t + 0.01;

        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.connect(gain);
        gain.connect(this.masterGain);

        osc.type = 'sine';
        osc.frequency.value = freq;

        // Marimba envelope: Soft attack to avoid clicks
        gain.gain.setValueAtTime(0, safeStart);
        gain.gain.linearRampToValueAtTime(0.3, safeStart + 0.02);
        gain.gain.exponentialRampToValueAtTime(0.001, safeStart + duration);

        osc.start(safeStart);
        osc.stop(safeStart + duration);

        // Cleanup check
        setTimeout(() => {
            osc.disconnect();
            gain.disconnect();
        }, (duration + 0.1) * 1000);
    },

    // --- Widget Interaction Sounds ---

    playPop: function (cols = 2, rows = 1) { // Drag Start (High Chord)
        this.init();
        const t = this.ctx.currentTime;

        // Base Pitch (E4) modulated by Width (Wider = Lower)
        const widthShift = (2 - cols) * 2;
        const baseFreq = 329.63 * Math.pow(2, widthShift / 12);

        // Harmony modulated by Height (Taller = More complex/Grand)
        let interval = 4; // Major 3rd
        if (rows === 2) interval = 7; // Perfect 5th
        if (rows >= 3) interval = 11; // Major 7th

        const upperFreq = baseFreq * Math.pow(2, interval / 12);

        this.playTone(baseFreq, t, 0.2);
        this.playTone(upperFreq, t, 0.2);
    },

    playSnap: function (cols = 2, rows = 1) { // Drop (Low/Resolved Chord)
        this.init();
        const t = this.ctx.currentTime;

        // Base Pitch (B3) modulated by width
        const widthShift = (2 - cols) * 2;
        const baseFreq = 246.94 * Math.pow(2, widthShift / 12);

        // Snap Interval: Perfect 4th relative to root
        const upperFreq = baseFreq * Math.pow(2, 5 / 12);

        this.playTone(baseFreq, t, 0.2);
        this.playTone(upperFreq, t, 0.2);
    },

    playSuccess: function () { // Auto Arrange "Ta-da!"
        this.init();
        const t = this.ctx.currentTime;
        // Fast E Major Arpeggio: E4 -> G#4 -> B4 -> E5
        this.playTone(329.63, t + 0.00, 0.1);
        this.playTone(415.30, t + 0.05, 0.1);
        this.playTone(493.88, t + 0.10, 0.1);
        this.playTone(659.25, t + 0.15, 0.2);
    },

    // --- UI Toggle Sounds ---

    playToggleOn: function () {
        this.init();
        const t = this.ctx.currentTime;
        // Crisp Marimba Click (G#4) - "Tak"
        this.playTone(415.30, t, 0.1);
    },

    playToggleOff: function () {
        this.init();
        const t = this.ctx.currentTime;
        // Lower Marimba Click (E4) - "Tuk"
        this.playTone(329.63, t, 0.1);
    }
};

// Global Warmup Listener
const warmupAudio = () => {
    SoundManager.init();
    document.removeEventListener('mousedown', warmupAudio);
    document.removeEventListener('touchstart', warmupAudio);
};
document.addEventListener('mousedown', warmupAudio);
document.addEventListener('touchstart', warmupAudio);

// Expose to window
window.SoundManager = SoundManager;
