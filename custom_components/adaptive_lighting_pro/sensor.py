"""Sensor platform for Adaptive Lighting Pro."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import AdaptiveLightingController
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors."""
    controller: AdaptiveLightingController = hass.data[DOMAIN][entry.entry_id]
    
    async_add_entities([
        BrightnessSensor(controller, entry),
        ColorTempSensor(controller, entry),
        ColorTempMiredsSensor(controller, entry),
        CircadianFactorSensor(controller, entry),
        DayProgressSensor(controller, entry),
        SunElevationSensor(controller, entry),
        SolarPositionSensor(controller, entry),
        StatusSensor(controller, entry),
        SyncGroupSensor(controller, entry),
    ], True)


class BaseSensor(SensorEntity):
    """Base sensor class."""

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


class BrightnessSensor(BaseSensor):
    """Brightness sensor."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:brightness-percent"

    def __init__(self, controller: AdaptiveLightingController, entry: ConfigEntry) -> None:
        super().__init__(controller, entry)
        self._attr_unique_id = f"{entry.entry_id}_brightness"
        self._attr_name = "Brightness"

    @property
    def native_value(self) -> int:
        return self._controller.current_brightness


class ColorTempSensor(BaseSensor):
    """Color temperature sensor (Kelvin)."""

    _attr_native_unit_of_measurement = "K"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:thermometer"

    def __init__(self, controller: AdaptiveLightingController, entry: ConfigEntry) -> None:
        super().__init__(controller, entry)
        self._attr_unique_id = f"{entry.entry_id}_color_temp"
        self._attr_name = "Color Temperature"

    @property
    def native_value(self) -> int:
        return self._controller.current_color_temp


class ColorTempMiredsSensor(BaseSensor):
    """Color temperature sensor (Mireds)."""

    _attr_native_unit_of_measurement = "mired"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:thermometer"

    def __init__(self, controller: AdaptiveLightingController, entry: ConfigEntry) -> None:
        super().__init__(controller, entry)
        self._attr_unique_id = f"{entry.entry_id}_color_temp_mireds"
        self._attr_name = "Color Temperature Mireds"

    @property
    def native_value(self) -> int:
        ct = self._controller.current_color_temp
        return int(1000000 / ct) if ct > 0 else 0


class CircadianFactorSensor(BaseSensor):
    """Circadian factor sensor."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:sine-wave"

    def __init__(self, controller: AdaptiveLightingController, entry: ConfigEntry) -> None:
        super().__init__(controller, entry)
        self._attr_unique_id = f"{entry.entry_id}_circadian_factor"
        self._attr_name = "Circadian Factor"

    @property
    def native_value(self) -> float:
        return round(self._controller.circadian_factor * 100, 1)


