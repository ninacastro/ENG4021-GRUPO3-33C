(() => {
  const campus = [-22.9785, -43.2324];
  const limitesCampus = [
    [-22.9810, -43.2360],
    [-22.9750, -43.2280],
  ];

  const inicializarSeletores = () => {
    document.querySelectorAll('.coordenadas-seletor').forEach((elemento) => {
      const campo = document.getElementById(elemento.dataset.coordenadasInput);
      if (!campo || !window.L) {
        return;
      }

      const mapa = L.map(elemento, {
        center: campus,
        zoom: 17,
        minZoom: 16,
        maxBounds: limitesCampus,
        maxBoundsViscosity: 1,
      });

      L.tileLayer(
        'https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}',
        {
          maxZoom: 19,
          attribution: '© Esri',
        }
      ).addTo(mapa);

      let marcador;

      const posicionarMarcador = (latitude, longitude, atualizarCampo) => {
        const localizacao = [latitude, longitude];

        if (!marcador) {
          marcador = L.marker(localizacao, { draggable: true }).addTo(mapa);
          marcador.on('dragend', () => {
            const posicao = marcador.getLatLng();
            posicionarMarcador(posicao.lat, posicao.lng, true);
          });
        } else {
          marcador.setLatLng(localizacao);
        }

        if (atualizarCampo) {
          campo.value = `${latitude.toFixed(6)}, ${longitude.toFixed(6)}`;
          campo.dispatchEvent(new Event('input', { bubbles: true }));
          campo.dispatchEvent(new Event('change', { bubbles: true }));
        }
      };

      const lerCampo = () => {
        const correspondencia = campo.value.match(
          /^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$/
        );
        if (!correspondencia) {
          return;
        }

        const latitude = Number(correspondencia[1]);
        const longitude = Number(correspondencia[2]);
        if (
          Number.isFinite(latitude)
          && Number.isFinite(longitude)
          && Math.abs(latitude) <= 90
          && Math.abs(longitude) <= 180
        ) {
          posicionarMarcador(latitude, longitude, false);
        }
      };

      mapa.on('click', (evento) => {
        posicionarMarcador(evento.latlng.lat, evento.latlng.lng, true);
      });
      campo.addEventListener('change', lerCampo);
      campo.addEventListener('blur', lerCampo);
      lerCampo();
      window.setTimeout(() => mapa.invalidateSize(), 0);
    });
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', inicializarSeletores, { once: true });
  } else {
    inicializarSeletores();
  }
})();
