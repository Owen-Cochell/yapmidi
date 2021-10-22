"""
This file contains various constants in use by yap-midi.
"""

MAX_INT_VALUE = 128

# -----------------------
#  MIDI Event Constants:
# -----------------------

# --== Channel Messages: ==--

NOTE_ON = 0x90
NOTE_OFF = 0x80
POLY_AFTERTOUCH = 0xA0
PROGRAM_CHANGE = 0xC0
AFTER_TOUCH = 0xD0
PITCH_BEND = 0xE0
CONTROL_CHANGE = 0xB0

# Tuple of channel messages:

CHANNELS = (NOTE_ON, NOTE_OFF, POLY_AFTERTOUCH, PROGRAM_CHANGE, AFTER_TOUCH, PITCH_BEND, CONTROL_CHANGE)
