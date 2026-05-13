/* ═══════════════════════════════════════════════
   FORMULÁRIOS — datepicker, ano letivo, submits
   Carregado em matricula_nova.html e matricula_editar.html
═══════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', function () {

  /* ── Feedback visual nos submits ── */
  var submitConfigs = [
    { formId: 'form-matricula-nova',   btnId: 'btn-submeter', texto: 'A validar...'  },
    { formId: 'form-confirmar',        btnId: 'btn-confirmar', texto: 'A registar...' },
    { formId: 'form-matricula-editar', btnId: 'btn-guardar',   texto: 'A guardar...'  },
  ];

  submitConfigs.forEach(function (cfg) {
    var form = document.getElementById(cfg.formId);
    if (!form) return;
    form.addEventListener('submit', function () {
      var btn = document.getElementById(cfg.btnId);
      if (btn) {
        btn.textContent = cfg.texto;
        btn.disabled    = true;
      }
    });
  });

  /* ── Datepicker — validação de min e max ── */
  document.querySelectorAll('input[type="date"]').forEach(function (input) {
    var hoje = new Date().toISOString().split('T')[0];
    if (!input.getAttribute('min')) {
      input.setAttribute('min', hoje);
    }
    input.addEventListener('change', function () {
      var min = input.getAttribute('min');
      var max = input.getAttribute('max');
      if (min && input.value && input.value < min) {
        input.setCustomValidity(
          'A data não pode ser anterior a ' +
          new Date(min + 'T00:00:00').toLocaleDateString('pt-PT') + '.'
        );
        input.reportValidity();
        return;
      }
      if (max && input.value && input.value > max) {
        input.setCustomValidity(
          'A data não pode ser posterior a ' +
          new Date(max + 'T00:00:00').toLocaleDateString('pt-PT') + '.'
        );
        input.reportValidity();
        return;
      }
      input.setCustomValidity('');
    });
  });

/* ──────────────────────────────────────────
   6. ANO LETIVO AUTOMÁTICO — derivado da data de matrícula
   Campo readonly — utilizador não edita directamente.
   Preenchido sempre que a data muda.
────────────────────────────────────────── */
var inputData = document.getElementById('id_data_matricula');
var inputAno  = document.getElementById('id_ano_letivo');

if (inputData && inputAno) {

  function actualizarAnoLetivo() {
    var valor = inputData.value;
    if (!valor) return;
    var ano = new Date(valor + 'T00:00:00').getFullYear();
    if (!isNaN(ano)) {
      inputAno.value = ano;
    }
  }

  // Preenche ao carregar a página se já houver data
  actualizarAnoLetivo();

  // Preenche sempre que a data muda
  inputData.addEventListener('change', actualizarAnoLetivo);
}

/* ──────────────────────────────────────────
   7. FILTRO DE TURMAS POR CURSO
   Lê os dados do JSON embutido no template.
   Filtra as opções do select de turmas
   conforme o curso seleccionado.
────────────────────────────────────────── */
var selectCurso  = document.getElementById('id_id_curso');
var selectTurma  = document.getElementById('id_id_turma');
var dadosTurmasEl = document.getElementById('dados-turmas');

if (selectCurso && selectTurma && dadosTurmasEl) {

  var todasTurmas = JSON.parse(dadosTurmasEl.textContent);

  function filtrarTurmas() {
    var cursoId = parseInt(selectCurso.value, 10);

    // Guarda a turma actualmente seleccionada (para manter se ainda válida)
    var turmaAtual = parseInt(selectTurma.value, 10);

    // Limpa todas as opções excepto a placeholder
    selectTurma.innerHTML = '<option value="">— Seleciona a turma —</option>';

    if (!cursoId) return;

    // Filtra turmas que pertencem ao curso seleccionado
    var turmasFiltradas = todasTurmas.filter(function (t) {
      return t.curso_id === cursoId;
    });

    turmasFiltradas.forEach(function (t) {
      var opt = document.createElement('option');
      opt.value       = t.id;
      opt.textContent = t.nome;
      // Mantém selecção se a turma ainda pertence ao curso
      if (t.id === turmaAtual) {
        opt.selected = true;
      }
      selectTurma.appendChild(opt);
    });
  }

  // Filtra ao mudar o curso
  selectCurso.addEventListener('change', filtrarTurmas);

  // Filtra ao carregar a página
  // (necessário se o form volta com erros e já tem curso seleccionado)
  filtrarTurmas();
}

});