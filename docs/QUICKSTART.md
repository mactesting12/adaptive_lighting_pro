# Quick Start Guide - Adaptive Lighting Pro

## 5-Minute Setup (Blueprint)

### Step 1: Download Files

Copy these files to your Home Assistant config folder:

```
config/
├── blueprints/
│   └── automation/
│       └── adaptive_lighting_pro/
│           └── adaptive_lighting_pro.yaml
└── packages/
    └── adaptive_lighting_pro_sensors.yaml
```

### Step 2: Enable Packages

Add to your `configuration.yaml`:

```yaml
homeassistant:
  packages: !include_dir_named packages
```

### Step 3: Restart Home Assistant

Go to Settings → System → Restart

### Step 4: Create Room Automations

1. Go to Settings → Automations & Scenes → Blueprints
2. Find "Adaptive Lighting Pro"
3. Click "Create Automation"
4. Configure your first room:
   - Give it a name like "living_room"
   - Select your lights
   - Adjust brightness/color temp ranges
   - Save

### Step 5: Repeat for Each Room

Create a new automation from the blueprint for each room you want to control.

---

## 10-Minute Setup (Custom Integration)

### Step 1: Install Integration

Copy the `custom_components/adaptive_lighting_pro` folder to:
```
config/custom_components/adaptive_lighting_pro/
```

### Step 2: Restart Home Assistant

Go to Settings → System → Restart

### Step 3: Add Integration

1. Go to Settings → Devices & Services
2. Click "+ Add Integration"
3. Search for "Adaptive Lighting Pro"
4. Follow the setup wizard

### Step 4: Configure Each Room

The wizard will guide you through:
1. Room name and light selection
2. Brightness settings
3. Color temperature settings
4. Timing settings
5. Sleep mode settings
6. Override detection settings

---

## Verify It's Working

### Check Sensors Exist

Go to Developer Tools → States and search for:
- `sensor.adaptive_lighting_pro_*_brightness`
- `sensor.adaptive_lighting_pro_*_color_temperature`

Or for blueprint:
- `input_number.alp_*_brightness`
- `input_number.alp_*_color_temp`

### Test the Lighting

1. Turn on a light in your configured room
2. Check if brightness and color temp match the sensor values
3. Wait for the next update interval or trigger manually

### Dashboard

Add these sensors to your dashboard to monitor:
- Current brightness %
- Current color temperature
- Day progress
- Status (Active/Sleep/Override)

---

## Common Initial Settings

### Living Room (Cozy)
- Min Brightness: 20%
- Max Brightness: 90%
- Min Color Temp: 2200K (warm)
- Max Color Temp: 4500K (neutral)

### Office (Productive)
- Min Brightness: 40%
- Max Brightness: 100%
- Min Color Temp: 2700K (warm-white)
- Max Color Temp: 5500K (daylight)

### Bedroom (Relaxing)
- Min Brightness: 10%
- Max Brightness: 70%
- Min Color Temp: 2000K (candlelight)
- Max Color Temp: 3500K (soft white)
- Sleep Brightness: 5%
- Sleep Color Temp: 2000K

### Bathroom (Functional)
- Min Brightness: 30%
- Max Brightness: 100%
- Min Color Temp: 2700K
- Max Color Temp: 5000K

---

## Troubleshooting

### "Sensors not updating"
- Check automation is enabled (Settings → Automations)
- Verify at least one light in the room is ON
- Check Home Assistant logs for errors

### "Lights not changing"
- Verify the Enabled switch is ON
- Check for Manual Override being active
- Confirm lights support color temperature

### "Color temp not working"
Some lights only support brightness. Check:
```yaml
{{ state_attr('light.your_light', 'supported_color_modes') }}
```
If it shows `['brightness']` only, the light doesn't support color temp.

---

## Next Steps

1. **Add Dashboard Cards**: See `docs/lovelace_example.yaml`
2. **Create Sleep Automations**: Auto-enable sleep mode at bedtime
3. **Set Up Scenes**: Create scenes that temporarily override
4. **Explore Modes**: Try different brightness/color temp modes

Need help? Check the full README.md for detailed documentation.
