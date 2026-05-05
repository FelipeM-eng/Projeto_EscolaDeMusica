/* ═══════════════════════════════════════════════
   ESCOLA DE MÚSICA — Comportamento JS
   Separado do HTML conforme regras do projeto
═══════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', function () {

  /* ── Feedback visual no formulário de login ── */
  const formLogin = document.getElementById('form-login');
  if (formLogin) {
    const btnEntrar = formLogin.querySelector('.btn-entrar');

    formLogin.addEventListener('submit', function () {
      btnEntrar.textContent = 'A entrar...';
      btnEntrar.disabled = true;
    });
  }

  /* ── Confirmação antes de logout ── */
  const formLogout = document.getElementById('form-logout');
  if (formLogout) {
    formLogout.addEventListener('submit', function (e) {
      const confirmar = confirm('Tens a certeza que queres terminar a sessão?');
      if (!confirmar) e.preventDefault();
    });
  }

});