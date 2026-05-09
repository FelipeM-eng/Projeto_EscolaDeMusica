/* ═══════════════════════════════════════════════
   MODAL — abertura e fecho da janela de confirmação
   Carregado apenas em matriculas_lista.html
═══════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', function () {

  var modal = document.getElementById('modal-confirmacao');
  if (!modal) return;

  /* ── Foco no primeiro botão ao abrir ── */
  var primeiroBotao = modal.querySelector('button, a');
  if (primeiroBotao) primeiroBotao.focus();

  /* ── Fechar com tecla Escape ── */
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') fecharModal();
  });

  /* ── Fechar ao clicar no fundo escuro ── */
  modal.addEventListener('click', function (e) {
    if (e.target === modal) fecharModal();
  });

  function fecharModal() {
    modal.style.transition = 'opacity 0.3s ease';
    modal.style.opacity    = '0';
    setTimeout(function () {
      if (modal.parentNode) modal.parentNode.removeChild(modal);
    }, 300);
  }

});