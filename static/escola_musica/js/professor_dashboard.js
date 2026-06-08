/**
 * Professor Dashboard JS
 * Gráficos Chart.js + acordeão de turmas + animações KPI
 * Regras: const/let apenas, sem innerHTML com dados da BD,
 *         sem var, sem style inline com variáveis Django
 */

'use strict';

document.addEventListener('DOMContentLoaded', () => {

  /* ════════════════════════════════════════
     LEITURA SEGURA DOS DADOS JSON
     json_script garante escape seguro no Django
  ════════════════════════════════════════ */

  const lerDadosJSON = (id) => {
    const el = document.getElementById(id);
    if (!el) return [];
    try {
      return JSON.parse(el.textContent || '[]');
    } catch {
      console.warn(`[prof-dashboard] Erro ao ler JSON de #${id}`);
      return [];
    }
  };

  const dadosBarras = lerDadosJSON('dados-grafico-barras');
  const dadosLinha  = lerDadosJSON('dados-grafico-linha');


  /* ════════════════════════════════════════
     PALETA DE CORES — consistente com o tema
  ════════════════════════════════════════ */

  const COR_PRIMARIA  = 'rgba(201, 168, 76,  1)';
  const COR_PRIM_BG   = 'rgba(201, 168, 76,  0.15)';
  const COR_ACENTO    = 'rgba(123, 79,  166, 1)';
  const COR_ACENTO_BG = 'rgba(123, 79,  166, 0.15)';
  const COR_GRID      = 'rgba(255, 255, 255, 0.06)';
  const COR_TEXTO     = 'rgba(255, 255, 255, 0.5)';

  const defaultsChart = {
    font: {
      family: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      size:   11,
    },
    color: COR_TEXTO,
  };

  if (typeof Chart !== 'undefined') {
    Chart.defaults.font.family = defaultsChart.font.family;
    Chart.defaults.font.size   = defaultsChart.font.size;
    Chart.defaults.color       = defaultsChart.color;
  }


  /* ════════════════════════════════════════
     GRÁFICO DE BARRAS — alunos por turma
  ════════════════════════════════════════ */

  const canvasBarras = document.getElementById('grafico-barras');

  if (canvasBarras && typeof Chart !== 'undefined' && dadosBarras.length > 0) {

    const labels = dadosBarras.map(d => d.turma);
    const totais  = dadosBarras.map(d => d.total);

    new Chart(canvasBarras, {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label:           'Alunos',
          data:            totais,
          backgroundColor: COR_PRIM_BG,
          borderColor:     COR_PRIMARIA,
          borderWidth:     1.5,
          borderRadius:    6,
          borderSkipped:   false,
        }],
      },
      options: {
        responsive:          true,
        maintainAspectRatio: true,
        animation: {
          duration: 900,
          easing:   'easeOutQuart',
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: 'rgba(10, 10, 15, 0.92)',
            borderColor:     COR_PRIMARIA,
            borderWidth:     1,
            padding:         10,
            callbacks: {
              label: (ctx) => ` ${ctx.parsed.y} aluno${ctx.parsed.y !== 1 ? 's' : ''}`,
            },
          },
        },
        scales: {
          x: {
            grid:   { color: COR_GRID },
            ticks:  { color: COR_TEXTO },
            border: { color: COR_GRID },
          },
          y: {
            beginAtZero: true,
            grid:        { color: COR_GRID },
            ticks: {
              color:     COR_TEXTO,
              precision: 0,
            },
            border: { color: COR_GRID },
          },
        },
      },
    });
  }


  /* ════════════════════════════════════════
     GRÁFICO DE LINHA — aulas por mês
  ════════════════════════════════════════ */

  const canvasLinha = document.getElementById('grafico-linha');

  if (canvasLinha && typeof Chart !== 'undefined' && dadosLinha.length > 0) {

    const labels = dadosLinha.map(d => d.mes);
    const totais  = dadosLinha.map(d => d.total);

    new Chart(canvasLinha, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label:           'Aulas dadas',
          data:            totais,
          borderColor:     COR_ACENTO,
          backgroundColor: COR_ACENTO_BG,
          borderWidth:     2,
          pointBackgroundColor: COR_ACENTO,
          pointBorderColor:     'rgba(10, 10, 15, 0.8)',
          pointBorderWidth:     2,
          pointRadius:          5,
          pointHoverRadius:     7,
          fill:            true,
          tension:         0.4,
        }],
      },
      options: {
        responsive:          true,
        maintainAspectRatio: true,
        animation: {
          duration: 1100,
          easing:   'easeOutQuart',
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: 'rgba(10, 10, 15, 0.92)',
            borderColor:     COR_ACENTO,
            borderWidth:     1,
            padding:         10,
            callbacks: {
              label: (ctx) => ` ${ctx.parsed.y} aula${ctx.parsed.y !== 1 ? 's' : ''}`,
            },
          },
        },
        scales: {
          x: {
            grid:   { color: COR_GRID },
            ticks:  { color: COR_TEXTO },
            border: { color: COR_GRID },
          },
          y: {
            beginAtZero: true,
            grid:        { color: COR_GRID },
            ticks: {
              color:     COR_TEXTO,
              precision: 0,
            },
            border: { color: COR_GRID },
          },
        },
      },
    });
  }


  /* ════════════════════════════════════════
     ACORDEÃO DE TURMAS
     Abre/fecha lista de alunos por turma
  ════════════════════════════════════════ */

  const botoesAcordeao = document.querySelectorAll('.turma-bloco__header');

  botoesAcordeao.forEach(btn => {
    btn.addEventListener('click', () => {
      const idAlvos  = btn.getAttribute('aria-controls');
      const painel   = document.getElementById(idAlvos);
      if (!painel) return;

      const estaAberto = btn.getAttribute('aria-expanded') === 'true';

      /* Fecha todos os outros painéis */
      botoesAcordeao.forEach(outroBt => {
        if (outroBt === btn) return;
        const outroId     = outroBt.getAttribute('aria-controls');
        const outroPainel = document.getElementById(outroId);
        if (!outroPainel) return;
        outroBt.setAttribute('aria-expanded', 'false');
        outroPainel.setAttribute('aria-hidden', 'true');
        outroPainel.style.maxHeight = '0px';
        outroBt.querySelector('.turma-bloco__seta')
          ?.classList.remove('seta--aberta');
      });

      /* Abre/fecha o actual */
      if (estaAberto) {
        btn.setAttribute('aria-expanded', 'false');
        painel.setAttribute('aria-hidden', 'true');
        painel.style.maxHeight = '0px';
        btn.querySelector('.turma-bloco__seta')
          ?.classList.remove('seta--aberta');
      } else {
        btn.setAttribute('aria-expanded', 'true');
        painel.setAttribute('aria-hidden', 'false');
        painel.style.maxHeight = painel.scrollHeight + 'px';
        btn.querySelector('.turma-bloco__seta')
          ?.classList.add('seta--aberta');
      }
    });
  });


  /* ════════════════════════════════════════
     ANIMAÇÃO DOS CONTADORES KPI
     Só anima valores inteiramente numéricos
     (evita animar datas como "07/06")
  ════════════════════════════════════════ */

  const animarContador = (el, valorFinal, duracao) => {
    const unidade    = el.querySelector('.kpi-card__unidade');
    const textoNodo = unidade && el.firstChild
        ? el.firstChild
        : el;

    let startTime = null;

    const step = (timestamp) => {
      if (!startTime) startTime = timestamp;
      const progresso  = Math.min((timestamp - startTime) / duracao, 1);
      const ease       = 1 - Math.pow(1 - progresso, 3);
      const valorAtual = Math.round(valorFinal * ease);

      if (unidade) {
        textoNodo.textContent = valorAtual;
      } else {
        el.textContent = valorAtual;
      }

      if (progresso < 1) requestAnimationFrame(step);
    };

    requestAnimationFrame(step);
  };

  const observadorKPI = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;

      const el   = entry.target;
      /* Extrai só dígitos para verificar se é puramente numérico */
      const texto = el.childNodes[0]?.textContent?.trim()
                 ?? el.textContent.trim();
      /* Só anima se o conteúdo for exclusivamente numérico */
      if (/^\d+$/.test(texto)) {
        animarContador(el, parseInt(texto, 10), 1000);
      }

      observadorKPI.unobserve(el);
    });
  }, { threshold: 0.5 });

  document.querySelectorAll('.kpi-card__valor').forEach(el => {
    observadorKPI.observe(el);
  });


  /* ════════════════════════════════════════
     ANEL CIRCULAR — taxa de assiduidade
  ════════════════════════════════════════ */

  const anelProg = document.querySelector('.kpi-anel-prog');

  if (anelProg) {
    const percentagemBruta = parseInt(
        anelProg.dataset.percentagem || '0', 10
    );
    const percentagem = Math.min(
        Math.max(percentagemBruta || 0, 0),
        100
    );

    const circunf = 2 * Math.PI * 15.9;
    const offset  = circunf - (percentagem / 100) * circunf;

    anelProg.style.strokeDasharray  = circunf.toFixed(2);
    anelProg.style.strokeDashoffset = circunf.toFixed(2);

    setTimeout(() => {
      anelProg.style.transition       =
        'stroke-dashoffset 1.4s cubic-bezier(0.4, 0, 0.2, 1)';
      anelProg.style.strokeDashoffset = offset.toFixed(2);
    }, 400);
  }


  /* ════════════════════════════════════════
     BARRAS DE ASSIDUIDADE POR TURMA
     Largura via JS a partir de data-valor
     Sem style inline com variáveis Django
  ════════════════════════════════════════ */

  document.querySelectorAll(
    '.kpi-card__barra, .assid-item__barra'
  ).forEach(barra => {
    const valor       = parseInt(barra.dataset.valor || '0', 10);
    /* Limita entre 0 e 100 */
    const valorSeguro = Math.min(Math.max(valor, 0), 100);

    /* Guarda largura final e começa em 0 */
    barra.style.width = '0%';

    setTimeout(() => {
      barra.style.transition = 'width 1.2s cubic-bezier(0.4, 0, 0.2, 1)';
      barra.style.width      = `${valorSeguro}%`;
    }, 250);
  });


  /* ════════════════════════════════════════
     ANIMAÇÃO DE ENTRADA DOS CARDS
     IntersectionObserver — fade + translateY
  ════════════════════════════════════════ */

  const elementosAnimados = document.querySelectorAll(
    '.kpi-card, .agenda-item, .turma-bloco, .sumario-item, .assid-item'
  );

  if ('IntersectionObserver' in window) {
    const observadorCards = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('card-visivel');
        observadorCards.unobserve(entry.target);
        });
    }, { threshold: 0.08 });

    elementosAnimados.forEach(el => observadorCards.observe(el));
  } else {
    elementosAnimados.forEach(el => el.classList.add('card-visivel'));
  }

});