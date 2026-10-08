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

        enchufado = (
            hass.states.get(datos["plugged_sensor"])
            if datos.get("plugged_sensor")
            else None
        )

        # Comprobación mínima de sensores necesarios
        if not bateria or not autonomia or not odometro:
            return

        manufacturer = None
        model = None
        charging_integration = None
        all_sensors = {}

        try:
            entity_registry = er.async_get(hass)

            entity_entry_bateria = entity_registry.async_get(datos["battery_sensor"])

            if entity_entry_bateria and entity_entry_bateria.device_id:
                device_registry = dr.async_get(hass)
                device = device_registry.async_get(entity_entry_bateria.device_id)

                if device:
                    manufacturer = device.manufacturer
                    model = device.model

            # Dominio de la integración que expone el sensor de carga
            entity_entry_carga = entity_registry.async_get(datos["charging_sensor"])

            if entity_entry_carga:
                charging_integration = entity_entry_carga.platform

            # Recopilar todas las entidades del mismo dispositivo que el
            # sensor de carga, para poder recomendar el sensor correcto
            # a usuarios que lo hayan configurado mal
            device_id_ref = (
                entity_entry_carga.device_id
                if entity_entry_carga
                else None
            )

            if device_id_ref:
                for ent in entity_registry.entities.values():
                    if ent.device_id == device_id_ref:
                        estado_ent = hass.states.get(ent.entity_id)
                        all_sensors[ent.entity_id] = (
                            estado_ent.state
                            if estado_ent
                            else None
                        )

        except Exception:
            pass

        # Enviar estado de carga exactamente como lo entrega Home Assistant
        charging_estado = (
            carga.state
            if carga
            else "Unknown"
        )

        # Potencia de carga (siempre en kW), si el sensor existe y tiene
        # un valor numérico. Si el sensor declara su unidad de medida en
        # W o MW, se convierte a kW antes de enviar.
        charger_power = 0.0

        if potencia and potencia.state not in (None, "unknown", "unavailable"):

            try:
                charger_power = float(potencia.state)

                unidad_potencia = str(
                    potencia.attributes.get("unit_of_measurement") or ""
                ).strip().lower()

                if unidad_potencia == "w":
                    charger_power = charger_power / 1000
                elif unidad_potencia == "mw":
                    charger_power = charger_power * 1000

                charger_power = round(charger_power, 3)

            except ValueError:
                charger_power = 0.0

        # Enchufado, a partir de un binary_sensor (on/off)
        plugged_estado = False

        if enchufado and enchufado.state not in (None, "unknown", "unavailable"):
            plugged_estado = enchufado.state == "on"

        # Qué entity_id tiene elegido el usuario en cada campo de
        # configuración, para poder revisarlo/recomendar cambios
        # desde el panel de gestión
        campos_seleccionados = {
            "battery_sensor": datos.get("battery_sensor"),
            "range_sensor": datos.get("range_sensor"),
            "odometer_sensor": datos.get("odometer_sensor"),
            "charging_sensor": datos.get("charging_sensor"),
            "gps_tracker": datos.get("gps_tracker"),
            "charge_power_sensor": datos.get("charge_power_sensor"),
            "plugged_sensor": datos.get("plugged_sensor"),
        }

        payload = {
            "manufacturer": manufacturer,
            "model": model,

            "odometer": int(float(odometro.state)),
            "range": int(float(autonomia.state)),
            "level": int(float(bateria.state)),
            "charging": charging_estado,
            "chargingIntegration": charging_integration,
            "chargingSensorEntity": datos["charging_sensor"],
            "allSensors": all_sensors,
            "camposSeleccionados": campos_seleccionados,

            "plugged": plugged_estado,

            "chargerPower": charger_power,

            "chargeRemainingTime": None,

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
