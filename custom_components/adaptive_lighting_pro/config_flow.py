"""Config flow for Adaptive Lighting Pro."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
    CONF_LIGHTS,
    CONF_TRIGGER_ENTITIES,
    CONF_ENABLE_ENTITY,
    CONF_SYNC_GROUP,
    CONF_APPLY_DELAY,
    CONF_INSTANT_TRANSITION,
    CONF_MIN_BRIGHTNESS,
    CONF_MAX_BRIGHTNESS,
    CONF_MIN_COLOR_TEMP,
    CONF_MAX_COLOR_TEMP,
    CONF_TRANSITION,
    CONF_UPDATE_INTERVAL,
    CONF_SLEEP_BRIGHTNESS,
    CONF_SLEEP_COLOR_TEMP,
    CONF_SUNRISE_OFFSET,
    CONF_SUNSET_OFFSET,
    CONF_BRIGHTNESS_MODE,
    CONF_COLOR_TEMP_MODE,
    CONF_DETECT_OVERRIDE,
    CONF_OVERRIDE_TIMEOUT,
    DEFAULT_APPLY_DELAY,
    DEFAULT_MIN_BRIGHTNESS,
    DEFAULT_MAX_BRIGHTNESS,
    DEFAULT_MIN_COLOR_TEMP,
    DEFAULT_MAX_COLOR_TEMP,
    DEFAULT_TRANSITION,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_SLEEP_BRIGHTNESS,
    DEFAULT_SLEEP_COLOR_TEMP,
    MODE_CIRCADIAN,
    SYNC_GROUPS,
)

_LOGGER = logging.getLogger(__name__)

MODE_OPTIONS = [
    selector.SelectOptionDict(value="circadian", label="Circadian (Natural curve)"),
    selector.SelectOptionDict(value="solar", label="Solar (Sun elevation)"),
    selector.SelectOptionDict(value="time_based", label="Time-based (Linear)"),
]


class AdaptiveLightingProConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Adaptive Lighting Pro."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize."""
        self._data: dict[str, Any] = {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Step 1: Basic setup - name, lights, triggers."""
        errors: dict[str, str] = {}

        if user_input is not None:
            if not user_input.get(CONF_LIGHTS):
                errors["base"] = "no_lights"
            else:
                self._data.update(user_input)
                return await self.async_step_brightness()

        # Get existing sync groups for dropdown
        sync_group_options = self._get_sync_group_options()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_NAME, default="Living Room"): selector.TextSelector(),
                vol.Required(CONF_LIGHTS, default=[]): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="light", multiple=True)
                ),
                vol.Optional(CONF_TRIGGER_ENTITIES, default=[]): selector.EntitySelector(
                    selector.EntitySelectorConfig(multiple=True)
                ),
                vol.Optional(CONF_ENABLE_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="input_boolean")
                ),
                vol.Optional(CONF_SYNC_GROUP, default=""): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=sync_group_options,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                        custom_value=True,
                        sort=True,
                    )
                ),
                vol.Optional(CONF_APPLY_DELAY, default=DEFAULT_APPLY_DELAY): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=5000, step=100, unit_of_measurement="ms", mode=selector.NumberSelectorMode.SLIDER)
                ),
                vol.Optional(CONF_INSTANT_TRANSITION, default=True): selector.BooleanSelector(),
            }),
            errors=errors,
            description_placeholders={"name": "Room Name"},
        )

    def _get_sync_group_options(self) -> list[selector.SelectOptionDict]:
        """Get existing sync groups as dropdown options."""
        options = [
            selector.SelectOptionDict(value="", label="None (No Sync)"),
        ]
        
        # Get existing sync groups from hass.data
        if self.hass.data.get(DOMAIN) and self.hass.data[DOMAIN].get(SYNC_GROUPS):
            existing_groups = list(self.hass.data[DOMAIN][SYNC_GROUPS].keys())
            for group in sorted(existing_groups):
                # Count rooms in this group
                group_data = self.hass.data[DOMAIN][SYNC_GROUPS][group]
                room_count = len(group_data.get("controllers", []))
                options.append(
                    selector.SelectOptionDict(
                        value=group, 
                        label=f"{group} ({room_count} room{'s' if room_count != 1 else ''})"
                    )
                )
        
        return options

    async def async_step_brightness(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Step 2: Brightness settings."""
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_color_temp()

        return self.async_show_form(
            step_id="brightness",
            data_schema=vol.Schema({
                vol.Required(CONF_MIN_BRIGHTNESS, default=DEFAULT_MIN_BRIGHTNESS): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=1, max=100, step=1, unit_of_measurement="%", mode=selector.NumberSelectorMode.SLIDER)
                ),
                vol.Required(CONF_MAX_BRIGHTNESS, default=DEFAULT_MAX_BRIGHTNESS): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=1, max=100, step=1, unit_of_measurement="%", mode=selector.NumberSelectorMode.SLIDER)
                ),
                vol.Required(CONF_BRIGHTNESS_MODE, default=MODE_CIRCADIAN): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=MODE_OPTIONS, mode=selector.SelectSelectorMode.DROPDOWN)
                ),
            }),
        )

    async def async_step_color_temp(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Step 3: Color temperature settings."""
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_timing()

        return self.async_show_form(
            step_id="color_temp",
            data_schema=vol.Schema({
                vol.Required(CONF_MIN_COLOR_TEMP, default=DEFAULT_MIN_COLOR_TEMP): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=1800, max=6500, step=100, unit_of_measurement="K", mode=selector.NumberSelectorMode.SLIDER)
                ),
                vol.Required(CONF_MAX_COLOR_TEMP, default=DEFAULT_MAX_COLOR_TEMP): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=1800, max=6500, step=100, unit_of_measurement="K", mode=selector.NumberSelectorMode.SLIDER)
                ),
                vol.Required(CONF_COLOR_TEMP_MODE, default=MODE_CIRCADIAN): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=MODE_OPTIONS, mode=selector.SelectSelectorMode.DROPDOWN)
                ),
            }),
        )

    async def async_step_timing(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Step 4: Timing settings."""
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_sleep()

        return self.async_show_form(
            step_id="timing",
            data_schema=vol.Schema({
                vol.Required(CONF_SUNRISE_OFFSET, default=0): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=-120, max=120, step=5, unit_of_measurement="min", mode=selector.NumberSelectorMode.SLIDER)
                ),
                vol.Required(CONF_SUNSET_OFFSET, default=0): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=-120, max=120, step=5, unit_of_measurement="min", mode=selector.NumberSelectorMode.SLIDER)
                ),
                vol.Required(CONF_TRANSITION, default=DEFAULT_TRANSITION): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=60, step=1, unit_of_measurement="s", mode=selector.NumberSelectorMode.SLIDER)
                ),
                vol.Required(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=30, max=600, step=30, unit_of_measurement="s", mode=selector.NumberSelectorMode.SLIDER)
                ),
            }),
        )

    async def async_step_sleep(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Step 5: Sleep mode settings."""
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_override()

        return self.async_show_form(
            step_id="sleep",
            data_schema=vol.Schema({
                vol.Required(CONF_SLEEP_BRIGHTNESS, default=DEFAULT_SLEEP_BRIGHTNESS): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=1, max=50, step=1, unit_of_measurement="%", mode=selector.NumberSelectorMode.SLIDER)
                ),
                vol.Required(CONF_SLEEP_COLOR_TEMP, default=DEFAULT_SLEEP_COLOR_TEMP): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=1800, max=3000, step=100, unit_of_measurement="K", mode=selector.NumberSelectorMode.SLIDER)
                ),
            }),
        )

    async def async_step_override(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Step 6: Override detection settings."""
        if user_input is not None:
            self._data.update(user_input)
            return self.async_create_entry(
                title=self._data[CONF_NAME], 
                data=self._data,
            )

        return self.async_show_form(
            step_id="override",
            data_schema=vol.Schema({
                vol.Required(CONF_DETECT_OVERRIDE, default=True): selector.BooleanSelector(),
                vol.Required(CONF_OVERRIDE_TIMEOUT, default=30): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=1, max=180, step=5, unit_of_measurement="min", mode=selector.NumberSelectorMode.SLIDER)
                ),
            }),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        """Get options flow."""
        return AdaptiveLightingProOptionsFlow(config_entry)


