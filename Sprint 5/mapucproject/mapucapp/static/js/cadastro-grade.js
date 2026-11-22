(function () {
  const container = document.getElementById('encontros-container');
  const adicionarBotao = document.getElementById('adicionar-encontro');
  const template = document.getElementById('encontro-template');
  const totalForms = document.getElementById('id_encontros-TOTAL_FORMS');

  if (!container || !adicionarBotao || !template || !totalForms) {
    return;
  }

  function atualizarEncontros() {
    const encontros = Array.from(container.children).filter(function (elemento) {
      return elemento.classList.contains('encontro-form');
    });

    encontros.forEach(function (encontro, indice) {
      encontro.querySelector('[data-encontro-titulo]').textContent =
        `Encontro ${indice + 1}`;
      encontro.querySelector('.remover-encontro').hidden = encontros.length === 1;
      encontro.querySelectorAll('[name], [id], [for]').forEach(function (campo) {
        ['name', 'id', 'for'].forEach(function (atributo) {
          const valor = campo.getAttribute(atributo);
          if (valor) {
            campo.setAttribute(
              atributo,
              valor.replace(
                /encontros-(?:\d+|__prefix__)-/g,
                `encontros-${indice}-`
              )
            );
          }
        });
      });
    });

    totalForms.value = encontros.length;
  }

  adicionarBotao.addEventListener('click', function () {
    const encontroAnterior = container.querySelector('.encontro-form:last-child');
    const campos = ['dia_semana', 'horario', 'codigo_sala'];
    const valoresAnteriores = {};

    campos.forEach(function (campo) {
      const elemento = encontroAnterior.querySelector(`[name$="-${campo}"]`);
      valoresAnteriores[campo] = elemento.value;
    });

    const encontroNovo = template.content.cloneNode(true);
    container.appendChild(encontroNovo);
    atualizarEncontros();

    const novoEncontro = container.querySelector('.encontro-form:last-child');
    campos.forEach(function (campo) {
      const elemento = novoEncontro.querySelector(`[name$="-${campo}"]`);
      elemento.value = valoresAnteriores[campo];
    });
  });

  container.addEventListener('click', function (event) {
    const botaoRemover = event.target.closest('.remover-encontro');
    if (!botaoRemover || container.children.length === 1) {
      return;
    }

    botaoRemover.closest('.encontro-form').remove();
    atualizarEncontros();
  });

  atualizarEncontros();
})();
