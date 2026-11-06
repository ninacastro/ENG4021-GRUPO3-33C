const modalPrivacidade = document.getElementById('modal-privacidade');
const abrirPrivacidade = document.getElementById('abrir-privacidade');
const fecharPrivacidade = document.getElementById('fechar-privacidade');
const modalDeslogar = document.getElementById('modal-deslogar');
const abrirDeslogar = document.getElementById('abrir-deslogar');
const cancelarDeslogar = document.getElementById('cancelar-deslogar');

function fecharModalPrivacidade() {
  modalPrivacidade.hidden = true;
  abrirPrivacidade.focus();
}

abrirPrivacidade.addEventListener('click', function () {
  modalPrivacidade.hidden = false;
  fecharPrivacidade.focus();
});

fecharPrivacidade.addEventListener('click', fecharModalPrivacidade);

modalPrivacidade.addEventListener('click', function (event) {
  if (event.target === modalPrivacidade) {
    fecharModalPrivacidade();
  }
});

function fecharModalDeslogar() {
  modalDeslogar.hidden = true;
  abrirDeslogar.focus();
}

abrirDeslogar.addEventListener('click', function () {
  modalDeslogar.hidden = false;
  cancelarDeslogar.focus();
});

cancelarDeslogar.addEventListener('click', fecharModalDeslogar);

modalDeslogar.addEventListener('click', function (event) {
  if (event.target === modalDeslogar) {
    fecharModalDeslogar();
  }
});

document.addEventListener('keydown', function (event) {
  if (event.key === 'Escape') {
    if (!modalPrivacidade.hidden) {
      fecharModalPrivacidade();
    } else if (!modalDeslogar.hidden) {
      fecharModalDeslogar();
    }
  }
});
