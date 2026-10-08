"""Funciones auxiliares compartidas por la integración."""


def convertir_potencia_kw(estado):
    """Convierte el estado de un sensor de potencia a kW.

    Recibe el objeto State de Home Assistant. Devuelve una tupla
    (valor_en_kw, unidad_original_en_minusculas), o None si el sensor no
    existe o su valor no es numérico (unknown, unavailable, texto...).

    Si el sensor declara su unidad de medida en W o MW, se convierte a kW.
    Con kW o sin unidad declarada, el valor se deja tal cual.
    """

    if estado is None or estado.state in (None, "unknown", "unavailable"):
        return None

    try:
        valor = float(estado.state)
    except ValueError:
        return None

    unidad = str(
        estado.attributes.get("unit_of_measurement") or ""
    ).strip().lower()

    if unidad == "w":
        valor = valor / 1000
    elif unidad == "mw":
        valor = valor * 1000

    return round(valor, 3), unidad
