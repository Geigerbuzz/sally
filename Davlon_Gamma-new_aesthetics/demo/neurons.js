// --- Neural Net Background Animation ---
// Designed to run on any page with the <canvas id="neural-bg"> element

document.addEventListener('DOMContentLoaded', () => {
    initNeuralNet();
});

function initNeuralNet() {
    const canvas = document.getElementById('neural-bg');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    let width, height;
    let particles = [];
    const connectionDistance = 120;
    // Miami/Davlon Palette
    const colors = ['#FF5733', '#33FF57', '#3357FF', '#FF33F5', '#33FFF5'];

    window.resizeNeuralBg = function () {
        if (canvas.parentElement) {
            width = canvas.width = canvas.parentElement.offsetWidth;
            height = canvas.height = canvas.parentElement.offsetHeight;

            // Dynamic Density: 1 particle per ~10000 pixels (High Density)
            const density = 10000;
            const newCount = Math.floor((width * height) / density);
            const particleCount = Math.max(60, Math.min(300, newCount));

            initParticles(particleCount);
        }
    };

    class Particle {
        constructor() {
            this.x = Math.random() * width;
            this.y = Math.random() * height;
            this.vx = (Math.random() - 0.5) * 1.5;
            this.vy = (Math.random() - 0.5) * 1.5;
            this.size = Math.random() * 3 + 2;
            this.color = colors[Math.floor(Math.random() * colors.length)];
        }

        update() {
            this.x += this.vx;
            this.y += this.vy;

            if (this.x < 0 || this.x > width) this.vx *= -1;
            if (this.y < 0 || this.y > height) this.vy *= -1;
        }

        draw() {
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fillStyle = this.color;
            ctx.fill();
        }
    }

    function initParticles(count) {
        particles = [];
        for (let i = 0; i < count; i++) {
            particles.push(new Particle());
        }
    }

    function animate() {
        if (!width || !height) return requestAnimationFrame(animate);

        ctx.clearRect(0, 0, width, height);
        // Access theme from body to adjust connection line visibility
        const isDark = document.body.getAttribute('data-theme') === 'dark';
        const baseColor = isDark ? '200, 200, 200' : '50, 50, 50';

        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const dx = particles[i].x - particles[j].x;
                const dy = particles[i].y - particles[j].y;
                const dist = Math.sqrt(dx * dx + dy * dy);

                if (dist < connectionDistance) {
                    ctx.beginPath();
                    ctx.strokeStyle = `rgba(${baseColor}, ${1 - dist / connectionDistance})`;
                    ctx.lineWidth = 1;
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.stroke();
                }
            }
        }

        particles.forEach(p => {
            p.update();
            p.draw();
        });

        requestAnimationFrame(animate);
    }

    window.addEventListener('resize', window.resizeNeuralBg);
    window.resizeNeuralBg(); // Call once immediately
    animate();
}
