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

});