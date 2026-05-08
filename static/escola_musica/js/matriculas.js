/* ═══════════════════════════════════════════════
   ESCOLA DE MÚSICA — JS principal
   Responsabilidades:
     1. Modal de confirmação de matrícula
     2. Fechar alertas
     3. Feedback visual em submits
     4. Confirmação antes de logout manual
     5. Validação de datepicker
   
   Gestão de sessão: delegada inteiramente ao Django.
   Não existe lógica de logout automático neste ficheiro.
═══════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', function () {

  /* ──────────────────────────────────────────
     1. MODAL DE CONFIRMAÇÃO
  ────────────────────────────────────────── */
  var modal = document.getElementById('modal-confirmacao');

  if (modal) {
    // Foco no primeiro botão ao abrir
    var primeiroBotao = modal.querySelector('button, a');
    if (primeiroBotao) primeiroBotao.focus();

    // Fechar com tecla Escape
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') fecharModal();
    });

    // Fechar ao clicar no fundo escuro (fora do card)
    modal.addEventListener('click', function (e) {
      if (e.target === modal) fecharModal();
    });
  }

  function fecharModal() {
    if (!modal) return;
    modal.style.transition = 'opacity 0.3s ease';
    modal.style.opacity = '0';
    setTimeout(function () {
      if (modal.parentNode) modal.parentNode.removeChild(modal);
    }, 300);
  }


  /* ──────────────────────────────────────────
     2. FECHAR ALERTAS MANUALMENTE
  ────────────────────────────────────────── */
  document.querySelectorAll('.alerta__fechar').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var alerta = btn.closest('.alerta');
      if (!alerta) return;
      alerta.style.transition = 'opacity 0.3s ease';
      alerta.style.opacity = '0';
      setTimeout(function () {
        if (alerta.parentNode) alerta.parentNode.removeChild(alerta);
      }, 300);
    });
  });

  // Auto-fechar alertas de sucesso após 5 segundos
  document.querySelectorAll('.alerta--success').forEach(function (alerta) {
    setTimeout(function () {
      alerta.style.transition = 'opacity 0.5s ease';
      alerta.style.opacity = '0';
      setTimeout(function () {
        if (alerta.parentNode) alerta.parentNode.removeChild(alerta);
      }, 500);
    }, 5000);
  });


  /* ──────────────────────────────────────────
     3. FEEDBACK VISUAL NOS SUBMITS
  ────────────────────────────────────────── */
  var submitConfigs = [
    { formId: 'form-matricula-nova',   btnId: 'btn-submeter',  texto: 'A validar...'  },
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
        btn.disabled = true;
      }
    });
  });


  /* ──────────────────────────────────────────
     4. CONFIRMAÇÃO ANTES DE LOGOUT MANUAL
  ────────────────────────────────────────── */
  var formLogout = document.getElementById('form-logout');
  if (formLogout) {
    formLogout.addEventListener('submit', function (e) {
      if (!confirm('Tens a certeza que queres terminar a sessão?')) {
        e.preventDefault();
      }
    });
  }


  /* ──────────────────────────────────────────
     5. DATEPICKER — min = hoje + ano letivo automático
  ────────────────────────────────────────── */
  var hoje = new Date().toISOString().split('T')[0];

  document.querySelectorAll('input[type="date"]').forEach(function (input) {
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
     6. ANO LETIVO AUTOMÁTICO
     Quando o utilizador seleciona a data de matrícula,
     preenche automaticamente o ano letivo com o ano
     da data escolhida — mas permite edição manual.
  ────────────────────────────────────────── */
  var inputData    = document.getElementById('id_data_matricula');
  var inputAno     = document.getElementById('id_ano_letivo');

  if (inputData && inputAno) {
    inputData.addEventListener('change', function () {
      var valor = inputData.value;
      if (!valor) return;

      var ano = new Date(valor + 'T00:00:00').getFullYear();
      if (!isNaN(ano)) {
        // Só preenche automaticamente se o campo estiver vazio
        // ou se o utilizador não o tiver alterado manualmente
        if (!inputAno.dataset.editadoManualmente) {
          inputAno.value = ano;
        }
      }
    });

    // Marca o campo como editado manualmente se o utilizador o alterar
    inputAno.addEventListener('input', function () {
      inputAno.dataset.editadoManualmente = '1';
    });

    // Reset da marca se o utilizador limpar o campo
    inputAno.addEventListener('change', function () {
      if (!inputAno.value) {
        delete inputAno.dataset.editadoManualmente;
      }
    });
  }

});