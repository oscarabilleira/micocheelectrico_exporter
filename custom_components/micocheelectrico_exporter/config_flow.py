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
        }
    )


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow para MiCocheEléctrico Exporter."""

    VERSION = 1

    async def async_step_user(self, user_input=None):

        if user_input is not None:
            return self.async_create_entry(
                title="MiCocheEléctrico",
                data=user_input
            )

        return self.async_show_form(
            step_id="user",
            data_schema=get_schema()
        )

    async def async_step_reconfigure(self, user_input=None):
        """Permitir reconfigurar la integración."""

        entry = self._get_reconfigure_entry()

        if user_input is not None:

            self.hass.config_entries.async_update_entry(
                entry,
                data=user_input
            )

            await self.hass.config_entries.async_reload(entry.entry_id)

            return self.async_abort(reason="reconfigure_successful")

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=get_schema(entry.data)
        )