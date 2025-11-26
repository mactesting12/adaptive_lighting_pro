"""Switch platform for Adaptive Lighting Pro."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import AdaptiveLightingController
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up switches."""
    controller: AdaptiveLightingController = hass.data[DOMAIN][entry.entry_id]
    
    async_add_entities([
        EnabledSwitch(controller, entry),
        SleepModeSwitch(controller, entry),
        ManualOverrideSwitch(controller, entry),
    ], True)


class BaseSwitch(SwitchEntity):
    """Base switch class."""

    _attr_has_entity_name = True
    _attr_should_poll = True

    def __init__(self, controller: AdaptiveLightingController, entry: ConfigEntry) -> None:
        """Initialize."""
        self._controller = controller
        self._entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"Adaptive Lighting - {entry.data.get(CONF_NAME, 'Unknown')}",
            manufacturer="Adaptive Lighting Pro",
            model="Circadian Controller",
            sw_version="1.0.0",
        )


class EnabledSwitch(BaseSwitch):
    """Switch to enable/disable adaptive lighting."""

    _attr_icon = "mdi:lightbulb-auto"

    def __init__(self, controller: AdaptiveLightingController, entry: ConfigEntry) -> None:
        super().__init__(controller, entry)
        self._attr_unique_id = f"{entry.entry_id}_enabled"
        self._attr_name = "Enabled"

    @property
    def is_on(self) -> bool:
        return self._controller.enabled

    async def async_turn_on(self, **kwargs: Any) -> None:
        self._controller.enabled = True
        _LOGGER.info("Adaptive Lighting enabled: %s", self._controller.name)

    async def async_turn_off(self, **kwargs: Any) -> None:
        self._controller.enabled = False
        _LOGGER.info("Adaptive Lighting disabled: %s", self._controller.name)


class SleepModeSwitch(BaseSwitch):
    """Switch for sleep mode."""

    _attr_icon = "mdi:sleep"

    def __init__(self, controller: AdaptiveLightingController, entry: ConfigEntry) -> None:
        super().__init__(controller, entry)
        self._attr_unique_id = f"{entry.entry_id}_sleep_mode"
        self._attr_name = "Sleep Mode"

    @property
    def is_on(self) -> bool:
        return self._controller.sleep_mode

    async def async_turn_on(self, **kwargs: Any) -> None:
        self._controller.sleep_mode = True
        _LOGGER.info("Sleep mode enabled: %s", self._controller.name)

    async def async_turn_off(self, **kwargs: Any) -> None:
        self._controller.sleep_mode = False
        _LOGGER.info("Sleep mode disabled: %s", self._controller.name)


class ManualOverrideSwitch(BaseSwitch):
    """Switch for manual override."""

    _attr_icon = "mdi:hand-back-right"

    def __init__(self, controller: AdaptiveLightingController, entry: ConfigEntry) -> None:
        super().__init__(controller, entry)
        self._attr_unique_id = f"{entry.entry_id}_manual_override"
        self._attr_name = "Manual Override"

    @property
    def is_on(self) -> bool:
        return self._controller.manual_override

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._controller.async_set_manual_override(30)
        _LOGGER.info("Manual override enabled: %s", self._controller.name)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._controller.async_clear_manual_override()
        _LOGGER.info("Manual override cleared: %s", self._controller.name)
