import evdev
from evdev import ecodes, InputDevice, UInput, list_devices
import sys
import select

# Target device names
KEYBOARD_NAME = "AT Translated Set 2 keyboard"
TRACKPOINT_NAME = "TPPS/2 Elan TrackPoint"

# Find devices
keyboard_path = None
trackpoint_path = None

for path in list_devices():
    try:
        dev = InputDevice(path)
        if dev.name == KEYBOARD_NAME:
            keyboard_path = path
        elif dev.name == TRACKPOINT_NAME:
            trackpoint_path = path
    except Exception:
        continue

if not keyboard_path or not trackpoint_path:
    print(f"Error: Could not find both devices.\nKeyboard: {keyboard_path}\nTrackpoint: {trackpoint_path}", file=sys.stderr)
    sys.exit(1)

print(f"Found Keyboard at: {keyboard_path}")
print(f"Found Trackpoint at: {trackpoint_path}")

keyboard = InputDevice(keyboard_path)
trackpoint = InputDevice(trackpoint_path)

# Create virtual keyboard (always grabbed to manage Caps Lock and mapping keys)
virtual_keyboard = UInput.from_device(keyboard, name="Virtual Scroll Keyboard")

# Create virtual mouse (handles cursor movement, smooth scrolling, and mouse buttons)
mouse_caps = {
    ecodes.EV_REL: [ecodes.REL_X, ecodes.REL_Y, ecodes.REL_WHEEL, ecodes.REL_HWHEEL, ecodes.REL_WHEEL_HI_RES, ecodes.REL_HWHEEL_HI_RES],
    ecodes.EV_KEY: [ecodes.BTN_LEFT, ecodes.BTN_RIGHT, ecodes.BTN_MIDDLE]
}
virtual_mouse = UInput(mouse_caps, name="Virtual Scroll Mouse")

# Grab physical keyboard and trackpoint permanently
keyboard.grab()
trackpoint.grab()

# State variables
caps_pressed = False
caps_used = False
d_pressed = False

# High-resolution scroll accumulation (120 units = 1 legacy scroll notch)
accumulated_hi_res_x = 0
accumulated_hi_res_y = 0

# Mapping for HJKL to arrows
NAV_MAP = {
    ecodes.KEY_H: ecodes.KEY_LEFT,
    ecodes.KEY_J: ecodes.KEY_DOWN,
    ecodes.KEY_K: ecodes.KEY_UP,
    ecodes.KEY_L: ecodes.KEY_RIGHT
}

def handle_keyboard_event(event):
    global caps_pressed, caps_used, d_pressed, accumulated_hi_res_x, accumulated_hi_res_y
    if event.type == ecodes.EV_KEY:
        # 1. Handle Caps Lock navigation / modifier
        if event.code == ecodes.KEY_CAPSLOCK:
            if event.value == 1:  # Down
                caps_pressed = True
                caps_used = False
            elif event.value == 0:  # Up
                caps_pressed = False
                d_pressed = False
                if not caps_used:
                    virtual_keyboard.write(ecodes.EV_KEY, ecodes.KEY_ESC, 1)
                    virtual_keyboard.write(ecodes.EV_KEY, ecodes.KEY_ESC, 0)
                    virtual_keyboard.syn()
            return

        # If Caps Lock is currently held down
        if caps_pressed:
            # D = Trackpoint scroll modifier
            if event.code == ecodes.KEY_D:
                caps_used = True
                if event.value == 1:  # Down
                    d_pressed = True
                    accumulated_hi_res_x = 0
                    accumulated_hi_res_y = 0
                elif event.value == 0:  # Up
                    d_pressed = False
                return

            # S = Right Mouse Click
            if event.code == ecodes.KEY_S:
                caps_used = True
                virtual_mouse.write(ecodes.EV_KEY, ecodes.BTN_RIGHT, event.value)
                virtual_mouse.syn()
                return

            # F = Left Mouse Click
            if event.code == ecodes.KEY_F:
                caps_used = True
                virtual_mouse.write(ecodes.EV_KEY, ecodes.BTN_LEFT, event.value)
                virtual_mouse.syn()
                return

            # Normal HJKL to Arrow keys
            if event.code in NAV_MAP:
                mapped_code = NAV_MAP[event.code]
                virtual_keyboard.write(ecodes.EV_KEY, mapped_code, event.value)
                caps_used = True
                return

    # Forward other events exactly as they are (including EV_SYN, EV_MSC, etc.)
    virtual_keyboard.write_event(event)

def handle_trackpoint_event(event):
    global caps_pressed, d_pressed, accumulated_hi_res_x, accumulated_hi_res_y
    # 1. Scroll Emulation Mode (Caps Lock + D is held)
    if caps_pressed and d_pressed:
        if event.type == ecodes.EV_REL:
            # Speed multiplier (adjust this to change scroll sensitivity)
            HI_RES_MULTIPLIER = 14
            
            if event.code == ecodes.REL_Y:
                # Invert Y axis for natural scroll direction
                delta_y = -event.value * HI_RES_MULTIPLIER
                accumulated_hi_res_y += delta_y
                
                # Send high-resolution scroll event (for smooth scrolling)
                virtual_mouse.write(ecodes.EV_REL, ecodes.REL_WHEEL_HI_RES, delta_y)
                
                # Accumulate and send standard wheel events (for legacy app compatibility)
                if abs(accumulated_hi_res_y) >= 120:
                    legacy_ticks = int(accumulated_hi_res_y / 120)
                    virtual_mouse.write(ecodes.EV_REL, ecodes.REL_WHEEL, legacy_ticks)
                    accumulated_hi_res_y -= legacy_ticks * 120
                
                virtual_mouse.syn()
                
            elif event.code == ecodes.REL_X:
                delta_x = event.value * HI_RES_MULTIPLIER
                accumulated_hi_res_x += delta_x
                
                # Send high-resolution horizontal scroll event
                virtual_mouse.write(ecodes.EV_REL, ecodes.REL_HWHEEL_HI_RES, delta_x)
                
                # Accumulate and send standard horizontal wheel events
                if abs(accumulated_hi_res_x) >= 120:
                    legacy_ticks = int(accumulated_hi_res_x / 120)
                    virtual_mouse.write(ecodes.EV_REL, ecodes.REL_HWHEEL, legacy_ticks)
                    accumulated_hi_res_x -= legacy_ticks * 120
                
                virtual_mouse.syn()

    # 2. Normal Pointer Movement (Sends movement, ignores physical Trackpoint buttons)
    else:
        if event.type == ecodes.EV_REL:
            if event.code in (ecodes.REL_X, ecodes.REL_Y):
                virtual_mouse.write_event(event)
        elif event.type == ecodes.EV_SYN:
            virtual_mouse.write_event(event)

def main():
    try:
        while True:
            # Wait for data on either device
            r, _, _ = select.select([keyboard.fd, trackpoint.fd], [], [])
            for fd in r:
                if fd == keyboard.fd:
                    for event in keyboard.read():
                        handle_keyboard_event(event)
                elif fd == trackpoint.fd:
                    for event in trackpoint.read():
                        handle_trackpoint_event(event)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            keyboard.ungrab()
        except Exception:
            pass
        try:
            trackpoint.ungrab()
        except Exception:
            pass

if __name__ == "__main__":
    main()
