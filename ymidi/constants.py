"""
This file contains various constants in use by yap-midi.
"""

MAX_INT_VALUE = 128

# -----------------------
#  MIDI Event Constants:
# -----------------------

NOTE_ON = b'0x90'
NOTE_OFF = b'0x80'
POLY_AFTERTOUCH = b'0xA0'
PROGRAM_CHANGE = b'0xC'
AFTER_TOUCH = b'0xD0'
PITCH_BEND = b'0xE0'
CONTROL_CHANGE = b'0xB0'
