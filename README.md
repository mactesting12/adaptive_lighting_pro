# Adaptive Lighting Pro

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/your-username/adaptive-lighting-pro.svg)](https://github.com/your-username/adaptive-lighting-pro/releases)

Advanced adaptive lighting for Home Assistant with circadian rhythm support, full sensor exposure, Zigbee switch watching, and room synchronization.

## Features

### 🌅 Circadian Lighting
- Natural bell-curve brightness/color following the sun
- Three modes: Circadian, Solar (elevation-based), Time-based (linear)
- Configurable sunrise/sunset offsets

### 📊 Full Sensor Exposure
All calculated values available as sensors:
- **Brightness** (%)
- **Color Temperature** (K and Mireds)
- **Circadian Factor** (%)
- **Day Progress** (%)
- **Sun Elevation** (°)
- **Solar Position** (Golden Hour, Twilight, etc.)
- **Status** (Active, Sleep, Override)

### 🔌 Zigbee Switch Support
Solves the common problem where Zigbee switches controlling smart bulbs don't trigger adaptive lighting:
- Add switches/groups as "Trigger Entities"
- Configurable delay after turn-on
- Works with light groups

### 🔗 Room Synchronization
Keep multiple rooms at identical brightness/color:
- Give rooms the same "Sync Group" name
- First room calculates, others follow
- Great for open floor plans

### 🎛️ Control Entities
Each room gets:
- **Enabled** switch
- **Sleep Mode** switch
- **Manual Override** switch
- Adjustable **Min/Max Brightness**
- Adjustable **Min/Max Color Temp**
- Adjustable **Transition Time**

### 🤖 Automation Integration
- Link an `input_boolean` to enable/disable per room
- Easy scene integration
- Services for programmatic control

## Installation

### HACS (Recommended)

1. Open HACS → Integrations
2. Click the three dots menu → Custom repositories
3. Add: `https://github.com/mactesting12/adaptive-lighting-pro`
4. Category: Integration
5. Click "Add"
6. Search for "Adaptive Lighting Pro" and download
7. Restart Home Assistant

### Manual

1. Download the `custom_components/adaptive_lighting_pro` folder
2. Copy to your `config/custom_components/` directory
3. Restart Home Assistant

## Setup

1. Go to **Settings → Devices & Services**
2. Click **+ Add Integration**
3. Search for "Adaptive Lighting Pro"
4. Follow the setup wizard:
   - **Room Setup**: Name, lights, triggers, sync group
   - **Brightness**: Min/max and mode
   - **Color Temperature**: Min/max and mode
   - **Timing**: Sun offsets, transition, update interval
   - **Sleep Mode**: Brightness and color temp
   - **Override**: Detection and timeout

## Configuration Options

### Room Setup
| Option | Description |
|--------|-------------|
| Room Name | Unique name for this configuration |
| Lights | Light entities to control |
| Trigger Switches | Entities to watch for ON (Zigbee switches, groups) |
| Enable Control | input_boolean to enable/disable via automation |
| Sync Group | Name to sync multiple rooms together |
| Apply Delay | Milliseconds to wait after trigger (helps Zigbee) |

### Brightness/Color Temp Modes
| Mode | Description |
|------|-------------|
| Circadian | Natural bell curve, peaks at solar noon |
| Solar | Directly follows sun elevation angle |
| Time-based | Linear from sunrise to sunset |

## Example: Zigbee Setup

If you have a Zigbee wall switch controlling Hue bulbs:

1. Add your Hue bulbs to **Lights**
2. Add your Zigbee switch to **Trigger Switches**
3. Set **Apply Delay** to 500-1000ms

Now when the Zigbee switch turns on, adaptive lighting will apply to the bulbs.

## Example: Room Sync

To sync your living room and kitchen:

**Living Room config:**
- Sync Group: `main_floor`

**Kitchen config:**
- Sync Group: `main_floor`

Both rooms will now have identical brightness and color temperature.

## Example: Automation Control

Create an input_boolean:

```yaml
input_boolean:
  adaptive_lighting_living_room:
    name: "Living Room Adaptive Lighting"
```

Select it as **Enable Control** in the config.

Now you can control it:

```yaml
automation:
  - alias: "Disable for Movie Mode"
    trigger:
      - platform: state
        entity_id: input_boolean.movie_mode
        to: "on"
    action:
      - service: input_boolean.turn_off
        target:
          entity_id: input_boolean.adaptive_lighting_living_room
```

## Services

### `adaptive_lighting_pro.apply_lighting`
Manually apply current values to lights.

### `adaptive_lighting_pro.set_manual_override`
Pause adaptive lighting for a duration.

### `adaptive_lighting_pro.clear_manual_override`
Resume adaptive lighting immediately.

## Comparison with Adaptive Lighting (HACS)

| Feature | Adaptive Lighting | This Integration |
|---------|-------------------|------------------|
| Circadian rhythm | ✅ | ✅ |
| Brightness sensor | ❌ | ✅ |
| Color temp sensor | ❌ | ✅ |
| All values as sensors | ❌ | ✅ |
| Trigger/switch watching | ❌ | ✅ |
| Room sync groups | ❌ | ✅ |
| External enable entity | ❌ | ✅ |
| Configurable apply delay | ❌ | ✅ |
| Adjustable via UI | Limited | ✅ Full |

## Support

- [Report Issues](https://github.com/mactesting12/adaptive-lighting-pro/issues)
- [Discussions](https://github.com/mactesting12/adaptive-lighting-pro/discussions)

## License

MIT License - see [LICENSE](LICENSE)
