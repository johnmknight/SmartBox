import board, time
from digitalio import DigitalInOut, Direction, Pull

# D0: Pull.UP, fires when value is False (active LOW)
# D1: Pull.DOWN, fires when value is True (active HIGH)
# D2: Pull.DOWN, fires when value is True (active HIGH)
d0 = DigitalInOut(board.D0); d0.switch_to_input(pull=Pull.UP)
d1 = DigitalInOut(board.D1); d1.switch_to_input(pull=Pull.DOWN)
d2 = DigitalInOut(board.D2); d2.switch_to_input(pull=Pull.DOWN)

last = [True, False, False]
print("Ready")

while True:
    vals = [not d0.value, d1.value, d2.value]
    for i, (name, v, lv) in enumerate(zip(["D0","D1","D2"], vals, last)):
        if v and not lv:
            print(f"PRESSED: {name}")
    last = vals
    time.sleep(0.05)
