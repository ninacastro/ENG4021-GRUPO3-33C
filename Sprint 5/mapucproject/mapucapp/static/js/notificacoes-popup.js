(() => {
  const container = document.getElementById('notificacoes-popup');
  if (!container) return;

  const stylesheet = document.createElement('link');
  stylesheet.rel = 'stylesheet';
  stylesheet.href = container.dataset.cssUrl;
  document.head.append(stylesheet);

  const storageKey = `mapuc-notificacoes-cursor-${container.dataset.alunoId}`;
  const pageCursor = Number(container.dataset.cursor) || 0;
  let cursor = pageCursor;
  try {
    const savedCursor = Number(sessionStorage.getItem(storageKey));
    if (Number.isSafeInteger(savedCursor) && savedCursor >= 0) {
      cursor = savedCursor;
    }
  } catch (error) {
    console.warn('Não foi possível recuperar o cursor das notificações.', error);
  }

  const fila = [];
  let exibindo = false;

  function exibirProxima() {
    if (exibindo || fila.length === 0) return;
    exibindo = true;

    const notificacao = fila.shift();
    const cartao = document.createElement('article');
    cartao.className = 'notificacao-popup-card';
    cartao.setAttribute('role', 'status');

    const fechar = document.createElement('button');
    fechar.className = 'notificacao-popup-fechar';
    fechar.type = 'button';
    fechar.setAttribute('aria-label', 'Fechar notificação');
    fechar.textContent = '×';

    const titulo = document.createElement('h2');
    titulo.textContent = notificacao.titulo;

    const mensagem = document.createElement('p');
    mensagem.textContent = notificacao.mensagem;

    const link = document.createElement('a');
    link.href = container.dataset.avisosUrl;
    link.textContent = 'Ver todos os avisos';

    cartao.append(fechar, titulo, mensagem, link);
    container.append(cartao);

    let temporizador;
    const remover = () => {
      window.clearTimeout(temporizador);
      cartao.remove();
      exibindo = false;
      exibirProxima();
    };
    fechar.addEventListener('click', remover, { once: true });
    temporizador = window.setTimeout(remover, 8000);
  }

  function consultarNotificacoes() {
    const url = new URL(container.dataset.endpoint, window.location.href);
    url.searchParams.set('since', String(cursor));

    fetch(url, {
      headers: { Accept: 'application/json' },
      credentials: 'same-origin',
    })
      .then(resposta => resposta.json().then(dados => ({ resposta, dados })))
      .then(({ resposta, dados }) => {
        if (Array.isArray(dados.notificacoes)) {
          fila.push(...dados.notificacoes);
          exibirProxima();
        }
        if (Number.isSafeInteger(dados.cursor) && dados.cursor >= cursor) {
          cursor = dados.cursor;
          try {
            sessionStorage.setItem(storageKey, String(cursor));
          } catch (error) {
            console.warn(
              'Não foi possível salvar o cursor das notificações.',
              error
            );
          }
        }
        if (!resposta.ok) {
          console.error('Falha ao atualizar notificações:', dados.erro);
        }
      })
      .catch(error => {
        console.error('Não foi possível consultar novas notificações.', error);
      })
      .then(() => window.setTimeout(consultarNotificacoes, 10000));
  }

  consultarNotificacoes();
})();
