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

  /* ── Ano letivo automático a partir da data de matrícula ── */
  var inputData = document.getElementById('id_data_matricula');
  var inputAno  = document.getElementById('id_ano_letivo');

  if (inputData && inputAno) {
    inputData.addEventListener('change', function () {
      if (!inputData.value) return;
      var ano = new Date(inputData.value + 'T00:00:00').getFullYear();
      if (!isNaN(ano) && !inputAno.dataset.editadoManualmente) {
        inputAno.value = ano;
      }
    });

    inputAno.addEventListener('input', function () {
      inputAno.dataset.editadoManualmente = '1';
    });

    inputAno.addEventListener('change', function () {
      if (!inputAno.value) delete inputAno.dataset.editadoManualmente;
    });
  }

});