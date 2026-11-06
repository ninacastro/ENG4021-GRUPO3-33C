import math


def parsear_coordenadas(coordenadas):
    partes = coordenadas.split(",")
    if len(partes) != 2:
        raise ValueError("Use o formato latitude, longitude.")

    try:
        latitude, longitude = (float(parte.strip()) for parte in partes)
    except ValueError as erro:
        raise ValueError("Latitude e longitude devem ser números.") from erro

    if (
        not math.isfinite(latitude)
        or not math.isfinite(longitude)
        or not -90 <= latitude <= 90
        or not -180 <= longitude <= 180
    ):
        raise ValueError("Latitude ou longitude fora dos limites válidos.")

    return latitude, longitude
