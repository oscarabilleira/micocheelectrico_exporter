import aiohttp
import time

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval

from .const import DOMAIN


WEBHOOK_URL = "https://abrir.gal/app_micocheelectrico/webhook.php"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry
) -> bool:
    """Configurar la integración."""

    hass.data.setdefault(DOMAIN, {})

    async def enviar_datos(_now):
        datos = entry.data

        token = datos["token"]

        bateria = hass.states.get(datos["battery_sensor"])
        autonomia = hass.states.get(datos["range_sensor"])
        odometro = hass.states.get(datos["odometer_sensor"])
        carga = hass.states.get(datos["charging_sensor"])
        gps = hass.states.get(datos["gps_tracker"])

        # Comprobación mínima de sensores necesarios
        if not bateria or not autonomia or not odometro:
            return

        # Enviar estado de carga exactamente como lo entrega Home Assistant
        charging_estado = (
            carga.state
            if carga
            else "Unknown"
        )

        payload = {
            "odometer": int(float(odometro.state)),
            "range": int(float(autonomia.state)),
            "level": int(float(bateria.state)),
            "charging": charging_estado,

            "plugged": False,

            "latitude": (
                gps.attributes.get("latitude")
                if gps
                else None
            ),

            "longitude": (
                gps.attributes.get("longitude")
                if gps
                else None
            ),

            "timestamp": int(time.time() * 1000)
        }

        url = f"{WEBHOOK_URL}?token={token}"

        try:
            async with aiohttp.ClientSession() as session:

                async with session.post(
                    url,
                    json=payload,
                    timeout=15
                ) as response:

                    respuesta = await response.text()

                    print("MiCocheEléctrico enviado:")
                    print(payload)

                    print("Respuesta servidor:")
                    print(response.status)

                    print(respuesta)

        except Exception as e:

            print(
                f"Error enviando datos MiCocheEléctrico: {e}"
            )


    unsub = async_track_time_interval(
        hass,
        enviar_datos,
        timedelta(minutes=1)
    )

    entry.async_on_unload(unsub)

    return True