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

  /* ============================================================
   CONTINUAÇÃO de mainpage.js
   Cola este bloco no FINAL do teu mainpage.js (depois de toda a
   lógica do hero/cartazes que já tens).

   Dependências (via CDN no template):
     - gsap
     - ScrollTrigger
     - Lenis  (window.Lenis)

   Funciona em "no-op" se o utilizador tiver
   prefers-reduced-motion ativo, ou se for mobile (<= 880px),
   ou se faltar alguma lib — o CSS já garante o fallback.
   ============================================================ */

(function inicializarCenas() {

    const reduzir = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const mobile  = window.matchMedia('(max-width: 880px)').matches;

    const semGsap  = typeof window.gsap === 'undefined';
    const semST    = typeof window.ScrollTrigger === 'undefined';
    const semLenis = typeof window.Lenis === 'undefined';

    /* ---------- elementos ---------- */
    const cenas    = document.getElementById('cenas-horizontais');
    const track    = document.getElementById('cenas-track');
    const hero     = document.getElementById('mainpage-hero');
    const cursor   = document.getElementById('cursor-custom');
    const rotulo   = cursor && cursor.querySelector('.cursor__rotulo');
    const somBtn   = document.getElementById('som-toggle');
    const pontos   = document.querySelectorAll('.progresso__ponto');
    const titulo   = document.querySelector('[data-letras]');

    if (!cenas || !track || !hero) return;

    /* ========================================================
       0. Quebrar o título em letras (sempre — não custa nada)
       ======================================================== */
    if (titulo && !titulo.dataset.dividido) {
        const texto = titulo.textContent.trim();
        titulo.textContent = '';
        [...texto].forEach((c) => {
            const span = document.createElement('span');
            span.className = 'ch';
            span.textContent = c === ' ' ? '\u00A0' : c;
            titulo.appendChild(span);
        });
        titulo.dataset.dividido = '1';
    }

    /* ========================================================
       1. Cursor customizado
       ======================================================== */
    if (cursor && !mobile) {
        let mx = 0, my = 0, cx = 0, cy = 0;

        document.addEventListener('pointermove', (e) => {
            mx = e.clientX; my = e.clientY;
        });

        function tick() {
            cx += (mx - cx) * 0.22;
            cy += (my - cy) * 0.22;
            cursor.style.transform = `translate(${cx}px, ${cy}px)`;
            requestAnimationFrame(tick);
        }
        tick();

        // contextual por secção
        const obs = new IntersectionObserver((entries) => {
            entries.forEach((en) => {
                if (!en.isIntersecting) return;
                if (en.target.classList.contains('cena--violao')) {
                    cursor.style.setProperty('--cursor-cor', '#d4a574');
                    cursor.style.setProperty('--cursor-tam', '14px');
                } else {
                    cursor.style.setProperty('--cursor-cor', '#f4ecd8');
                    cursor.style.setProperty('--cursor-tam', '16px');
                }
            });
        }, { threshold: 0.4 });
        document.querySelectorAll('.cena, .cenas__slot--hero').forEach(s => obs.observe(s));

        // cresce em elementos interativos
        document.querySelectorAll('a, button, [role="link"], .polaroid, .etiqueta, [data-audio-acorde]')
            .forEach(el => {
                el.addEventListener('pointerenter', () => {
                    cursor.style.setProperty('--cursor-tam', '42px');
                    const r = el.getAttribute('data-cursor');
                    if (r && rotulo) { rotulo.textContent = r; cursor.classList.add('cursor--rotulo'); }
                });
                el.addEventListener('pointerleave', () => {
                    cursor.style.setProperty('--cursor-tam', '14px');
                    cursor.classList.remove('cursor--rotulo');
                });
            });
    }

    /* ========================================================
       2. Áudio — acorde dedilhado de Mi menor via Web Audio
       ======================================================== */
    let audioCtx = null;
    let somLigado = false;

    function garantirCtx() {
        if (!audioCtx) {
            const C = window.AudioContext || window.webkitAudioContext;
            if (!C) return null;
            audioCtx = new C();
        }
        if (audioCtx.state === 'suspended') audioCtx.resume();
        return audioCtx;
    }

    // notas de Em (E2, B2, E3, G3, B3, E4) em Hz
    const ACORDE = [82.41, 123.47, 164.81, 196.00, 246.94, 329.63];

    function tocarCorda(freq, atrasoSeg) {
        const ctx = garantirCtx();
        if (!ctx) return;
        const t0 = ctx.currentTime + atrasoSeg;

        // Karplus-Strong simplificado com osc + filtro + envelope
        const osc = ctx.createOscillator();
        osc.type = 'triangle';
        osc.frequency.value = freq;

        const filtro = ctx.createBiquadFilter();
        filtro.type = 'lowpass';
        filtro.frequency.value = 2200;
        filtro.Q.value = 0.7;

        const env = ctx.createGain();
        env.gain.setValueAtTime(0.0001, t0);
        env.gain.exponentialRampToValueAtTime(0.35, t0 + 0.01);
        env.gain.exponentialRampToValueAtTime(0.0001, t0 + 1.8);

        osc.connect(filtro).connect(env).connect(ctx.destination);
        osc.start(t0);
        osc.stop(t0 + 1.9);
    }

    function tocarAcorde() {
        if (!somLigado) return;
        ACORDE.forEach((f, i) => tocarCorda(f, i * 0.06));
    }

    if (somBtn) {
        somBtn.addEventListener('click', () => {
            somLigado = !somLigado;
            somBtn.setAttribute('aria-pressed', String(somLigado));
            if (somLigado) garantirCtx();
        });
    }

    if (titulo) {
        titulo.addEventListener('pointerenter', tocarAcorde);
        titulo.addEventListener('click', () => {
            // primeiro clique também liga som
            if (!somLigado && somBtn) { somBtn.click(); }
            tocarAcorde();
        });
    }

    /* ========================================================
       3. Lenis smooth scroll
       ======================================================== */
    let lenis = null;
    if (!semLenis && !reduzir) {
        lenis = new window.Lenis({
            duration: 1.1,
            easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
            smoothWheel: true,
        });
        function raf(time) { lenis.raf(time); requestAnimationFrame(raf); }
        requestAnimationFrame(raf);
    }

    /* ========================================================
       4. Se mobile ou reduced-motion → não montar scroll horizontal
       ======================================================== */
    if (mobile || reduzir || semGsap || semST) {
        // garantir que a cena do violão aparece animada de forma simples
        const cv = document.querySelector('.cena--violao');
        if (cv) {
            cv.style.opacity = '1';
            cv.style.transform = 'none';
        }
        revelarChrome();
        return;
    }

    /* ========================================================
       5. SCROLL HORIZONTAL com GSAP + ScrollTrigger
       ======================================================== */
    const gsap = window.gsap;
    const ScrollTrigger = window.ScrollTrigger;
    gsap.registerPlugin(ScrollTrigger);

    if (lenis) {
        lenis.on('scroll', ScrollTrigger.update);
        gsap.ticker.add((time) => lenis.raf(time * 1000));
        gsap.ticker.lagSmoothing(0);
    }

    const slots = track.children.length;            // 2: hero-slot + violão
    const distancia = (slots - 1) * window.innerWidth;

    // ajusta altura "fake" do wrapper para acomodar o scroll
    cenas.style.height = (slots * 100) + 'vh';

    // 5.1 movimento horizontal da pista
    const pista = gsap.to(track, {
        x: () => -distancia,
        ease: 'none',
        scrollTrigger: {
            trigger: cenas,
            start: 'top top',
            end: () => '+=' + distancia,
            pin: true,
            scrub: 1,
            invalidateOnRefresh: true,
            anticipatePin: 1,
            onUpdate: (self) => {
                // 5.2 hero recua em profundidade conforme avançamos
                const p = self.progress;             // 0 → 1
                const fase = Math.min(p / 0.5, 1);   // primeira metade = transição hero→violão
                hero.style.setProperty('--hero-x',       (-window.innerWidth * 0.35 * fase) + 'px');
                hero.style.setProperty('--hero-scale',   (1 - 0.3 * fase).toFixed(3));
                hero.style.setProperty('--hero-blur',    (8 * fase).toFixed(2) + 'px');
                hero.style.setProperty('--hero-opacity', (1 - 0.7 * fase).toFixed(3));

                // pontos do indicador
                pontos.forEach(p => p.classList.remove('progresso__ponto--ativo'));
                if (fase < 0.5) pontos[0]?.classList.add('progresso__ponto--ativo');
                else            pontos[1]?.classList.add('progresso__ponto--ativo');
            },
        },
    });

    // 5.3 ENTRADA do Violão (diagonal superior-direita → centro)
    gsap.fromTo('.cena--violao',
        { x: '60vw', y: '-30vh', rotate: -8, scale: 0.6, opacity: 0 },
        {
            x: 0, y: 0, rotate: 0, scale: 1, opacity: 1,
            ease: 'power2.out',
            scrollTrigger: {
                trigger: cenas,
                start: 'top top',
                end: () => '+=' + (distancia * 0.55),
                scrub: 1,
                containerAnimation: pista,
            },
        }
    );

    // 5.4 Letras do título — dedilhado
    gsap.to('.violao__titulo .ch', {
        y: 0, rotate: 0, opacity: 1,
        ease: 'back.out(1.4)',
        stagger: 0.045,
        scrollTrigger: {
            trigger: '.cena--violao',
            start: 'left 70%',
            end: 'left 20%',
            scrub: 0.6,
            containerAnimation: pista,
        },
    });

    // 5.5 Cordas a vibrar quando o violão chega
    ScrollTrigger.create({
        trigger: '.cena--violao',
        start: 'left 50%',
        containerAnimation: pista,
        once: true,
        onEnter: () => {
            document.querySelectorAll('.violao__cordas line').forEach((linha, i) => {
                gsap.fromTo(linha,
                    { scaleY: 1 + (0.6 - i * 0.08), transformOrigin: '50% 50%' },
                    {
                        scaleY: 1,
                        duration: 1.2 + i * 0.15,
                        ease: 'elastic.out(1, 0.2)',
                    }
                );
            });
            // toca o acorde se o som estiver ligado
            tocarAcorde();
        },
    });

    // 5.6 Polaroids caem em stagger conforme o scroll passa
    gsap.to('.polaroid', {
        y: 0, opacity: 1,
        ease: 'power3.out',
        stagger: 0.08,
        scrollTrigger: {
            trigger: '.cena--violao',
            start: 'left 60%',
            end: 'left 10%',
            scrub: 0.8,
            containerAnimation: pista,
        },
    });

    // 5.7 Click nos pontos do indicador
    pontos.forEach((p, idx) => {
        if (p.disabled) return;
        p.addEventListener('click', () => {
            const total = cenas.offsetHeight - window.innerHeight;
            const alvo  = cenas.offsetTop + (idx / (slots - 1)) * total;
            if (lenis) lenis.scrollTo(alvo, { duration: 1.4 });
            else window.scrollTo({ top: alvo, behavior: 'smooth' });
        });
    });

    revelarChrome();

    function revelarChrome() {
        // pequena entrada do chrome (indicador + toggle de som)
        gsap?.from?.('.progresso, .som-toggle', {
            opacity: 0, y: 8, duration: 0.6, delay: 0.4, ease: 'power2.out',
        });
    }

    // recalcula em resize
    let rId;
    window.addEventListener('resize', () => {
        clearTimeout(rId);
        rId = setTimeout(() => ScrollTrigger.refresh(), 180);
    });

})();

})();