/**
 * Mainpage
 * Hero cinematográfica + cartazes + parallax + partículas.
 */

(function () {
  'use strict';

  const SELECTOR_HOLDER = '.hero-scene__holder[data-url]';
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  let rafParallax = null;
  let targetX = 0;
  let targetY = 0;
  let currentX = 0;
  let currentY = 0;

  function revelarCena() {
    const cena = document.getElementById('mainpage-hero');

    if (cena) {
      requestAnimationFrame(() => {
        cena.classList.add('hero-scene--visivel');
      });
    }
  }

  function navegar(url) {
    if (url) {
      window.location.href = url;
    }
  }

  function ligarCartazes() {

  document.querySelectorAll(SELECTOR_HOLDER).forEach(holder => {

    function iniciarQueda() {

    if (holder.classList.contains('hero-scene__holder--caindo')) {
        return;
    }

    holder.classList.add('hero-scene__holder--caindo');

    holder.classList.add('hero-scene__holder--balanco');

    setTimeout(() => {

        holder.classList.remove('hero-scene__holder--balanco');

        holder.classList.add('hero-scene__holder--queda');

    }, 300);

    setTimeout(() => {

        navegar(holder.dataset.url);

    }, 1300);
}

    holder.addEventListener('click', iniciarQueda);

    holder.addEventListener('keydown', e => {

      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        iniciarQueda();
      }

    });

  });

}

  function ligarParallax() {

    if (reducedMotion) return;

    const cena = document.getElementById('mainpage-hero');
    const ambiente = document.getElementById('hero-ambiente');
    const feixes = document.getElementById('hero-feixes');
    const mural = document.getElementById('hero-mural');

    if (!cena || !ambiente) return;

    cena.addEventListener('mousemove', e => {

      const rect = cena.getBoundingClientRect();

      const nx = (e.clientX - rect.left) / rect.width - 0.5;
      const ny = (e.clientY - rect.top) / rect.height - 0.5;

      targetX = nx * 14;
      targetY = ny * 10;

    }, { passive: true });

    cena.addEventListener('mouseleave', () => {
      targetX = 0;
      targetY = 0;
    });

    function loop() {

      currentX += (targetX - currentX) * 0.06;
      currentY += (targetY - currentY) * 0.06;

      ambiente.style.transform =
        `perspective(900px) rotateY(${currentX * 0.12}deg) rotateX(${-currentY * 0.1}deg)`;

      if (feixes) {
        feixes.style.transform =
          `translate(${currentX * 0.6}px, ${currentY * 0.4}px)`;
      }

      if (mural) {
        mural.style.transform =
          `translate(${currentX * 0.15}px, ${currentY * 0.1}px)`;
      }

      rafParallax = requestAnimationFrame(loop);
    }

    loop();
  }

  function ligarPo() {

    if (reducedMotion) return;

    const canvas = document.getElementById('hero-po');
    const cena = document.getElementById('mainpage-hero');

    if (!canvas || !cena) return;

    const ctx = canvas.getContext('2d');

    let particles = [];
    let w = 0;
    let h = 0;

    function resize() {

      const dpr = Math.min(window.devicePixelRatio || 1, 2);

      const rect = cena.getBoundingClientRect();

      w = rect.width;
      h = rect.height;

      canvas.width = w * dpr;
      canvas.height = h * dpr;

      canvas.style.width = `${w}px`;
      canvas.style.height = `${h}px`;

      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      const count = Math.floor((w * h) / 9000);

      particles = Array.from({ length: count }, () => ({
        x: Math.random() * w,
        y: Math.random() * h * 0.85,
        r: 0.4 + Math.random() * 1.2,
        vx: (Math.random() - 0.5) * 0.15,
        vy: -0.08 - Math.random() * 0.2,
        a: 0.15 + Math.random() * 0.45
      }));
    }

    function draw() {

      ctx.clearRect(0, 0, w, h);

      particles.forEach(p => {

        p.x += p.vx;
        p.y += p.vy;

        if (p.y < 0) {
          p.y = h * 0.65;
          p.x = Math.random() * w;
        }

        if (p.x < 0 || p.x > w) {
          p.vx *= -1;
        }

        const dx = (p.x / w) - 0.5;
        const dy = (p.y / h) - 0.42;

        const zona =
          Math.max(
            0,
            1 - Math.abs(dx) * 1.8 - Math.abs(dy) * 1.4
          );

        const alpha = p.a * zona;

        if (alpha < 0.02) return;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);

        ctx.fillStyle =
          `rgba(255, 235, 200, ${alpha})`;

        ctx.fill();
      });

      requestAnimationFrame(draw);
    }

    resize();

    window.addEventListener('resize', resize, {
      passive: true
    });

    draw();
  }

  function init() {
    revelarCena();
    ligarCartazes();
    ligarParallax();
    ligarPo();
  }

  document.addEventListener('DOMContentLoaded', init);

  

})();