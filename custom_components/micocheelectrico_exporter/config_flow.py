import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import DOMAIN


def get_schema(defaults=None):
    """Esquema de configuración."""

    defaults = defaults or {}

    return vol.Schema(
        {
            vol.Required(
                "token",
                default=defaults.get("token", "")
            ): str,

            vol.Required(
                "battery_sensor",
                default=defaults.get("battery_sensor")
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain="sensor",
                    device_class="battery"
                )
            ),

            vol.Required(
                "range_sensor",
                default=defaults.get("range_sensor")
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain="sensor"
                )
            ),

            vol.Required(
                "odometer_sensor",
                default=defaults.get("odometer_sensor")
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain="sensor"
                )
            ),

            vol.Required(
                "charging_sensor",
                default=defaults.get("charging_sensor")
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain="sensor"
                )
            ),

            vol.Required(
                "gps_tracker",
                default=defaults.get("gps_tracker")
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain="device_tracker"
                )
            ),

            vol.Optional(
                "charge_power_sensor",
                default=defaults.get("charge_power_sensor")
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain="sensor"
                )
            ),

            vol.Optional(
                "plugged_sensor",
                default=defaults.get("plugged_sensor")
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain="binary_sensor"
                )
            ),
        }
    )


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow para MiCocheEléctrico Exporter."""

    VERSION = 1


    async def async_step_user(self, user_input=None):
        """Configuración inicial."""

        if user_input is not None:

            self._user_input = user_input

            return await self.async_step_verify()

        return self.async_show_form(
            step_id="user",
            data_schema=get_schema()
        )


    async def async_step_verify(self, user_input=None):
        """Verificación antes de crear integración."""

        if user_input is not None:

            return self.async_create_entry(
                title="MiCocheEléctrico",
                data=self._user_input
            )

        return self.async_show_form(
            step_id="verify",
            description_placeholders=self._get_sensor_values(),
            data_schema=vol.Schema({})
        )


    async def async_step_reconfigure(self, user_input=None):
        """Reconfigurar integración existente."""

        entry = self._get_reconfigure_entry()

        if user_input is not None:

            self._reconfigure_entry = entry
            self._user_input = user_input

            return await self.async_step_verify_reconfigure()

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=get_schema(entry.data)
        )


    async def async_step_verify_reconfigure(self, user_input=None):
        """Verificación antes de guardar cambios."""

        if user_input is not None:

            self.hass.config_entries.async_update_entry(
                self._reconfigure_entry,
                data=self._user_input
            )

            # No hacemos async_reload aquí.
            # Evita error FAILED_UNLOAD si la integración no puede descargarse.

            return self.async_abort(
                reason="reconfigure_successful"
            )


        return self.async_show_form(
            step_id="verify_reconfigure",
            description_placeholders=self._get_sensor_values(),
            data_schema=vol.Schema({})
        )


    def _get_sensor_values(self):
        """Obtener valores actuales de sensores."""

        data = self._user_input

        bateria = self.hass.states.get(
            data["battery_sensor"]
        )

        autonomia = self.hass.states.get(
            data["range_sensor"]
        )

        odometro = self.hass.states.get(
            data["odometer_sensor"]
        )

        carga = self.hass.states.get(
            data["charging_sensor"]
        )

        gps = self.hass.states.get(
            data["gps_tracker"]
        )

        potencia = (
            self.hass.states.get(data["charge_power_sensor"])
            if data.get("charge_power_sensor")
            else None
        )

        enchufado = (
            self.hass.states.get(data["plugged_sensor"])
            if data.get("plugged_sensor")
            else None
        )

        return {

            "battery_sensor": data["battery_sensor"],
            "battery_value": (
                bateria.state
                if bateria
                else "No disponible"
            ),

            "range_sensor": data["range_sensor"],
            "range_value": (
                autonomia.state
                if autonomia
                else "No disponible"
            ),

            "odometer_sensor": data["odometer_sensor"],
            "odometer_value": (
                odometro.state
                if odometro
                else "No disponible"
            ),

            "charging_sensor": data["charging_sensor"],
            "charging_value": (
                carga.state
                if carga
                else "No disponible"
            ),

            "gps_tracker": data["gps_tracker"],
            "gps_value": (
                gps.state
                if gps
                else "No disponible"
            ),

            "charge_power_sensor": (
                data.get("charge_power_sensor")
                or "No configurado"
            ),
            "charge_power_value": (
                potencia.state
                if potencia
                else "No disponible"
            ),

            "plugged_sensor": (
                data.get("plugged_sensor")
                or "No configurado"
            ),
            "plugged_value": (
                enchufado.state
                if enchufado
                else "No disponible"
            ),
        }