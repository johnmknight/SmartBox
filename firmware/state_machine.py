# state_machine.py
# Box physical state from proximity + USB signals.
#
# States:
#   DOCKED    - on surface + USB connected (in rack, charging)
#   SET_DOWN  - on surface + no USB (placed somewhere else)
#   AWAY      - not on surface + no USB (being carried)
#   DOCKING   - not on surface + USB (transitional)

import time
import sensor
import power

DOCKED   = "DOCKED"
SET_DOWN = "SET_DOWN"
AWAY     = "AWAY"
DOCKING  = "DOCKING"

_current_state   = AWAY
_previous_state  = None
_state_since     = 0
_on_change_callbacks = []
# Settle times per target state.
# DOCKING is transitional — resolve quickly so the brief USB-before-surface moment
# is captured (or skipped cleanly if the box lands within the window).
# All other states use 2.0s to debounce vibration / momentary sensor noise.
_SETTLE_TIMES = {
    DOCKED:   2.0,
    AWAY:     2.0,
    SET_DOWN: 2.0,
    DOCKING:  0.5,   # transitional — settle fast
}
_pending_state   = None
_pending_since   = 0

def init():
    global _current_state, _state_since
    _state_since = time.monotonic()
    _current_state = _evaluate()
    print(f"[state] Initial state: {_current_state}")

def on_change(callback):
    _on_change_callbacks.append(callback)

def poll():
    global _current_state, _previous_state, _state_since
    global _pending_state, _pending_since
    evaluated = _evaluate()
    if evaluated == _current_state:
        _pending_state = None
        return _current_state
    now = time.monotonic()
    if evaluated != _pending_state:
        _pending_state = evaluated
        _pending_since = now
        return _current_state
    if now - _pending_since >= _SETTLE_TIMES.get(_pending_state, 2.0):
        _previous_state = _current_state
        _current_state  = _pending_state
        _state_since    = now
        _pending_state  = None
        print(f"[state] {_previous_state}  {_current_state}")
        for cb in _on_change_callbacks:
            try:
                cb(_current_state, _previous_state)
            except Exception as e:
                print(f"[state] Callback error: {e}")
    return _current_state

def current():
    return _current_state

def time_in_state():
    return time.monotonic() - _state_since

def _evaluate():
    on_surface = sensor.is_on_surface()
    usb = power.usb_connected()
    if on_surface and usb:     return DOCKED
    if on_surface and not usb: return SET_DOWN
    if not on_surface and usb: return DOCKING
    return AWAY

def debug_payload():
    return {
        "state": _current_state,
        "previous_state": _previous_state,
        "time_in_state": round(time_in_state(), 1),
        "on_surface": sensor.is_on_surface(),
        "usb_connected": power.usb_connected(),
    }
