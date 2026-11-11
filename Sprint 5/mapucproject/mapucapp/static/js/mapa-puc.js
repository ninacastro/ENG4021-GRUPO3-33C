
const centroPUC = [-22.9785, -43.2324];

const limitesCampus = [
  [-22.9810, -43.2360],
  [-22.9750, -43.2280],
];

const mapa = L.map('mapa-puc', {
  center: centroPUC,
  zoom: 17,
  minZoom: 16,
  maxBounds: limitesCampus,
  maxBoundsViscosity: 1.0,
});

L.tileLayer(
  'https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}',
  {
    maxZoom: 19,
    attribution: '© Esri',
  }
).addTo(mapa);

const botaoLocalizacao = document.getElementById('botao-localizacao');
const botaoRota = document.getElementById('botao-rota');
const statusLocalizacao = document.getElementById('status-localizacao');
const camadaRota = L.layerGroup().addTo(mapa);
const iconeUsuario = L.divIcon({
  className: '',
  html: '<span class="marcador-usuario"></span>',
  iconSize: [18, 18],
  iconAnchor: [9, 9],
});

let marcadorUsuario = null;
let circuloPrecisao = null;
let posicaoUsuario = null;
let destinoAtual = null;
let observadorLocalizacao = null;

function definirStatus(mensagem, erro = false) {
  statusLocalizacao.textContent = mensagem;
  statusLocalizacao.classList.toggle('status-localizacao--erro', erro);
}

function estaDentroDosLimites(latitude, longitude) {
  return latitude >= limitesCampus[0][0]
    && latitude <= limitesCampus[1][0]
    && longitude >= limitesCampus[0][1]
    && longitude <= limitesCampus[1][1];
}

function atualizarLocalizacao(resultado) {
  const primeiraLocalizacao = posicaoUsuario === null;
  posicaoUsuario = {
    latitude: resultado.coords.latitude,
    longitude: resultado.coords.longitude,
  };
  const { latitude, longitude } = posicaoUsuario;
  const foraDosLimites = !estaDentroDosLimites(latitude, longitude);

  if (marcadorUsuario) {
    mapa.removeLayer(marcadorUsuario);
    mapa.removeLayer(circuloPrecisao);
  }

  circuloPrecisao = L.circle([latitude, longitude], {
    radius: resultado.coords.accuracy,
    color: '#1677ff',
    fillColor: '#1677ff',
    fillOpacity: 0.12,
    weight: 1,
  }).addTo(mapa);
  marcadorUsuario = L.marker([latitude, longitude], { icon: iconeUsuario })
    .addTo(mapa)
    .bindPopup('Você está aqui.');

  if (foraDosLimites) {
    mapa.setMaxBounds(null);
    mapa.setMinZoom(16);
    if (primeiraLocalizacao) {
      mapa.setView([latitude, longitude], 17);
    }
    definirStatus(
      'Você está fora dos limites definidos para o mapa do campus. A posição foi marcada em azul.'
    );
  } else {
    mapa.setMaxBounds(limitesCampus);
    mapa.setMinZoom(16);
    if (primeiraLocalizacao) {
      mapa.setView([latitude, longitude], Math.max(mapa.getZoom(), 17));
    }
    definirStatus('Localização encontrada dentro dos limites do mapa.');
  }

  botaoRota.disabled = !destinoAtual;
}

function tratarErroLocalizacao(erro) {
  const mensagens = {
    1: 'Permissão de localização negada. Autorize o acesso nas configurações do navegador.',
    2: 'Não foi possível determinar sua localização. Verifique o GPS ou a conexão.',
    3: 'A localização demorou demais. Tente novamente.',
  };
  definirStatus(
    mensagens[erro.code] || 'Ocorreu um erro ao obter sua localização.',
    true
  );
  botaoLocalizacao.disabled = false;
  botaoLocalizacao.textContent = 'Tentar localização novamente';

  if (observadorLocalizacao !== null) {
    navigator.geolocation.clearWatch(observadorLocalizacao);
    observadorLocalizacao = null;
  }
}

function iniciarAcompanhamentoLocalizacao() {
  if (!window.isSecureContext) {
    definirStatus('A localização requer uma conexão HTTPS ou acesso por localhost.', true);
    return;
  }

  if (!navigator.geolocation) {
    definirStatus('Este navegador não oferece suporte à localização.', true);
    return;
  }

  if (observadorLocalizacao !== null) {
    return;
  }

  botaoLocalizacao.disabled = true;
  botaoLocalizacao.textContent = 'Localização ativa';
  definirStatus('Obtendo sua localização...');
  observadorLocalizacao = navigator.geolocation.watchPosition(
    atualizarLocalizacao,
    tratarErroLocalizacao,
    {
      enableHighAccuracy: true,
      timeout: 15000,
      maximumAge: 10000,
    }
  );
}

function selecionarDestino(destino) {
  destinoAtual = destino;
  botaoRota.disabled = !posicaoUsuario;
  if (posicaoUsuario) {
    definirStatus(`Destino: ${destino.nome}. Toque em "Traçar rota a pé".`);
  } else {
    definirStatus(`Destino: ${destino.nome}. Agora informe sua localização.`);
  }
}

