"""Constants for Adaptive Lighting Pro."""
from typing import Final

DOMAIN: Final = "adaptive_lighting_pro"

# Configuration keys
CONF_LIGHTS: Final = "lights"
CONF_TRIGGER_ENTITIES: Final = "trigger_entities"
CONF_ENABLE_ENTITY: Final = "enable_entity"
CONF_SYNC_GROUP: Final = "sync_group"
CONF_APPLY_DELAY: Final = "apply_delay"
CONF_MIN_BRIGHTNESS: Final = "min_brightness"
CONF_MAX_BRIGHTNESS: Final = "max_brightness"
CONF_MIN_COLOR_TEMP: Final = "min_color_temp"
CONF_MAX_COLOR_TEMP: Final = "max_color_temp"
CONF_TRANSITION: Final = "transition"
CONF_UPDATE_INTERVAL: Final = "update_interval"
CONF_SLEEP_BRIGHTNESS: Final = "sleep_brightness"
CONF_SLEEP_COLOR_TEMP: Final = "sleep_color_temp"
CONF_SUNRISE_OFFSET: Final = "sunrise_offset"
CONF_SUNSET_OFFSET: Final = "sunset_offset"
CONF_BRIGHTNESS_MODE: Final = "brightness_mode"
CONF_COLOR_TEMP_MODE: Final = "color_temp_mode"
CONF_DETECT_OVERRIDE: Final = "detect_manual_override"
CONF_OVERRIDE_TIMEOUT: Final = "manual_override_timeout"

# Default values
DEFAULT_APPLY_DELAY: Final = 500
DEFAULT_MIN_BRIGHTNESS: Final = 20
DEFAULT_MAX_BRIGHTNESS: Final = 100
DEFAULT_MIN_COLOR_TEMP: Final = 2200
DEFAULT_MAX_COLOR_TEMP: Final = 5500
DEFAULT_TRANSITION: Final = 3
DEFAULT_UPDATE_INTERVAL: Final = 60
DEFAULT_SLEEP_BRIGHTNESS: Final = 5
DEFAULT_SLEEP_COLOR_TEMP: Final = 2000

# Modes
MODE_CIRCADIAN: Final = "circadian"
MODE_SOLAR: Final = "solar"
MODE_TIME_BASED: Final = "time_based"

BRIGHTNESS_MODES: Final = [MODE_CIRCADIAN, MODE_SOLAR, MODE_TIME_BASED]
COLOR_TEMP_MODES: Final = [MODE_CIRCADIAN, MODE_SOLAR, MODE_TIME_BASED]

# Entity suffixes
SENSOR_BRIGHTNESS: Final = "brightness"
SENSOR_COLOR_TEMP: Final = "color_temp"
SENSOR_COLOR_TEMP_MIREDS: Final = "color_temp_mireds"
SENSOR_CIRCADIAN_FACTOR: Final = "circadian_factor"
SENSOR_DAY_PROGRESS: Final = "day_progress"
SENSOR_SUN_ELEVATION: Final = "sun_elevation"
SENSOR_SOLAR_POSITION: Final = "solar_position"

SWITCH_ENABLED: Final = "enabled"
SWITCH_SLEEP_MODE: Final = "sleep_mode"

NUMBER_MIN_BRIGHTNESS: Final = "min_brightness"
NUMBER_MAX_BRIGHTNESS: Final = "max_brightness"
NUMBER_MIN_COLOR_TEMP: Final = "min_color_temp"
NUMBER_MAX_COLOR_TEMP: Final = "max_color_temp"
NUMBER_TRANSITION: Final = "transition"

# Services
SERVICE_APPLY_LIGHTING: Final = "apply_lighting"
SERVICE_SET_OVERRIDE: Final = "set_manual_override"
SERVICE_CLEAR_OVERRIDE: Final = "clear_manual_override"

# Attributes
ATTR_BRIGHTNESS: Final = "brightness"
ATTR_COLOR_TEMP: Final = "color_temp"
ATTR_MANUAL_OVERRIDE: Final = "manual_override"
ATTR_SLEEP_MODE: Final = "sleep_mode"
ATTR_SYNC_GROUP: Final = "sync_group"

# Storage
SYNC_GROUPS: Final = "sync_groups"
