/**
 * Aluno Dashboard JS
 * Calendário interactivo + animações KPI + contadores
 */

'use strict';

document.addEventListener('DOMContentLoaded', function () {

  /* ════════════════════════════════════════
     DADOS DO CALENDÁRIO — injectados pelo Django
     Lidos do <script type="application/json">
  ════════════════════════════════════════ */

  const dadosEl  = document.getElementById('calendario-dados');
  let EVENTOS  = [];

  if (dadosEl) {
    try {
      EVENTOS = JSON.parse(dadosEl.textContent || '[]');
    } catch (e) {
      console.warn('[dashboard] Erro ao ler dados do calendário:', e);
      EVENTOS = [];
    }
  }

  /* Indexa eventos por data para acesso O(1) */
  let eventosPorData = {};
  EVENTOS.forEach(ev => {
    if (!eventosPorData[ev.data]) {
      eventosPorData[ev.data] = [];
    }
    eventosPorData[ev.data].push(ev);
  });


  /* ════════════════════════════════════════
     CALENDÁRIO
  ════════════════════════════════════════ */

  const hoje         = new Date();
  let mesActual    = hoje.getMonth();
  let anoActual    = hoje.getFullYear();

  const MESES_PT = [
    'Janeiro','Fevereiro','Março','Abril',
    'Maio','Junho','Julho','Agosto',
    'Setembro','Outubro','Novembro','Dezembro'
  ];

  const gridDias   = document.getElementById('calendario-dias');
  const labelMes   = document.getElementById('calendario-mes-label');
  const btnPrev    = document.getElementById('cal-prev');
  const btnNext    = document.getElementById('cal-next');

  /* Tooltip reutilizável */
  const tooltip = document.createElement('div');
  tooltip.className  = 'calendario-tooltip';
  tooltip.setAttribute('role', 'tooltip');
  tooltip.setAttribute('aria-live', 'polite');
  document.body.appendChild(tooltip);

  function padZero(n) {
    return n < 10 ? '0' + n : '' + n;
  }

  function dataStr(ano, mes, dia) {
    /* Formato YYYY-MM-DD para comparar com dados Django */
    return ano + '-' + padZero(mes + 1) + '-' + padZero(dia);
  }

  function renderizarCalendario(ano, mes) {
    if (!gridDias || !labelMes) return;

    labelMes.textContent = MESES_PT[mes] + ' ' + ano;

    /* Primeiro dia do mês (0=Dom … 6=Sáb) → converte para Seg=0 */
    const primeiroDia = new Date(ano, mes, 1).getDay();
    const offsetSeg   = (primeiroDia === 0) ? 6 : primeiroDia - 1;

    const diasNoMes   = new Date(ano, mes + 1, 0).getDate();

    gridDias.innerHTML = '';

    /* Células vazias antes do dia 1 */
    for (let i = 0; i < offsetSeg; i++) {
      const vazio = document.createElement('div');
      vazio.className = 'cal-dia cal-dia--vazio';
      vazio.setAttribute('aria-hidden', 'true');
      gridDias.appendChild(vazio);
    }

    /* Dias do mês */
    for (let d = 1; d <= diasNoMes; d++) {
      const chave    = dataStr(ano, mes, d);
      const eventos  = eventosPorData[chave] || [];
      const eHoje    = (
        d === hoje.getDate() &&
        mes === hoje.getMonth() &&
        ano === hoje.getFullYear()
      );
      const ehFuturo = new Date(ano, mes, d) > hoje;

      const celula = document.createElement('div');
      celula.className = 'cal-dia';
      celula.setAttribute('role', 'gridcell');

      /* Classes de estado */
      if (eHoje)          celula.classList.add('cal-dia--hoje');
      if (eventos.length) {
        const temPresenca = eventos.some(e => e.presenca === true);
        const temFalta = eventos.some(e => e.presenca === false);
        const temAgendada = eventos.some(e => e.presenca === null);

        if (ehFuturo || temAgendada) {
          celula.classList.add('cal-dia--agendada');
        } else if (temPresenca && !temFalta) {
          celula.classList.add('cal-dia--presente');
        } else if (temFalta && !temPresenca) {
          celula.classList.add('cal-dia--falta');
        } else if (temPresenca && temFalta) {
          celula.classList.add('cal-dia--misto');
        }
      }

      /* Número do dia */
      const numSpan = document.createElement('span');
      numSpan.className   = 'cal-dia__num';
      numSpan.textContent = d;
      celula.appendChild(numSpan);

      /* Ponto indicador se tiver evento */
      if (eventos.length) {
        const ponto = document.createElement('span');
        ponto.className = 'cal-dia__ponto';
        ponto.setAttribute('aria-hidden', 'true');
        celula.appendChild(ponto);
      }

      /* Acessibilidade */
      let descricao = d + ' de ' + MESES_PT[mes];
      if (eventos.length) {
        descricao += ' — ' + eventos.length + ' aula(s)';
      }
      celula.setAttribute('aria-label', descricao);

      /* Tooltip ao hover */
      if (eventos.length) {
        celula.addEventListener('mouseenter', function () {
            const evs = eventosPorData[this.dataset.chave] || [];

            tooltip.textContent = '';

            evs.forEach(function (e) {
                const estado = e.presenca === true
                    ? '✓ Presente'
                    : e.presenca === false
                    ? '✗ Falta'
                    : '→ Agendada';

                const linha = document.createElement('div');
                linha.className = 'tooltip-linha';

                const estadoEl = document.createElement('span');
                estadoEl.className = 'tooltip-estado';
                estadoEl.textContent = estado;

                const cursoEl = document.createElement('span');
                cursoEl.className = 'tooltip-curso';
                cursoEl.textContent = e.curso || '';

                const horaEl = document.createElement('span');
                horaEl.className = 'tooltip-hora';
                horaEl.textContent = e.hora_inicio + (e.hora_fim ? ' – ' + e.hora_fim : '');

                linha.appendChild(estadoEl);
                linha.appendChild(cursoEl);
                linha.appendChild(horaEl);
                tooltip.appendChild(linha);
            });

            tooltip.style.display = 'block';

            const rect = this.getBoundingClientRect();
            tooltip.style.left = rect.left + 'px';
            tooltip.style.top = (rect.top - tooltip.offsetHeight - 8) + 'px';
        }.bind(celula));

        celula.addEventListener('mouseleave', function () {
            tooltip.style.display = 'none';
        });

        celula.dataset.chave = chave;
      }

      gridDias.appendChild(celula);
    }
  }

  /* Navegação entre meses */
  btnPrev?.addEventListener('click', () => {
    mesActual--;
    if (mesActual < 0) { mesActual = 11; anoActual--; }
    renderizarCalendario(anoActual, mesActual);
  });

  btnNext?.addEventListener('click', () => {
    mesActual++;
    if (mesActual > 11) { mesActual = 0; anoActual++; }
    renderizarCalendario(anoActual, mesActual);
  });

  /* Renderiza o mês actual */
  renderizarCalendario(anoActual, mesActual);


  /* ════════════════════════════════════════
     ANIMAÇÃO DOS CONTADORES KPI
     Conta de 0 até ao valor real
  ════════════════════════════════════════ */

  function animarContador(el, valorFinal, duracao) {
    if (!el) return;
    const inicio    = 0;
    let startTime = null;
    const unidade   = el.querySelector('.kpi-card__unidade');

    function step(timestamp) {
      if (!startTime) startTime = timestamp;
      const progresso = Math.min((timestamp - startTime) / duracao, 1);
      /* Easing out cubic */
      const ease      = 1 - Math.pow(1 - progresso, 3);
      const valorAtual = Math.round(inicio + (valorFinal - inicio) * ease);

      /* Preserva a unidade (%) se existir */
      if (unidade) {
        el.childNodes[0].textContent = valorAtual;
      } else {
        el.textContent = valorAtual;
      }

      if (progresso < 1) requestAnimationFrame(step);
    }

    requestAnimationFrame(step);
  }

  /* Activa contadores quando entram no viewport */
  const observadorKPI = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (!entry.isIntersecting) return;

      const el         = entry.target;
      const valorFinal = parseInt(el.textContent, 10);
      if (!isNaN(valorFinal)) {
        animarContador(el, valorFinal, 1200);
      }
      observadorKPI.unobserve(el);
    });
  }, { threshold: 0.5 });

  document.querySelectorAll('.kpi-card__valor').forEach(function (el) {
        const texto = el.childNodes[0]?.textContent.trim() || el.textContent.trim();

        if (/^\d+$/.test(texto)) {
            observadorKPI.observe(el);
        }
  });


  /* ════════════════════════════════════════
     ANEL CIRCULAR — KPI taxa de presença
  ════════════════════════════════════════ */

  const anelProg = document.querySelector('.kpi-anel-prog');

  if (anelProg) {
    const percentagem = parseInt(anelProg.dataset.percentagem, 10) || 0;
    const circunf     = 2 * Math.PI * 15.9;   /* r=15.9 do SVG */
    const offset      = circunf - (percentagem / 100) * circunf;

    anelProg.style.strokeDasharray  = circunf.toFixed(2);
    anelProg.style.strokeDashoffset = circunf.toFixed(2);  /* começa vazio */

    /* Anima após um pequeno delay */
    setTimeout(function () {
      anelProg.style.transition     = 'stroke-dashoffset 1.4s cubic-bezier(0.4, 0, 0.2, 1)';
      anelProg.style.strokeDashoffset = offset.toFixed(2);
    }, 300);
  }


  /* ════════════════════════════════════════
     BARRAS DE KPI — animação de entrada
  ════════════════════════════════════════ */

  document.querySelectorAll('.kpi-card__barra').forEach(function (barra) {
    const valor = parseInt(barra.dataset.valor, 10) || 0;
    const larguraFinal = Math.max(0, Math.min(valor, 100)) + '%';

    barra.style.width = '0%';

    setTimeout(function () {
        barra.style.transition = 'width 1.2s cubic-bezier(0.4, 0, 0.2, 1)';
        barra.style.width = larguraFinal;
    }, 200);
  });


  /* ════════════════════════════════════════
     ANIMAÇÃO DE ENTRADA DOS CARDS
     Fade + translateY ao carregar
  ════════════════════════════════════════ */

  const observadorCards = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add('card-visivel');
        observadorCards.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll(
    '.kpi-card, .matricula-card, .aulas-tabela__linha, .proxima-aula-card'
  ).forEach(function (el) {
    observadorCards.observe(el);
  });


  /* ════════════════════════════════════════
     FECHAR TOOLTIP AO SCROLL
  ════════════════════════════════════════ */

  window.addEventListener('scroll', function () {
    tooltip.style.display = 'none';
  }, { passive: true });

});