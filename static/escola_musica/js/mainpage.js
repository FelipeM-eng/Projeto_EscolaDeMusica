/**
 * Mainpage JS — Física de inércia estilo Danilo Sierra
 * Velocidade do rato → impulso → desaceleração suave
 */

document.addEventListener('DOMContentLoaded', () => {

  const brandingBtn       = document.getElementById('brandingBtn');
  const loginModal        = document.getElementById('loginModal');
  const gridItems         = document.querySelectorAll('.grid-item');
  const brandingContainer = document.querySelector('.branding-container');

  /* ════════════════════════════════════════
     FÍSICA — inércia com velocidade
  ════════════════════════════════════════ */

  /* Posição alvo (onde o rato está) */
  let targetX  = 0;
  let targetY  = 0;

  /* Posição actual suavizada pelo lerp */
  let currentX = 0;
  let currentY = 0;

  /* Velocidade instantânea do rato */
  let velX     = 0;
  let velY     = 0;
  let prevMouseX = window.innerWidth  / 2;
  let prevMouseY = window.innerHeight / 2;

  /* Fricção — mais baixo = mais inércia / mais fluido */
  const FRICTION    = 0.055;
  /* Intensidade do deslocamento máximo em px */
  const INTENSIDADE = 0.038;

  /* Profundidades por item — criam ilusão de camadas */
  const PROFUNDIDADES = [1.0, 1.6, 0.7, 1.3, 0.5, 1.8,
                         0.9, 1.4, 0.6, 1.1, 1.7, 0.8,
                         1.2, 1.5, 0.4];

  gridItems.forEach((item, i) => {
    item.dataset.depth = PROFUNDIDADES[i % PROFUNDIDADES.length];
  });

  /* Rastreia velocidade do rato */
  document.addEventListener('mousemove', e => {
    velX = e.clientX - prevMouseX;
    velY = e.clientY - prevMouseY;
    prevMouseX = e.clientX;
    prevMouseY = e.clientY;

    /* Alvo baseado na posição relativa ao centro */
    targetX = (window.innerWidth  / 2 - e.clientX) * INTENSIDADE;
    targetY = (window.innerHeight / 2 - e.clientY) * INTENSIDADE;
  }, { passive: true });

  /* Ao sair da janela — regressa ao centro */
  document.addEventListener('mouseleave', () => {
    targetX = 0;
    targetY = 0;
    velX    = 0;
    velY    = 0;
  });

  /* Pausa quando tab oculta */
  let running = true;
  document.addEventListener('visibilitychange', () => {
    running = !document.hidden;
    if (running) animate();
  });

  /* Loop de animação */
  function animate() {
    if (!running) return;

    /* LERP — interpolação suave com fricção */
    currentX += (targetX - currentX) * FRICTION;
    currentY += (targetY - currentY) * FRICTION;

    gridItems.forEach(item => {
      const depth = parseFloat(item.dataset.depth) || 1;
      const x = (currentX * depth).toFixed(3);
      const y = (currentY * depth).toFixed(3);
      item.style.transform = `translate(${x}px, ${y}px)`;
    });

    requestAnimationFrame(animate);
  }

  animate();


  /* ════════════════════════════════════════
     MODAL DE LOGIN
  ════════════════════════════════════════ */

  brandingBtn.addEventListener('click', e => {
    e.stopPropagation();
    const aberto = loginModal.classList.toggle('active');
    brandingBtn.querySelector('.btn-text').textContent = aberto
      ? 'Fechar'
      : 'Escola de Música';
  });

  document.addEventListener('click', e => {
    if (
      loginModal.classList.contains('active') &&
      !loginModal.contains(e.target)          &&
      !brandingBtn.contains(e.target)
    ) {
      loginModal.classList.remove('active');
      brandingBtn.querySelector('.btn-text').textContent = 'Escola de Música';
    }
  });


  /* ════════════════════════════════════════
     CLIQUE NOS CARDS
  ════════════════════════════════════════ */

  gridItems.forEach(item => {
    item.addEventListener('click', () => {
      const url = item.getAttribute('data-url');
      if (url) window.location.href = url;
    });
  });


  /* ════════════════════════════════════════
     SCROLL — branding compacto
  ════════════════════════════════════════ */

  window.addEventListener('scroll', () => {
    const s = window.pageYOffset > 80;
    Object.assign(brandingContainer.style, s ? {
      background:           'rgba(0,0,0,0.35)',
      padding:              '6px 10px',
      borderRadius:         '50px',
      backdropFilter:       'blur(14px) saturate(160%)',
      webkitBackdropFilter: 'blur(14px) saturate(160%)',
    } : {
      background:           'transparent',
      padding:              '',
      backdropFilter:       '',
      webkitBackdropFilter: '',
    });
  }, { passive: true });

});