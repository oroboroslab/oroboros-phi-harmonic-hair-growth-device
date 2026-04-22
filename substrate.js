/* ============================================
   SUBSTRATE FIELD - Particle Animation
   Oroborian Medical Technology
   ============================================ */

(function () {
    const canvas = document.getElementById('substrate-field');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    let width, height;
    let particles = [];
    let connections = [];
    const PARTICLE_COUNT = 80;
    const CONNECTION_DISTANCE = 180;
    const GOLD = { r: 184, g: 184, b: 184 };

    function resize() {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
    }

    function createParticles() {
        particles = [];
        for (let i = 0; i < PARTICLE_COUNT; i++) {
            particles.push({
                x: Math.random() * width,
                y: Math.random() * height,
                vx: (Math.random() - 0.5) * 0.3,
                vy: (Math.random() - 0.5) * 0.3,
                radius: Math.random() * 1.5 + 0.5,
                alpha: Math.random() * 0.5 + 0.1,
                pulse: Math.random() * Math.PI * 2,
                pulseSpeed: Math.random() * 0.02 + 0.005
            });
        }
    }

    function update() {
        for (let i = 0; i < particles.length; i++) {
            const p = particles[i];
            p.x += p.vx;
            p.y += p.vy;
            p.pulse += p.pulseSpeed;

            // Wrap around edges
            if (p.x < 0) p.x = width;
            if (p.x > width) p.x = 0;
            if (p.y < 0) p.y = height;
            if (p.y > height) p.y = 0;
        }
    }

    function draw() {
        ctx.clearRect(0, 0, width, height);

        // Draw connections
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const dx = particles[i].x - particles[j].x;
                const dy = particles[i].y - particles[j].y;
                const dist = Math.sqrt(dx * dx + dy * dy);

                if (dist < CONNECTION_DISTANCE) {
                    const alpha = (1 - dist / CONNECTION_DISTANCE) * 0.15;
                    ctx.beginPath();
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.strokeStyle = `rgba(${GOLD.r}, ${GOLD.g}, ${GOLD.b}, ${alpha})`;
                    ctx.lineWidth = 0.5;
                    ctx.stroke();
                }
            }
        }

        // Draw particles
        for (let i = 0; i < particles.length; i++) {
            const p = particles[i];
            const pulseAlpha = p.alpha + Math.sin(p.pulse) * 0.15;
            const pulseRadius = p.radius + Math.sin(p.pulse) * 0.3;

            // Glow
            ctx.beginPath();
            ctx.arc(p.x, p.y, pulseRadius * 3, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(${GOLD.r}, ${GOLD.g}, ${GOLD.b}, ${pulseAlpha * 0.1})`;
            ctx.fill();

            // Core
            ctx.beginPath();
            ctx.arc(p.x, p.y, pulseRadius, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(${GOLD.r}, ${GOLD.g}, ${GOLD.b}, ${pulseAlpha})`;
            ctx.fill();
        }
    }

    function animate() {
        update();
        draw();
        requestAnimationFrame(animate);
    }

    // Scroll-triggered element visibility
    function handleScroll() {
        const elements = document.querySelectorAll('.arch-card, .ops-card, .target-card, .security-block');
        const windowHeight = window.innerHeight;

        elements.forEach(el => {
            const rect = el.getBoundingClientRect();
            if (rect.top < windowHeight * 0.85) {
                el.classList.add('visible');
            }
        });
    }

    // Initialize
    resize();
    createParticles();
    animate();

    window.addEventListener('resize', () => {
        resize();
    });

    window.addEventListener('scroll', handleScroll);

    // Trigger initial check
    setTimeout(handleScroll, 100);
})();
