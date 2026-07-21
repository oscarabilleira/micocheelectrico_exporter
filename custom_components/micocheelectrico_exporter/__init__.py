import aiohttp
import time

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

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

        potencia = (
            hass.states.get(datos["charge_power_sensor"])
            if datos.get("charge_power_sensor")
            else None
        )

        # Comprobación mínima de sensores necesarios
        if not bateria or not autonomia or not odometro:
            return

        manufacturer = None
        model = None

        try:
            entity_registry = er.async_get(hass)
            entity_entry = entity_registry.async_get(datos["battery_sensor"])

            if entity_entry and entity_entry.device_id:
                device_registry = dr.async_get(hass)
                device = device_registry.async_get(entity_entry.device_id)

                if device:
                    manufacturer = device.manufacturer
                    model = device.model

        except Exception:
            pass

        # Enviar estado de carga exactamente como lo entrega Home Assistant
        charging_estado = (
            carga.state
            if carga
            else "Unknown"
        )

        # Potencia de carga (kW), si el sensor existe y tiene un valor numérico
        charger_power = 0.0

        if potencia and potencia.state not in (None, "unknown", "unavailable"):

            try:
                charger_power = float(potencia.state)
            except ValueError:
                charger_power = 0.0

        payload = {
            "manufacturer": manufacturer,
            "model": model,

            "odometer": int(float(odometro.state)),
            "range": int(float(autonomia.state)),
            "level": int(float(bateria.state)),
            "charging": charging_estado,

            "plugged": False,

            "chargerPower": charger_power,

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