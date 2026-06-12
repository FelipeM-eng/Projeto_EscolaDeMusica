/* Portfólio — animações de scroll com GSAP/ScrollTrigger */
(() => {
  if (!window.gsap || !window.ScrollTrigger) return;
  gsap.registerPlugin(ScrollTrigger);

  /* ---- Split em palavras/letras ---- */
  document.querySelectorAll('.split-words').forEach(el => {
    el.innerHTML = el.textContent.trim().split(/\s+/)
      .map(w => `<span class="word"><span style="display:inline-block">${w}</span></span>`).join(' ');
  });
  document.querySelectorAll('.split-chars').forEach(el => {
    el.innerHTML = [...el.textContent.trim()]
      .map(c => c === ' ' ? ' ' : `<span class="char">${c}</span>`).join('');
  });

  /* ---- Reveal palavras ---- */
  gsap.utils.toArray('.split-words').forEach(el => {
    gsap.to(el.querySelectorAll('.word'), {
      y:0, opacity:1, duration:1, ease:'expo.out', stagger:0.05,
      scrollTrigger:{ trigger:el, start:'top 85%' }
    });
  });

  /* ---- Reveal letras (títulos dos cursos) ---- */
  gsap.utils.toArray('.split-chars').forEach(el => {
    gsap.to(el.querySelectorAll('.char'), {
      y:0, opacity:1, duration:.8, ease:'expo.out', stagger:0.03,
      scrollTrigger:{ trigger:el, start:'top 80%' }
    });
  });

  /* ---- Reveal genérico ---- */
  gsap.utils.toArray('.reveal-up, .reveal-line').forEach(el => {
    ScrollTrigger.create({
      trigger:el, start:'top 85%',
      onEnter:()=>el.classList.add('is-in')
    });
  });

  /* ---- Timeline bullets staggered ---- */
  gsap.utils.toArray('.curso__timeline').forEach(list => {
    const items = list.querySelectorAll('li');
    ScrollTrigger.create({
      trigger:list, start:'top 80%',
      onEnter:()=>items.forEach((li,i)=>setTimeout(()=>li.classList.add('is-in'), i*120))
    });
  });

  /* ---- Parallax na mídia ---- */
  gsap.utils.toArray('.curso__media--parallax').forEach(fig => {
    const inner = fig.querySelector('img, .curso__media-placeholder');
    gsap.fromTo(inner, { yPercent:-10 }, {
      yPercent:10, ease:'none',
      scrollTrigger:{ trigger:fig, start:'top bottom', end:'bottom top', scrub:true }
    });
  });

  /* ---- Índice gigante: parallax + contagem visual ---- */
  gsap.utils.toArray('.curso__index').forEach(el => {
    gsap.fromTo(el, { xPercent:-15, opacity:.3 }, {
      xPercent:0, opacity:1, ease:'expo.out',
      scrollTrigger:{ trigger:el.closest('.curso'), start:'top 70%' }
    });
  });

  /* ---- Nav sticky: link ativo ---- */
  const links = document.querySelectorAll('.portfolio__nav a');
  document.querySelectorAll('.curso').forEach(curso => {
    ScrollTrigger.create({
      trigger:curso, start:'top 50%', end:'bottom 50%',
      onToggle:({isActive})=>{
        if(!isActive) return;
        links.forEach(a => a.classList.toggle('is-active', a.dataset.target === curso.id));
      }
    });
  });

  /* ---- Contadores de stats ---- */
  gsap.utils.toArray('.stat__num').forEach(el => {
    const target = +el.dataset.count;
    const obj = { n:0 };
    ScrollTrigger.create({
      trigger:el, start:'top 85%',
      onEnter:()=>gsap.to(obj,{
        n:target, duration:2, ease:'expo.out',
        onUpdate:()=> el.textContent = Math.round(obj.n)
      })
    });
  });


  /* ---- Smooth scroll para anchors do portfolio ---- */
  document.querySelectorAll('.portfolio__nav a').forEach(a => {
    a.addEventListener('click', e => {
      e.preventDefault();
      document.getElementById(a.dataset.target)?.scrollIntoView({ behavior:'smooth', block:'start' });
    });
  });
})();
