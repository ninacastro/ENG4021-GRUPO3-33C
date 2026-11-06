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
