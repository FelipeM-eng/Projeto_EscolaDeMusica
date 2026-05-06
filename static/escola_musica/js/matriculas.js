/* ═══════════════════════════════════════════════
   ESCOLA DE MÚSICA — Comportamento JS
   Separado do HTML conforme regras do projeto
═══════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', function () {

  /* ──────────────────────────────────────────
     1. FECHAR ALERTAS MANUALMENTE
  ────────────────────────────────────────── */
  document.querySelectorAll('.alerta__fechar').forEach(function (btn) {
    btn.addEventListener('click', function () {
      btn.closest('.alerta').remove();
    });
  });

  /* ──────────────────────────────────────────
     2. AUTO-FECHAR ALERTAS DE SUCESSO (5s)
  ────────────────────────────────────────── */
  document.querySelectorAll('.alerta--success').forEach(function (alerta) {
    setTimeout(function () {
      alerta.style.transition = 'opacity 0.5s ease';
      alerta.style.opacity = '0';
      setTimeout(function () { alerta.remove(); }, 500);
    }, 5000);
  });

  /* ──────────────────────────────────────────
     3. DATEPICKER — garantir data mínima = hoje
     (reforço JS além do atributo min no HTML)
  ────────────────────────────────────────── */
  const hoje = new Date().toISOString().split('T')[0];

  document.querySelectorAll('input[type="date"]').forEach(function (input) {
    // Só aplica min se não tiver já um definido pelo backend
    if (!input.getAttribute('min')) {
      input.setAttribute('min', hoje);
    }
    // Validação ao mudar o valor
    input.addEventListener('change', function () {
      if (input.value < input.getAttribute('min')) {
        input.setCustomValidity(
          'A data não pode ser anterior ao mínimo permitido.'
        );
        input.reportValidity();
      } else {
        input.setCustomValidity('');
      }
    });
  });

  /* ──────────────────────────────────────────
     4. FEEDBACK VISUAL NO SUBMIT
  ────────────────────────────────────────── */
  const formNova = document.getElementById('form-matricula-nova');
  if (formNova) {
    formNova.addEventListener('submit', function () {
      const btn = document.getElementById('btn-submeter');
      if (btn) {
        btn.textContent = 'A registar...';
        btn.disabled = true;
      }
    });
  }

  /* ──────────────────────────────────────────
     5. CONFIRMAÇÃO ANTES DE LOGOUT
  ────────────────────────────────────────── */
  const formLogout = document.getElementById('form-logout');
  if (formLogout) {
    formLogout.addEventListener('submit', function (e) {
      if (!confirm('Tens a certeza que queres terminar a sessão?')) {
        e.preventDefault();
      }
    });
  }

  /* ──────────────────────────────────────────
     6. FEEDBACK NO FORMULÁRIO DE LOGIN
  ────────────────────────────────────────── */
  const formLogin = document.getElementById('form-login');
  if (formLogin) {
    formLogin.addEventListener('submit', function () {
      const btn = formLogin.querySelector('.btn-entrar');
      if (btn) {
        btn.textContent = 'A entrar...';
        btn.disabled = true;
      }
    });
  }

});