function decodificarPolyline(encoded, precisao = 6) {
  let indice = 0;
  let latitude = 0;
  let longitude = 0;
  const fator = Math.pow(10, precisao);
  const coordenadas = [];

  function lerDelta() {
    let resultado = 0;
    let deslocamento = 0;
    let byte;

    do {
      if (indice >= encoded.length) {
        throw new Error('A geometria da rota está incompleta.');
      }
      byte = encoded.charCodeAt(indice) - 63;
      indice += 1;
      resultado |= (byte & 0x1f) << deslocamento;
      deslocamento += 5;
    } while (byte >= 0x20);

    return resultado & 1 ? ~(resultado >> 1) : resultado >> 1;
  }

  while (indice < encoded.length) {
    latitude += lerDelta();
    longitude += lerDelta();
    coordenadas.push([latitude / fator, longitude / fator]);
  }

  return coordenadas;
}

function tracarRota() {
  if (!posicaoUsuario || !destinoAtual) {
    return;
  }

  botaoRota.disabled = true;
  definirStatus(`Calculando rota a pé até ${destinoAtual.nome}...`);
  camadaRota.clearLayers();

  const consulta = {
    locations: [
      { lat: posicaoUsuario.latitude, lon: posicaoUsuario.longitude },
      { lat: destinoAtual.latitude, lon: destinoAtual.longitude },
    ],
    costing: 'pedestrian',
    units: 'kilometers',
  };
  const url = `https://valhalla1.openstreetmap.de/route?json=${encodeURIComponent(JSON.stringify(consulta))}`;

  return fetch(url)
    .then((resposta) => {
      if (!resposta.ok) {
        throw new Error(`O serviço de rotas respondeu com erro (${resposta.status}).`);
      }
      return resposta.json();
    })
    .then((dados) => {
      const trecho = dados.trip && dados.trip.legs && dados.trip.legs[0];
      if (!dados.trip || dados.trip.status !== 0 || !trecho || !trecho.shape || !trecho.summary) {
        throw new Error('Não foi possível encontrar um caminho a pé para esse destino.');
      }

      const coordenadasRota = decodificarPolyline(trecho.shape);
      if (coordenadasRota.length < 2) {
        throw new Error('O serviço não retornou um caminho válido.');
      }

      const linhaRota = L.polyline(coordenadasRota, {
        color: '#1769d2',
        weight: 6,
        opacity: 0.85,
      }).addTo(camadaRota);

      const foraDosLimites = !estaDentroDosLimites(
        posicaoUsuario.latitude,
        posicaoUsuario.longitude
      );
      if (foraDosLimites) {
        mapa.setMaxBounds(null);
        mapa.setMinZoom(1);
      }
      mapa.fitBounds(linhaRota.getBounds(), { padding: [40, 40] });

      const distancia = new Intl.NumberFormat('pt-BR', {
        maximumFractionDigits: 1,
      }).format(trecho.summary.length);
      const minutos = Math.ceil(trecho.summary.time / 60);
      definirStatus(`Rota a pé até ${destinoAtual.nome}: ${distancia} km, cerca de ${minutos} min.`);
    })
    .catch((erro) => {
      definirStatus(erro.message || 'Não foi possível calcular a rota a pé.', true);
    })
    .finally(() => {
      botaoRota.disabled = !posicaoUsuario || !destinoAtual;
    });
}

if (botaoLocalizacao && botaoRota && statusLocalizacao) {
  botaoLocalizacao.addEventListener('click', () => {
    iniciarAcompanhamentoLocalizacao();
  });

  botaoRota.addEventListener('click', tracarRota);

  if (navigator.permissions && navigator.permissions.query) {
    navigator.permissions.query({ name: 'geolocation' })
      .then((permissao) => {
        if (permissao.state === 'granted') {
          iniciarAcompanhamentoLocalizacao();
        } else if (permissao.state === 'denied') {
          definirStatus(
            'A localização está bloqueada nas permissões do navegador. Altere a permissão para usar o mapa.',
            true
          );
        }
      })
      .catch(() => {
        definirStatus('Toque em "Usar minha localização" para ativar sua posição no mapa.');
      });
  }
}

// Adiciona os marcadores gerais do mapa
const dadosMarcadores = document.getElementById('mapa-marcadores');

if (dadosMarcadores) {
  const marcadores = JSON.parse(dadosMarcadores.textContent);

  marcadores.forEach((marcador) => {
    const conteudoPopup = document.createElement('div');
    const nome = document.createElement('strong');
    const detalhes = document.createElement('div');

    nome.textContent = marcador.nome;
    detalhes.textContent = marcador.detalhes;

    conteudoPopup.append(nome, detalhes);

    const marcadorMapa = L.marker([marcador.latitude, marcador.longitude])
      .addTo(mapa)
      .bindPopup(conteudoPopup)
      .on('popupopen', (evento) => {
        const botaoExistente = conteudoPopup.querySelector('.botao-destino-mapa');
        if (botaoExistente) {
          botaoExistente.remove();
        }

        const botaoDestino = document.createElement('button');
        botaoDestino.type = 'button';
        botaoDestino.className = 'botao-destino-mapa';
        botaoDestino.textContent = 'Traçar rota até aqui';
        botaoDestino.addEventListener('click', () => {
          selecionarDestino(marcador);
          marcadorMapa.closePopup();
          if (posicaoUsuario) {
            tracarRota();
          }
        });
        conteudoPopup.appendChild(botaoDestino);
      });
  });
}

const dadosLocalSelecionado = document.getElementById('mapa-local-selecionado');

if (dadosLocalSelecionado) {
  const local = JSON.parse(dadosLocalSelecionado.textContent);

  if (local) {
    selecionarDestino(local);
    mapa.setView([local.latitude, local.longitude], 19);

    const conteudoPopup = document.createElement('strong');
    conteudoPopup.textContent = local.nome;

    L.marker([local.latitude, local.longitude])
      .addTo(mapa)
      .bindPopup(conteudoPopup)
      .openPopup();
  }
}
