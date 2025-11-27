"""Number platform for Adaptive Lighting Pro."""
from __future__ import annotations

import logging

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, PERCENTAGE
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
    """Set up number entities."""
    controller: AdaptiveLightingController = hass.data[DOMAIN][entry.entry_id]
    
    async_add_entities([
        MinBrightnessNumber(controller, entry),
        MaxBrightnessNumber(controller, entry),
        MinColorTempNumber(controller, entry),
        MaxColorTempNumber(controller, entry),
        TransitionNumber(controller, entry),
        SleepBrightnessNumber(controller, entry),
        SleepColorTempNumber(controller, entry),
    ], True)


class BaseNumber(NumberEntity):
    """Base number class."""

    _attr_has_entity_name = True
    _attr_should_poll = True
    _attr_mode = NumberMode.SLIDER

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


class MinBrightnessNumber(BaseNumber):
    """Minimum brightness setting."""

    _attr_native_min_value = 1
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_icon = "mdi:brightness-4"

    def __init__(self, controller: AdaptiveLightingController, entry: ConfigEntry) -> None:
        super().__init__(controller, entry)
        self._attr_unique_id = f"{entry.entry_id}_min_brightness"
        self._attr_name = "Minimum Brightness"

    @property
    def native_value(self) -> float:
        return self._controller.min_brightness

    async def async_set_native_value(self, value: float) -> None:
        self._controller.min_brightness = int(value)


class MaxBrightnessNumber(BaseNumber):
    """Maximum brightness setting."""

    _attr_native_min_value = 1
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_icon = "mdi:brightness-7"

    def __init__(self, controller: AdaptiveLightingController, entry: ConfigEntry) -> None:
        super().__init__(controller, entry)
        self._attr_unique_id = f"{entry.entry_id}_max_brightness"
        self._attr_name = "Maximum Brightness"

    @property
    def native_value(self) -> float:
        return self._controller.max_brightness

    async def async_set_native_value(self, value: float) -> None:
        self._controller.max_brightness = int(value)


class MinColorTempNumber(BaseNumber):
    """Minimum color temperature setting."""

    _attr_native_min_value = 1800
    _attr_native_max_value = 6500
    _attr_native_step = 100
    _attr_native_unit_of_measurement = "K"
    _attr_icon = "mdi:thermometer-low"

    def __init__(self, controller: AdaptiveLightingController, entry: ConfigEntry) -> None:
        super().__init__(controller, entry)
        self._attr_unique_id = f"{entry.entry_id}_min_color_temp"
        self._attr_name = "Minimum Color Temp"

    @property
    def native_value(self) -> float:
        return self._controller.min_color_temp

    async def async_set_native_value(self, value: float) -> None:
        self._controller.min_color_temp = int(value)


class MaxColorTempNumber(BaseNumber):
    """Maximum color temperature setting."""

    _attr_native_min_value = 1800
    _attr_native_max_value = 6500
    _attr_native_step = 100
    _attr_native_unit_of_measurement = "K"
    _attr_icon = "mdi:thermometer-high"

    def __init__(self, controller: AdaptiveLightingController, entry: ConfigEntry) -> None:
        super().__init__(controller, entry)
        self._attr_unique_id = f"{entry.entry_id}_max_color_temp"
        self._attr_name = "Maximum Color Temp"

    @property
    def native_value(self) -> float:
        return self._controller.max_color_temp

    async def async_set_native_value(self, value: float) -> None:
        self._controller.max_color_temp = int(value)


class TransitionNumber(BaseNumber):
    """Transition time setting."""

    _attr_native_min_value = 0
    _attr_native_max_value = 60
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "s"
    _attr_icon = "mdi:timer-outline"

    def __init__(self, controller: AdaptiveLightingController, entry: ConfigEntry) -> None:
        super().__init__(controller, entry)
        self._attr_unique_id = f"{entry.entry_id}_transition"
        self._attr_name = "Transition Time"

    @property
    def native_value(self) -> float:
        return self._controller.transition

    async def async_set_native_value(self, value: float) -> None:
        self._controller.transition = int(value)


class SleepBrightnessNumber(BaseNumber):
    """Sleep mode brightness setting."""

    _attr_native_min_value = 1
    _attr_native_max_value = 50
    _attr_native_step = 1
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_icon = "mdi:brightness-4"

    def __init__(self, controller: AdaptiveLightingController, entry: ConfigEntry) -> None:
        super().__init__(controller, entry)
        self._attr_unique_id = f"{entry.entry_id}_sleep_brightness"
        self._attr_name = "Sleep Brightness"

    @property
    def native_value(self) -> float:
        return self._controller.sleep_brightness

    async def async_set_native_value(self, value: float) -> None:
        self._controller.sleep_brightness = int(value)
        # If currently in sleep mode, apply immediately
        if self._controller.sleep_mode:
            await self._controller.async_force_update()


class SleepColorTempNumber(BaseNumber):
    """Sleep mode color temperature setting."""

    _attr_native_min_value = 1800
    _attr_native_max_value = 4000
    _attr_native_step = 100
    _attr_native_unit_of_measurement = "K"
    _attr_icon = "mdi:moon-waning-crescent"

    def __init__(self, controller: AdaptiveLightingController, entry: ConfigEntry) -> None:
        super().__init__(controller, entry)
        self._attr_unique_id = f"{entry.entry_id}_sleep_color_temp"
        self._attr_name = "Sleep Color Temp"

    @property
    def native_value(self) -> float:
        return self._controller.sleep_color_temp

    async def async_set_native_value(self, value: float) -> None:
        self._controller.sleep_color_temp = int(value)
        # If currently in sleep mode, apply immediately
        if self._controller.sleep_mode:
            await self._controller.async_force_update()
