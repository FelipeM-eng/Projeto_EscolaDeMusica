/* ═══════════════════════════════════════════════
   BASE — comportamentos globais
   Carregado em TODAS as páginas via base.html
═══════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', function () {

  /* ── Fechar alertas manualmente ── */
  document.querySelectorAll('.alerta__fechar').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var alerta = btn.closest('.alerta');
      if (!alerta) return;
      alerta.style.transition = 'opacity 0.3s ease';
      alerta.style.opacity    = '0';
      setTimeout(function () {
        if (alerta.parentNode) alerta.parentNode.removeChild(alerta);
      }, 300);
    });
  });

  /* ── Auto-fechar alertas de sucesso após 5s ── */
  document.querySelectorAll('.alerta--success').forEach(function (alerta) {
    setTimeout(function () {
      alerta.style.transition = 'opacity 0.5s ease';
      alerta.style.opacity    = '0';
      setTimeout(function () {
        if (alerta.parentNode) alerta.parentNode.removeChild(alerta);
      }, 500);
    }, 5000);
  });

  /* ── Confirmação antes de logout manual ── */
  var formLogout = document.getElementById('form-logout');
  if (formLogout) {
    formLogout.addEventListener('submit', function (e) {
      if (!confirm('Tens a certeza que queres terminar a sessão?')) {
        e.preventDefault();
      }
    });
  }

  // Seleciona todos os cards que devem funcionar como link
    const cards = document.querySelectorAll('.card-link');

    cards.forEach(card => {
        card.addEventListener('click', function() {
            // Pega a URL que o Django gerou no atributo data-url
            const url = this.getAttribute('data-url');
            
            if (url) {
                window.location.href = url;
            }
        });
    });


  /* ── Redirecionamento Seguro de Cards ── */
  document.addEventListener('click', function(e) {
    // Verifica se o clique foi no card-link ou em algo dentro dele
    const card = e.target.closest('.card-link');
    
    if (card) {
      const url = card.getAttribute('data-url');
      
      // VALIDAÇÃO DE SEGURANÇA:
      // Verifica se a URL começa com "/" (garante que é um link interno do seu Django)
      if (url && url.startsWith('/')) {
        window.location.href = url;
      } else {
        // Caso alguém tente injetar "https://google.com", o JS vai ignorar
        console.warn("Redirecionamento bloqueado: Apenas links internos são permitidos.");
      }
    }
  });

  /* ── Partículas de fundo global ── */
  (function () {

    const canvas = document.getElementById('fundo-po-global');
    if (!canvas) return;

    const reducedMotion = window.matchMedia(
      '(prefers-reduced-motion: reduce)'
    ).matches;
    if (reducedMotion) return;

    const ctx = canvas.getContext('2d');
    let particles = [];
    let w = 0;
    let h = 0;

    function resize() {
      const dpr  = Math.min(window.devicePixelRatio || 1, 2);
      w = window.innerWidth;
      h = window.innerHeight;

      canvas.width  = w * dpr;
      canvas.height = h * dpr;
      canvas.style.width  = w + 'px';
      canvas.style.height = h + 'px';

      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      /* Menos partículas que a mainpage — mais subtil */
      const count = Math.floor((w * h) / 14000);

      particles = Array.from({ length: count }, function () {
        return {
          x:  Math.random() * w,
          y:  Math.random() * h,
          r:  0.3 + Math.random() * 0.9,
          vx: (Math.random() - 0.5) * 0.1,
          vy: -0.05 - Math.random() * 0.12,
          a:  0.1 + Math.random() * 0.3,
        };
      });
    }

    function draw() {
      ctx.clearRect(0, 0, w, h);

      particles.forEach(function (p) {
        p.x += p.vx;
        p.y += p.vy;

        if (p.y < 0)    { p.y = h; p.x = Math.random() * w; }
        if (p.x < 0)    { p.vx *= -1; }
        if (p.x > w)    { p.vx *= -1; }

        /* Zona de visibilidade — mais visível no centro */
        const dx   = p.x / w - 0.5;
        const dy   = p.y / h - 0.4;
        const zona = Math.max(0, 1 - Math.abs(dx) * 2 - Math.abs(dy) * 1.6);
        const alpha = p.a * zona;

        if (alpha < 0.015) return;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(255, 235, 200, ' + alpha + ')';
        ctx.fill();
      });

      requestAnimationFrame(draw);
    }

    resize();
    window.addEventListener('resize', resize, { passive: true });
    draw();

  })();

});