"""Adaptive Lighting Pro - Advanced circadian lighting for Home Assistant."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_NAME,
    Platform,
    SERVICE_TURN_ON,
    STATE_ON,
)
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_interval,
)
from homeassistant.util import dt as dt_util

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
    MODE_SOLAR,
    MODE_TIME_BASED,
    SYNC_GROUPS,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.SWITCH, Platform.NUMBER]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Adaptive Lighting Pro from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault(SYNC_GROUPS, {})
    
    controller = AdaptiveLightingController(hass, entry)
    hass.data[DOMAIN][entry.entry_id] = controller
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await controller.async_start()
    await async_register_services(hass)
    
    entry.async_on_unload(entry.add_update_listener(async_update_options))
    
    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    controller: AdaptiveLightingController = hass.data[DOMAIN][entry.entry_id]
    await controller.async_stop()
    
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok


async def async_register_services(hass: HomeAssistant) -> None:
    """Register services for Adaptive Lighting Pro."""
    
    if hass.services.has_service(DOMAIN, "apply_lighting"):
        return
    
    async def handle_apply_lighting(call: ServiceCall) -> None:
        """Apply current adaptive lighting values."""
        entry_id = call.data.get("entry_id")
        entity_id = call.data.get("entity_id")
        
        if entry_id and entry_id in hass.data[DOMAIN]:
            controller = hass.data[DOMAIN][entry_id]
            if isinstance(controller, AdaptiveLightingController):
                await controller.async_apply_lighting(entity_id)
    
    async def handle_set_manual_override(call: ServiceCall) -> None:
        """Set manual override for a room."""
        entry_id = call.data.get("entry_id")
        duration = call.data.get("duration", 30)
        
        if entry_id and entry_id in hass.data[DOMAIN]:
            controller = hass.data[DOMAIN][entry_id]
            if isinstance(controller, AdaptiveLightingController):
                await controller.async_set_manual_override(duration)
    
    async def handle_clear_manual_override(call: ServiceCall) -> None:
        """Clear manual override for a room."""
        entry_id = call.data.get("entry_id")
        
        if entry_id and entry_id in hass.data[DOMAIN]:
            controller = hass.data[DOMAIN][entry_id]
            if isinstance(controller, AdaptiveLightingController):
                await controller.async_clear_manual_override()
    
    hass.services.async_register(DOMAIN, "apply_lighting", handle_apply_lighting)
    hass.services.async_register(DOMAIN, "set_manual_override", handle_set_manual_override)
    hass.services.async_register(DOMAIN, "clear_manual_override", handle_clear_manual_override)


class AdaptiveLightingController:
    """Controller for a single Adaptive Lighting Pro instance."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the controller."""
        self.hass = hass
        self.entry = entry
        self._unsub_interval: callable | None = None
        self._unsub_state_change: list[callable] = []
        self._unsub_trigger_change: list[callable] = []
        self._manual_override = False
        self._manual_override_until: datetime | None = None
        self._last_applied: dict[str, Any] = {}
        
        # Load configuration
        data = entry.data
        self._name = data.get(CONF_NAME, "Adaptive Lighting")
        self._lights = data.get(CONF_LIGHTS, [])
        self._trigger_entities = data.get(CONF_TRIGGER_ENTITIES, [])
        self._enable_entity = data.get(CONF_ENABLE_ENTITY, "")
        self._sync_group = data.get(CONF_SYNC_GROUP, "")
        self._apply_delay = data.get(CONF_APPLY_DELAY, DEFAULT_APPLY_DELAY)
        self._instant_transition = data.get(CONF_INSTANT_TRANSITION, True)
        self._min_brightness = data.get(CONF_MIN_BRIGHTNESS, DEFAULT_MIN_BRIGHTNESS)
        self._max_brightness = data.get(CONF_MAX_BRIGHTNESS, DEFAULT_MAX_BRIGHTNESS)
        self._min_color_temp = data.get(CONF_MIN_COLOR_TEMP, DEFAULT_MIN_COLOR_TEMP)
        self._max_color_temp = data.get(CONF_MAX_COLOR_TEMP, DEFAULT_MAX_COLOR_TEMP)
        self._transition = data.get(CONF_TRANSITION, DEFAULT_TRANSITION)
        self._update_interval = data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
        self._sleep_brightness = data.get(CONF_SLEEP_BRIGHTNESS, DEFAULT_SLEEP_BRIGHTNESS)
        self._sleep_color_temp = data.get(CONF_SLEEP_COLOR_TEMP, DEFAULT_SLEEP_COLOR_TEMP)
        self._sunrise_offset = data.get(CONF_SUNRISE_OFFSET, 0)
        self._sunset_offset = data.get(CONF_SUNSET_OFFSET, 0)
        self._brightness_mode = data.get(CONF_BRIGHTNESS_MODE, MODE_CIRCADIAN)
        self._color_temp_mode = data.get(CONF_COLOR_TEMP_MODE, MODE_CIRCADIAN)
        self._detect_override = data.get(CONF_DETECT_OVERRIDE, True)
        self._override_timeout = data.get(CONF_OVERRIDE_TIMEOUT, 30)
        
        # State
        self._internal_enabled = True
        self._sleep_mode = False
        self._adapt_brightness = True
        self._adapt_color_temp = True
        self._current_brightness = 0
        self._current_color_temp = 0
        self._circadian_factor = 0.0
        self._day_progress = 0.0
        self._sun_elevation = 0.0
    
    @property
    def name(self) -> str:
        """Return the name."""
        return self._name
    
    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return self.entry.entry_id
    
    @property
    def sync_group(self) -> str:
        """Return sync group name."""
        return self._sync_group
    
    @property
    def trigger_entities(self) -> list:
        """Return trigger entities."""
        return self._trigger_entities
    
    @property
    def lights(self) -> list:
        """Return light entities."""
        return self._lights
    
    @property
    def enabled(self) -> bool:
        """Return if controller is enabled."""
        if self._enable_entity:
            enable_state = self.hass.states.get(self._enable_entity)
            if enable_state and enable_state.state == "off":
                return False
        return self._internal_enabled
    
    @enabled.setter
    def enabled(self, value: bool) -> None:
        """Set enabled state."""
        self._internal_enabled = value
    
    @property
    def sleep_mode(self) -> bool:
        """Return sleep mode state."""
        return self._sleep_mode
    
    @sleep_mode.setter
    def sleep_mode(self, value: bool) -> None:
        """Set sleep mode."""
        self._sleep_mode = value
    
    @property
    def adapt_brightness(self) -> bool:
        """Return if brightness adaptation is enabled."""
        return self._adapt_brightness
    
    @adapt_brightness.setter
    def adapt_brightness(self, value: bool) -> None:
        """Set brightness adaptation."""
        self._adapt_brightness = value
    
    @property
    def adapt_color_temp(self) -> bool:
        """Return if color temp adaptation is enabled."""
        return self._adapt_color_temp
    
    @adapt_color_temp.setter
    def adapt_color_temp(self, value: bool) -> None:
        """Set color temp adaptation."""
        self._adapt_color_temp = value
    
    @property
    def current_brightness(self) -> int:
        """Return current brightness."""
        return self._current_brightness
    
    @property
    def current_color_temp(self) -> int:
        """Return current color temperature."""
        return self._current_color_temp
    
    @property
    def circadian_factor(self) -> float:
        """Return circadian factor."""
        return self._circadian_factor
    
    @property
    def day_progress(self) -> float:
        """Return day progress."""
        return self._day_progress
    
    @property
    def sun_elevation(self) -> float:
        """Return sun elevation."""
        return self._sun_elevation
    
    @property
    def manual_override(self) -> bool:
        """Return manual override state."""
        if self._manual_override and self._manual_override_until:
            if dt_util.utcnow() > self._manual_override_until:
                self._manual_override = False
                self._manual_override_until = None
        return self._manual_override
    
    # Setters for number entities
    @property
    def min_brightness(self) -> int:
        return self._min_brightness
    
    @min_brightness.setter
    def min_brightness(self, value: int) -> None:
        self._min_brightness = value
    
    @property
    def max_brightness(self) -> int:
        return self._max_brightness
    
    @max_brightness.setter
    def max_brightness(self, value: int) -> None:
        self._max_brightness = value
    
    @property
    def min_color_temp(self) -> int:
        return self._min_color_temp
    
    @min_color_temp.setter
    def min_color_temp(self, value: int) -> None:
        self._min_color_temp = value
    
    @property
    def max_color_temp(self) -> int:
        return self._max_color_temp
    
    @max_color_temp.setter
    def max_color_temp(self, value: int) -> None:
        self._max_color_temp = value
    
    @property
    def transition(self) -> int:
        return self._transition
    
    @transition.setter
    def transition(self, value: int) -> None:
        self._transition = value

    async def async_start(self) -> None:
        """Start the controller."""
        # Register with sync group
        if self._sync_group:
            sync_groups = self.hass.data[DOMAIN][SYNC_GROUPS]
            if self._sync_group not in sync_groups:
                sync_groups[self._sync_group] = {
                    "brightness": 0,
                    "color_temp": 0,
                    "controllers": [],
                }
            sync_groups[self._sync_group]["controllers"].append(self)
        
        # Initial update
        await self._async_update()
        
        # Periodic updates
        self._unsub_interval = async_track_time_interval(
            self.hass,
            self._async_update,
            timedelta(seconds=self._update_interval),
        )
        
        # Watch trigger entities (for Zigbee switches, light groups, etc.)
        if self._trigger_entities:
            @callback
            def trigger_changed(event):
                if not self.enabled:
                    return
                
                new_state = event.data.get("new_state")
                old_state = event.data.get("old_state")
                
                if new_state is None:
                    return
                
                # Trigger on turn ON
                if new_state.state in ["on", "home", "playing", "open"]:
                    if old_state is None or old_state.state not in ["on", "home", "playing", "open"]:
                        _LOGGER.debug(
                            "Trigger %s turned on for %s, applying %swith %dms delay",
                            event.data.get("entity_id"),
                            self._name,
                            "instantly " if self._instant_transition else "",
                            self._apply_delay,
                        )
                        
                        async def delayed_apply():
                            await asyncio.sleep(self._apply_delay / 1000)
                            # Use instant transition if enabled to prevent visible color shift
                            await self.async_apply_lighting(instant=self._instant_transition)
                        
                        self.hass.async_create_task(delayed_apply())
            
            for trigger in self._trigger_entities:
                unsub = async_track_state_change_event(self.hass, [trigger], trigger_changed)
                self._unsub_trigger_change.append(unsub)
        
        # Watch lights for turn-on and override detection
        if self._lights:
            @callback
            def light_changed(event):
                if not self.enabled:
                    return
                
                entity_id = event.data.get("entity_id")
                new_state = event.data.get("new_state")
                old_state = event.data.get("old_state")
                
                if new_state is None:
                    return
                
                # Light turned ON
                if new_state.state == STATE_ON and (old_state is None or old_state.state != STATE_ON):
                    _LOGGER.debug(
                        "Light %s turned on, applying %swith %dms delay",
                        entity_id,
                        "instantly " if self._instant_transition else "",
                        self._apply_delay,
                    )
                    
                    async def delayed_apply():
                        await asyncio.sleep(self._apply_delay / 1000)
                        # Use instant transition if enabled to prevent visible color shift
                        await self.async_apply_lighting([entity_id], instant=self._instant_transition)
                    
                    self.hass.async_create_task(delayed_apply())
                    return
                
                # Override detection
                if not self._detect_override or old_state is None:
                    return
                
                if new_state.context and new_state.context.parent_id:
                    return
                
                if new_state.state == STATE_ON and old_state.state == STATE_ON:
                    new_attrs = new_state.attributes
                    old_attrs = old_state.attributes
                    
                    if (new_attrs.get("brightness") != old_attrs.get("brightness") or
                        new_attrs.get("color_temp") != old_attrs.get("color_temp")):
                        
                        expected = self._last_applied.get(entity_id, {})
                        if expected:
                            is_our_change = (
                                abs((new_attrs.get("brightness") or 0) - (expected.get("brightness") or 0)) < 5 and
                                abs((new_attrs.get("color_temp") or 0) - (expected.get("color_temp") or 0)) < 10
                            )
                            if not is_our_change:
                                self.hass.async_create_task(
                                    self.async_set_manual_override(self._override_timeout)
                                )
            
            for light in self._lights:
                unsub = async_track_state_change_event(self.hass, [light], light_changed)
                self._unsub_state_change.append(unsub)
        
        _LOGGER.info("Adaptive Lighting Pro started: %s", self._name)

    async def async_stop(self) -> None:
        """Stop the controller."""
        if self._unsub_interval:
            self._unsub_interval()
            self._unsub_interval = None
        
        for unsub in self._unsub_state_change:
            unsub()
        self._unsub_state_change.clear()
        
        for unsub in self._unsub_trigger_change:
            unsub()
        self._unsub_trigger_change.clear()
        
        # Remove from sync group
        if self._sync_group:
            sync_groups = self.hass.data[DOMAIN].get(SYNC_GROUPS, {})
            sync_data = sync_groups.get(self._sync_group)
            if sync_data and self in sync_data["controllers"]:
                sync_data["controllers"].remove(self)
        
        _LOGGER.info("Adaptive Lighting Pro stopped: %s", self._name)

    async def async_set_manual_override(self, duration_minutes: int) -> None:
        """Set manual override."""
        self._manual_override = True
        self._manual_override_until = dt_util.utcnow() + timedelta(minutes=duration_minutes)
        _LOGGER.debug("Manual override set for %s: %d minutes", self._name, duration_minutes)

    async def async_clear_manual_override(self) -> None:
        """Clear manual override."""
        self._manual_override = False
        self._manual_override_until = None
        _LOGGER.debug("Manual override cleared for %s", self._name)
        await self.async_force_update()

    async def async_force_update(self) -> None:
        """Force recalculation and apply to lights immediately."""
        # Recalculate values
        brightness, color_temp = self._calculate_values()
        self._current_brightness = brightness
        self._current_color_temp = color_temp
        
        # Update sync group if applicable
        if self._sync_group:
            sync_groups = self.hass.data[DOMAIN].get(SYNC_GROUPS, {})
            sync_data = sync_groups.get(self._sync_group)
            if sync_data:
                sync_data["brightness"] = brightness
                sync_data["color_temp"] = color_temp
        
        # Apply to lights
        await self.async_apply_lighting()
        
        _LOGGER.debug("Force update completed for %s: brightness=%d, color_temp=%d", 
                      self._name, brightness, color_temp)

    def _get_sun_data(self) -> tuple[datetime | None, datetime | None, float]:
        """Get sunrise, sunset, and elevation."""
        sun = self.hass.states.get("sun.sun")
        if sun is None:
            now = dt_util.now()
            return (
                now.replace(hour=6, minute=0),
                now.replace(hour=18, minute=0),
                45.0 if 6 <= now.hour <= 18 else -10.0
            )
        
        elevation = float(sun.attributes.get("elevation", 0))
        
        sunrise_str = sun.attributes.get("next_rising")
        sunset_str = sun.attributes.get("next_setting")
        
        sunrise = dt_util.parse_datetime(sunrise_str) if sunrise_str else None
        sunset = dt_util.parse_datetime(sunset_str) if sunset_str else None
        
        now = dt_util.utcnow()
        
        # Adjust sunrise to today if it's in the future
        if sunrise and sunrise > now:
            sunrise = sunrise - timedelta(days=1)
        
        # Adjust sunset - if next_setting is tomorrow but sun is already down,
        # we need today's sunset (which has passed)
        if sunset and sunset > now and elevation <= 0:
            # Sun is down, so today's sunset has passed - use yesterday's reference
            sunset = sunset - timedelta(days=1)
        elif sunset and sunrise and sunset < sunrise:
            sunset = sunset + timedelta(days=1)
        
        if sunrise:
            sunrise = sunrise + timedelta(minutes=self._sunrise_offset)
        if sunset:
            sunset = sunset + timedelta(minutes=self._sunset_offset)
        
        return sunrise, sunset, elevation

    def _calculate_factors(self, sunrise, sunset, elevation) -> tuple[float, float, float, float]:
        """Calculate lighting factors."""
        now = dt_util.utcnow()
        
        # If sun is down, we're in nighttime - use minimum values
        if elevation <= 0:
            # Determine if we're before sunrise (early morning) or after sunset (evening)
            if sunrise and now < sunrise:
                day_progress = 0.0  # Pre-dawn
            else:
                day_progress = 1.0  # Post-dusk
            
            # All factors should be 0 when sun is down
            return 0.0, 0.0, 0.0, day_progress
        
        # Sun is up - calculate day progress
        if sunrise and sunset and sunrise < now < sunset:
            total = (sunset - sunrise).total_seconds()
            elapsed = (now - sunrise).total_seconds()
            day_progress = max(0.0, min(1.0, elapsed / total))
        elif sunrise and now < sunrise:
            day_progress = 0.0
        else:
            day_progress = 1.0
        
        # Circadian (bell curve)
        if day_progress <= 0.5:
            circadian = (2 * day_progress) ** 1.5
        else:
            circadian = (2 * (1 - day_progress)) ** 1.5
        
        # Solar (elevation based)
        if elevation >= 60:
            solar = 1.0
        else:
            solar = elevation / 60.0
        
        # Time-based (linear)
        if day_progress <= 0.5:
            time_based = 2 * day_progress
        else:
            time_based = 2 * (1 - day_progress)
        
        return circadian, solar, time_based, day_progress

    def _calculate_values(self) -> tuple[int, int]:
        """Calculate brightness and color temp."""
        sunrise, sunset, elevation = self._get_sun_data()
        circadian, solar, time_based, day_progress = self._calculate_factors(sunrise, sunset, elevation)
        
        self._circadian_factor = circadian
        self._day_progress = day_progress * 100
        self._sun_elevation = elevation
        
        # Select factor based on mode
        if self._brightness_mode == MODE_SOLAR:
            b_factor = solar
        elif self._brightness_mode == MODE_TIME_BASED:
            b_factor = time_based
        else:
            b_factor = circadian
        
        if self._color_temp_mode == MODE_SOLAR:
            ct_factor = solar
        elif self._color_temp_mode == MODE_TIME_BASED:
            ct_factor = time_based
        else:
            ct_factor = circadian
        
        # Apply sleep mode
        if self._sleep_mode:
            return self._sleep_brightness, self._sleep_color_temp
        
        brightness = int(self._min_brightness + (self._max_brightness - self._min_brightness) * b_factor)
        color_temp = int(self._min_color_temp + (self._max_color_temp - self._min_color_temp) * ct_factor)
        
        return brightness, color_temp

    async def _async_update(self, now: datetime | None = None) -> None:
        """Update and apply lighting."""
        if not self.enabled or self.manual_override:
            return
        
        # Check sync group
        use_sync = False
        if self._sync_group:
            sync_groups = self.hass.data[DOMAIN].get(SYNC_GROUPS, {})
            sync_data = sync_groups.get(self._sync_group)
            if sync_data:
                controllers = sync_data.get("controllers", [])
                if controllers and controllers[0] != self and sync_data["brightness"] > 0:
                    use_sync = True
                    self._current_brightness = sync_data["brightness"]
                    self._current_color_temp = sync_data["color_temp"]
        
        if not use_sync:
            brightness, color_temp = self._calculate_values()
            self._current_brightness = brightness
            self._current_color_temp = color_temp
            
            # Update sync group
            if self._sync_group:
                sync_groups = self.hass.data[DOMAIN].get(SYNC_GROUPS, {})
                sync_data = sync_groups.get(self._sync_group)
                if sync_data:
                    sync_data["brightness"] = brightness
                    sync_data["color_temp"] = color_temp
        
        await self.async_apply_lighting()

    async def async_apply_lighting(self, entity_ids: list[str] | None = None, instant: bool = False) -> None:
        """Apply lighting to lights.
        
        Args:
            entity_ids: Specific lights to update, or None for all
            instant: If True, use transition=0 for immediate change
        """
        if not self.enabled:
            return
        
        # If neither adaptation is enabled, skip
        if not self._adapt_brightness and not self._adapt_color_temp:
            return
        
        lights = entity_ids or self._lights
        if not lights:
            return
        
        brightness_255 = int((self._current_brightness / 100) * 255)
        mireds = int(1000000 / self._current_color_temp) if self._current_color_temp > 0 else 370
        
        for light_id in lights:
            state = self.hass.states.get(light_id)
            if state is None or state.state != STATE_ON:
                continue
            
            supported_modes = state.attributes.get("supported_color_modes", [])
            supports_ct = "color_temp" in supported_modes
            
            # Use instant transition (0) when light just turned on, normal otherwise
            transition = 0 if instant else self._transition
            
            service_data = {
                "entity_id": light_id,
                "transition": transition,
            }
            
            # Only add brightness if adapt_brightness is enabled
            if self._adapt_brightness:
                service_data["brightness"] = brightness_255
            
            # Only add color_temp if adapt_color_temp is enabled and supported
            if self._adapt_color_temp and supports_ct:
                service_data["color_temp"] = mireds
            
            # Skip if we have nothing to change
            if len(service_data) <= 2:  # Only entity_id and transition
                continue
            
            self._last_applied[light_id] = {
                "brightness": brightness_255 if self._adapt_brightness else None,
                "color_temp": mireds if self._adapt_color_temp else None,
            }
            
            try:
                await self.hass.services.async_call(
                    "light", SERVICE_TURN_ON, service_data, blocking=False
                )
            except Exception as ex:
                _LOGGER.error("Error applying to %s: %s", light_id, ex)
