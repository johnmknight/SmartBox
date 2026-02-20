# code.py — SmartToolbox main entry point (CircuitPython)
# Install libs first: circup install adafruit_minimqtt adafruit_vcnl4020
#   adafruit_max1704x adafruit_st7789 adafruit_display_text adafruit_ntp neopixel

import time, board, wifi, socketpool, ssl
import settings, sensor, power, state_machine, display, mqtt_client
from modes import mode_toolbox, mode_clock, mode_weather, mode_battery
from modes.interrupts import red_alert, lockdown, self_destruct

print("\n=== SmartToolbox Firmware v1.0 ===")
settings.load()
print(f"Box: {settings.box_id()} | Rack: {settings.rack_id()}")

display.init()
sensor.init()
power.init()

def connect_wifi():
    ssid = settings.get("wifi_ssid")
    pwd  = settings.get("wifi_pass")
    if not ssid: return False
    try:
        print(f"[wifi] Connecting to {ssid}...")
        wifi.radio.connect(ssid, pwd)
        print(f"[wifi] Connected - IP: {wifi.radio.ipv4_address}")
        return True
    except Exception as e:
        print(f"[wifi] Failed: {e}"); return False

wifi_ok = connect_wifi()
pool    = socketpool.SocketPool(wifi.radio) if wifi_ok else None
ssl_ctx = ssl.create_default_context() if wifi_ok else None

if wifi_ok:
    mqtt_client.init(pool, ssl_ctx)
    mode_clock.sync_ntp(pool)

# MQTT handlers
def handle_command(topic, p):
    action = p.get("action")
    if action == "identify":
        display.set_pixel(0xFFFFFF, brightness=1.0); time.sleep(0.5); display.set_pixel(0x00FF80)
    elif action == "set_category":
        cat = p.get("category", "Unknown")
        mode_toolbox.set_category(cat)
        mqtt_client.publish_ack("set_category", {"category": cat})
    elif action == "set_mode":
        display.set_mode(p.get("mode", "TOOLBOX"))
    elif action == "reboot":
        import microcontroller; microcontroller.reset()

def handle_weather(topic, p):   mode_weather.update(p)

def handle_red_alert(topic, p):
    display.set_interrupt(display.INTERRUPT_RED_ALERT)
    mqtt_client.publish_ack("red-alert")

def handle_lockdown(topic, p):
    display.set_interrupt(display.INTERRUPT_LOCKDOWN)
    mqtt_client.publish_ack("lockdown")

def handle_self_destruct(topic, p):
    display.set_interrupt(display.INTERRUPT_SELF_DESTRUCT)
    self_destruct.start(p.get("countdown", 30))
    mqtt_client.publish_ack("self-destruct")

def handle_all_clear(topic, p):
    display.clear_interrupt()
    mqtt_client.publish_ack("all-clear")

mqtt_client.on_message(mqtt_client.TOPIC_COMMAND,       handle_command)
mqtt_client.on_message(mqtt_client.TOPIC_WEATHER,       handle_weather)
mqtt_client.on_message(mqtt_client.TOPIC_RED_ALERT,     handle_red_alert)
mqtt_client.on_message(mqtt_client.TOPIC_LOCKDOWN,      handle_lockdown)
mqtt_client.on_message(mqtt_client.TOPIC_SELF_DESTRUCT, handle_self_destruct)
mqtt_client.on_message(mqtt_client.TOPIC_ALL_CLEAR,     handle_all_clear)

# State machine
def on_state_change(new_state, prev_state):
    mqtt_client.publish_state(new_state, mode_toolbox.current_category())
    colors = {"DOCKED": 0x00FF80, "AWAY": 0xFF8C00, "SET_DOWN": 0xFFFF00}
    display.set_pixel(colors.get(new_state, 0xFFFFFF))

state_machine.on_change(on_state_change)
state_machine.init()

# Main loop
_last_battery = 0;  _BATTERY_INTERVAL = 60
_last_debug   = 0;  _DEBUG_INTERVAL   = 10
_last_render  = 0;  _RENDER_INTERVAL  = 0.5

print("[main] Entering main loop")

while True:
    now = time.monotonic()
    state_machine.poll()
    mqtt_client.poll()

    usb_event = power.poll_usb_change()
    if usb_event:
        mqtt_client.publish_debug({"event": f"usb_{usb_event}", **power.debug_payload()})

    for event in display.poll_buttons():
        display.handle_button(event)

    if now - _last_render >= _RENDER_INTERVAL:
        _last_render = now
        if display.is_interrupted():
            intr = display._current_interrupt
            if intr == display.INTERRUPT_RED_ALERT:    red_alert.render()
            elif intr == display.INTERRUPT_LOCKDOWN:   lockdown.render()
            elif intr == display.INTERRUPT_SELF_DESTRUCT:
                if self_destruct.render(): display.clear_interrupt()
        else:
            mode = display.current_mode()
            if mode == display.MODE_TOOLBOX:  mode_toolbox.render(state_machine.current())
            elif mode == display.MODE_CLOCK:  mode_clock.render()
            elif mode == display.MODE_WEATHER: mode_weather.render()
            elif mode == display.MODE_BATTERY: mode_battery.render()

    if now - _last_battery >= _BATTERY_INTERVAL:
        _last_battery = now
        mqtt_client.publish_battery(power.battery_percent(), power.battery_voltage(), power.is_charging())

    if settings.debug() and now - _last_debug >= _DEBUG_INTERVAL:
        _last_debug = now
        mqtt_client.publish_debug({
            **state_machine.debug_payload(), **sensor.debug_payload(), **power.debug_payload(),
            "wifi_rssi": wifi.radio.ap_info.rssi if wifi_ok else None,
            "mqtt_connected": mqtt_client.is_connected(),
            "mode": display.current_mode(),
        })

    time.sleep(0.05)
