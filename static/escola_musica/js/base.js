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

  // Seleciona todos os cards que devem funcionar como link
    const cards = document.querySelectorAll('.card-link');

    cards.forEach(card => {
        card.addEventListener('click', function() {
            // Pega a URL que o Django gerou no atributo data-url
            const url = this.getAttribute('data-url');
            
            if (url) {
                window.location.href = url;
            }
        });
    });


  /* ── Redirecionamento Seguro de Cards ── */
  document.addEventListener('click', function(e) {
    // Verifica se o clique foi no card-link ou em algo dentro dele
    const card = e.target.closest('.card-link');
    
    if (card) {
      const url = card.getAttribute('data-url');
      
      // VALIDAÇÃO DE SEGURANÇA:
      // Verifica se a URL começa com "/" (garante que é um link interno do seu Django)
      if (url && url.startsWith('/')) {
        window.location.href = url;
      } else {
        // Caso alguém tente injetar "https://google.com", o JS vai ignorar
        console.warn("Redirecionamento bloqueado: Apenas links internos são permitidos.");
      }
    }
  });

});