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

L.marker([-22.9781, -43.2328])
  .addTo(mapa)
  .bindPopup('<b>Prédio Cardeal Leme</b><br>Salas L, F, etc.');

L.marker([-22.9791, -43.2322])
  .addTo(mapa)
  .bindPopup('<b>RDC</b><br>Laboratórios de Informática e Aulas');

L.marker([-22.9774, -43.2335])
  .addTo(mapa)
  .bindPopup('<b>Prédio da Amizade</b><br>Salas I, Ala Kennedy');
