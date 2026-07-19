import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import DOMAIN


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow para MiCocheEléctrico Exporter."""

    async def async_step_user(self, user_input=None):

        if user_input is not None:
            return self.async_create_entry(
                title="MiCocheEléctrico",
                data=user_input
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("token"): str,

                    vol.Required("battery_sensor"): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain="sensor",
                            device_class="battery"
                        )
                    ),

                    vol.Required("range_sensor"): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain="sensor"
                        )
                    ),

                    vol.Required("odometer_sensor"): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain="sensor"
                        )
                    ),

                    vol.Required("charging_sensor"): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain="sensor"
                        )
                    ),

                    vol.Required("gps_tracker"): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain="device_tracker"
                        )
                    ),
                }
            )
        )