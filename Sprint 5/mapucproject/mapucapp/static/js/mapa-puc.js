
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

    L.marker([marcador.latitude, marcador.longitude])
      .addTo(mapa)
      .bindPopup(conteudoPopup);
  });
}

// Identifica o local selecionado na busca
const dadosCoordenadas = document.getElementById('coordenadas-selecionadas');
const dadosNomeLocal = document.getElementById('nome-local-selecionado');

if (dadosCoordenadas && dadosNomeLocal) {
  const coordenadas = JSON.parse(dadosCoordenadas.textContent);
  const nomeLocal = JSON.parse(dadosNomeLocal.textContent);

  if (coordenadas && nomeLocal) {
    const correspondencia = coordenadas.match(
      /^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$/
    );

    if (correspondencia) {
      const latitude = Number(correspondencia[1]);
      const longitude = Number(correspondencia[2]);

      if (
        Number.isFinite(latitude) &&
        Number.isFinite(longitude) &&
        Math.abs(latitude) <= 90 &&
        Math.abs(longitude) <= 180
      ) {
        mapa.setView([latitude, longitude], 19);

        const conteudoPopup = document.createElement('strong');
        conteudoPopup.textContent = nomeLocal;

        L.marker([latitude, longitude])
          .addTo(mapa)
          .bindPopup(conteudoPopup)
          .openPopup();
      }
    }
  }
}