class AdaptiveLightingProOptionsFlow(config_entries.OptionsFlow):
    """Options flow for Adaptive Lighting Pro."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize."""
        self._config_entry = config_entry
        self._data: dict[str, Any] = dict(config_entry.data)

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Start options flow."""
        return await self.async_step_user()

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Options step 1."""
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_brightness()

        # Get existing sync groups for dropdown
        sync_group_options = self._get_sync_group_options()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_NAME, default=self._data.get(CONF_NAME, "")): selector.TextSelector(),
                vol.Required(CONF_LIGHTS, default=self._data.get(CONF_LIGHTS, [])): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="light", multiple=True)
                ),
                vol.Optional(CONF_TRIGGER_ENTITIES, default=self._data.get(CONF_TRIGGER_ENTITIES, [])): selector.EntitySelector(
                    selector.EntitySelectorConfig(multiple=True)
                ),
                vol.Optional(CONF_ENABLE_ENTITY, default=self._data.get(CONF_ENABLE_ENTITY, "")): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="input_boolean")
                ),
                vol.Optional(CONF_SYNC_GROUP, default=self._data.get(CONF_SYNC_GROUP, "")): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=sync_group_options,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                        custom_value=True,
                        sort=True,
                    )
                ),
                vol.Optional(CONF_APPLY_DELAY, default=self._data.get(CONF_APPLY_DELAY, DEFAULT_APPLY_DELAY)): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=5000, step=100, unit_of_measurement="ms", mode=selector.NumberSelectorMode.SLIDER)
                ),
                vol.Optional(CONF_INSTANT_TRANSITION, default=self._data.get(CONF_INSTANT_TRANSITION, True)): selector.BooleanSelector(),
            }),
        )

    def _get_sync_group_options(self) -> list[selector.SelectOptionDict]:
        """Get existing sync groups as dropdown options."""
        options = [
            selector.SelectOptionDict(value="", label="None (No Sync)"),
        ]
        
        # Get existing sync groups from hass.data
        if self.hass.data.get(DOMAIN) and self.hass.data[DOMAIN].get(SYNC_GROUPS):
            existing_groups = list(self.hass.data[DOMAIN][SYNC_GROUPS].keys())
            for group in sorted(existing_groups):
                group_data = self.hass.data[DOMAIN][SYNC_GROUPS][group]
                room_count = len(group_data.get("controllers", []))
                options.append(
                    selector.SelectOptionDict(
                        value=group, 
                        label=f"{group} ({room_count} room{'s' if room_count != 1 else ''})"
                    )
                )
        
        return options

    async def async_step_brightness(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Options step 2."""
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_color_temp()

        return self.async_show_form(
            step_id="brightness",
            data_schema=vol.Schema({
                vol.Required(CONF_MIN_BRIGHTNESS, default=self._data.get(CONF_MIN_BRIGHTNESS, DEFAULT_MIN_BRIGHTNESS)): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=1, max=100, step=1, unit_of_measurement="%", mode=selector.NumberSelectorMode.SLIDER)
                ),
                vol.Required(CONF_MAX_BRIGHTNESS, default=self._data.get(CONF_MAX_BRIGHTNESS, DEFAULT_MAX_BRIGHTNESS)): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=1, max=100, step=1, unit_of_measurement="%", mode=selector.NumberSelectorMode.SLIDER)
                ),
                vol.Required(CONF_BRIGHTNESS_MODE, default=self._data.get(CONF_BRIGHTNESS_MODE, MODE_CIRCADIAN)): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=MODE_OPTIONS, mode=selector.SelectSelectorMode.DROPDOWN)
                ),
            }),
        )

    async def async_step_color_temp(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Options step 3."""
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_timing()

        return self.async_show_form(
            step_id="color_temp",
            data_schema=vol.Schema({
                vol.Required(CONF_MIN_COLOR_TEMP, default=self._data.get(CONF_MIN_COLOR_TEMP, DEFAULT_MIN_COLOR_TEMP)): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=1800, max=6500, step=100, unit_of_measurement="K", mode=selector.NumberSelectorMode.SLIDER)
                ),
                vol.Required(CONF_MAX_COLOR_TEMP, default=self._data.get(CONF_MAX_COLOR_TEMP, DEFAULT_MAX_COLOR_TEMP)): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=1800, max=6500, step=100, unit_of_measurement="K", mode=selector.NumberSelectorMode.SLIDER)
                ),
                vol.Required(CONF_COLOR_TEMP_MODE, default=self._data.get(CONF_COLOR_TEMP_MODE, MODE_CIRCADIAN)): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=MODE_OPTIONS, mode=selector.SelectSelectorMode.DROPDOWN)
                ),
            }),
        )

    async def async_step_timing(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Options step 4."""
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_sleep()

        return self.async_show_form(
            step_id="timing",
            data_schema=vol.Schema({
                vol.Required(CONF_SUNRISE_OFFSET, default=self._data.get(CONF_SUNRISE_OFFSET, 0)): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=-120, max=120, step=5, unit_of_measurement="min", mode=selector.NumberSelectorMode.SLIDER)
                ),
                vol.Required(CONF_SUNSET_OFFSET, default=self._data.get(CONF_SUNSET_OFFSET, 0)): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=-120, max=120, step=5, unit_of_measurement="min", mode=selector.NumberSelectorMode.SLIDER)
                ),
                vol.Required(CONF_TRANSITION, default=self._data.get(CONF_TRANSITION, DEFAULT_TRANSITION)): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=60, step=1, unit_of_measurement="s", mode=selector.NumberSelectorMode.SLIDER)
                ),
                vol.Required(CONF_UPDATE_INTERVAL, default=self._data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=30, max=600, step=30, unit_of_measurement="s", mode=selector.NumberSelectorMode.SLIDER)
                ),
            }),
        )

    async def async_step_sleep(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Options step 5."""
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_override()

        return self.async_show_form(
            step_id="sleep",
            data_schema=vol.Schema({
                vol.Required(CONF_SLEEP_BRIGHTNESS, default=self._data.get(CONF_SLEEP_BRIGHTNESS, DEFAULT_SLEEP_BRIGHTNESS)): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=1, max=50, step=1, unit_of_measurement="%", mode=selector.NumberSelectorMode.SLIDER)
                ),
                vol.Required(CONF_SLEEP_COLOR_TEMP, default=self._data.get(CONF_SLEEP_COLOR_TEMP, DEFAULT_SLEEP_COLOR_TEMP)): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=1800, max=3000, step=100, unit_of_measurement="K", mode=selector.NumberSelectorMode.SLIDER)
                ),
            }),
        )

    async def async_step_override(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Options step 6."""
        if user_input is not None:
            self._data.update(user_input)
            self.hass.config_entries.async_update_entry(self._config_entry, data=self._data)
            return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="override",
            data_schema=vol.Schema({
                vol.Required(CONF_DETECT_OVERRIDE, default=self._data.get(CONF_DETECT_OVERRIDE, True)): selector.BooleanSelector(),
                vol.Required(CONF_OVERRIDE_TIMEOUT, default=self._data.get(CONF_OVERRIDE_TIMEOUT, 30)): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=1, max=180, step=5, unit_of_measurement="min", mode=selector.NumberSelectorMode.SLIDER)
                ),
            }),
        )