class DayProgressSensor(BaseSensor):
    """Day progress sensor."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:progress-clock"

    def __init__(self, controller: AdaptiveLightingController, entry: ConfigEntry) -> None:
        super().__init__(controller, entry)
        self._attr_unique_id = f"{entry.entry_id}_day_progress"
        self._attr_name = "Day Progress"

    @property
    def native_value(self) -> float:
        return round(self._controller.day_progress, 1)


class SunElevationSensor(BaseSensor):
    """Sun elevation sensor."""

    _attr_native_unit_of_measurement = "°"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:weather-sunny"

    def __init__(self, controller: AdaptiveLightingController, entry: ConfigEntry) -> None:
        super().__init__(controller, entry)
        self._attr_unique_id = f"{entry.entry_id}_sun_elevation"
        self._attr_name = "Sun Elevation"

    @property
    def native_value(self) -> float:
        return round(self._controller.sun_elevation, 1)


class SolarPositionSensor(BaseSensor):
    """Solar position description sensor."""

    _attr_icon = "mdi:sun-compass"

    def __init__(self, controller: AdaptiveLightingController, entry: ConfigEntry) -> None:
        super().__init__(controller, entry)
        self._attr_unique_id = f"{entry.entry_id}_solar_position"
        self._attr_name = "Solar Position"

    @property
    def native_value(self) -> str:
        elevation = self._controller.sun_elevation
        if elevation < -18:
            return "Night"
        elif elevation < -12:
            return "Astronomical Twilight"
        elif elevation < -6:
            return "Nautical Twilight"
        elif elevation < 0:
            return "Civil Twilight"
        elif elevation < 15:
            return "Golden Hour"
        elif elevation < 30:
            return "Morning/Evening"
        else:
            return "Daylight"


class StatusSensor(BaseSensor):
    """Status sensor with attributes."""

    _attr_icon = "mdi:lightbulb-auto"

    def __init__(self, controller: AdaptiveLightingController, entry: ConfigEntry) -> None:
        super().__init__(controller, entry)
        self._attr_unique_id = f"{entry.entry_id}_status"
        self._attr_name = "Status"

    @property
    def native_value(self) -> str:
        if not self._controller.enabled:
            return "Disabled"
        if self._controller.manual_override:
            return "Manual Override"
        if self._controller.sleep_mode:
            return "Sleep Mode"
        
        # Check partial adaptation
        adapt_b = self._controller.adapt_brightness
        adapt_ct = self._controller.adapt_color_temp
        
        if adapt_b and adapt_ct:
            return "Active"
        elif adapt_b:
            return "Brightness Only"
        elif adapt_ct:
            return "Color Temp Only"
        else:
            return "Paused"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        ct = self._controller.current_color_temp
        return {
            "enabled": self._controller.enabled,
            "manual_override": self._controller.manual_override,
            "sleep_mode": self._controller.sleep_mode,
            "adapt_brightness": self._controller.adapt_brightness,
            "adapt_color_temp": self._controller.adapt_color_temp,
            "brightness": self._controller.current_brightness,
            "color_temp_kelvin": ct,
            "color_temp_mireds": int(1000000 / ct) if ct > 0 else 0,
            "circadian_factor": round(self._controller.circadian_factor * 100, 1),
            "day_progress": round(self._controller.day_progress, 1),
            "sun_elevation": round(self._controller.sun_elevation, 1),
            "sync_group": self._controller.sync_group or "None",
            "lights": self._controller.lights,
            "trigger_entities": self._controller.trigger_entities,
        }


class SyncGroupSensor(BaseSensor):
    """Sync group status sensor."""

    _attr_icon = "mdi:link-variant"

    def __init__(self, controller: AdaptiveLightingController, entry: ConfigEntry) -> None:
        super().__init__(controller, entry)
        self._attr_unique_id = f"{entry.entry_id}_sync_group"
        self._attr_name = "Sync Group"

    @property
    def native_value(self) -> str:
        """Return sync group name or 'Not Synced'."""
        if self._controller.sync_group:
            return self._controller.sync_group
        return "Not Synced"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return sync group details."""
        sync_group = self._controller.sync_group
        
        if not sync_group:
            return {
                "is_synced": False,
                "sync_group_name": None,
                "is_leader": False,
                "synced_rooms": [],
                "synced_room_count": 0,
            }
        
        # Get sync group data
        from .const import SYNC_GROUPS
        sync_groups = self._controller.hass.data.get(DOMAIN, {}).get(SYNC_GROUPS, {})
        sync_data = sync_groups.get(sync_group, {})
        controllers = sync_data.get("controllers", [])
        
        # Get room names in this sync group
        synced_rooms = [c.name for c in controllers]
        
        # Check if this room is the leader (first in list)
        is_leader = controllers[0] == self._controller if controllers else False
        
        return {
            "is_synced": True,
            "sync_group_name": sync_group,
            "is_leader": is_leader,
            "synced_rooms": synced_rooms,
            "synced_room_count": len(synced_rooms),
            "leader_room": controllers[0].name if controllers else None,
        }
