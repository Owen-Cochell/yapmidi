"""
This file contains all MIDI Meta events.

Meta events are used in MIDI files to provide
metadata such as temp, track name, copyright info, ect.

TODO: Improve meta event descriptions!
"""

from ymidi.events.base import BaseMetaMesage, BaseEvent
from ymidi.constants import CHANNEL_PREFIX, COPYRIGHT, CUE_POINT, INSTRUMENT, KEY_SIGNATURE, LYRIC, MARKER, RESERVED, SEQUENCE_NUMBER, SMPTE_OFFSET, TEMPO_SET, TEXT, TIME_SIGNATURE, TRACK_END, TRACK_NAME


class SequenceNumber(BaseMetaMesage):
    """
    Event that specifies the number of a sequence.
    In a format 2 file, it can be used to represent
    a pattern so Cue messages can refer to the patterns.
    
    This event is optional and MUST occur at the beginning of a track,
    and before any non-zero delta-times and vanilla MIDI events.
    """
    
    name = "SequenceNumber"
    type = SEQUENCE_NUMBER
    length = 2


class MetaText(BaseMetaMesage):
    """
    Event that contains text that can describe anything.
    
    This event is optional, and can occur anywhere in the track,
    although it is recommended to put a text event at the beginning
    of a track, so the track can be properly named.
    """
    
    name = "Text"
    type = TEXT
    length = -1
    
    def __init__(self, *args) -> None:
        super().__init__(*args)
        
        self.text = bytes.decode(args, encoding='utf-8')  # Decode the bytes into a string


class CopyrightNotice(MetaText):
    """
    Contains a copyright notice as ASCII text.
    
    This notice should ideally contain the character C,
    copyright year, and owner of the copyright.
    These events should be the first event in the first track chunk at time 0,
    to ensure that this event is recorded and processed.
    """
    
    name = "CopyrightNotice"
    type = COPYRIGHT


class TrackName(MetaText):
    """
    Contains the name of the track/sequence.
    
    If present in a format 0 track,
    or the first track in a format 1 file,
    then this event contains the name of the sequence.
    Otherwise, it is the name of the track.
    """

    name = "TrackName"
    type = TRACK_NAME


class InstrumentName(MetaText):
    """
    Contains the name of the instrumentation to be used in the track.
    """

    name = "InstrumentName"
    type = INSTRUMENT


class Lyric(MetaText):
    """
    Contains a lyric to be sung.
    """
    
    name = "Lyric"
    type = LYRIC


class Marker(MetaText):
    """
    Name of a point in the sequence.
    
    Usually found in format 0 track,
    or first track in format 1 file.
    """
    
    name = "Marker"
    type = MARKER


class CuePoint(MetaText):
    """
    Description of something happening
    at this point in the sequence.
    """
    
    name = "CuePoint"
    type = CUE_POINT


class ChannelPrefix(BaseMetaMesage):
    """
    Associates a MIDI channel with all events that follow.
    
    This channel mapping is effective until the next normal MIDI event,
    or the next ChannelPrefix event.
    
    This allows multiple tracks to be present in one,
    which can be useful for MIDI format 0 files.
    """

    name = "ChannelPrefix"
    type = CHANNEL_PREFIX
    legnth = 1
    
    def __init__(self, num) -> None:
        super().__init__(num)
        
        self.num = num  # Channel number to map


class EndOfTrack(BaseMetaMesage):
    """
    Represents an end of track.
    
    This message is NOT optional,
    and must be present at the end of each track!
    """
    
    name = "EndOfTrack"
    type = TRACK_END


class SetTempo(BaseMetaMesage):
    """
    Changes the tempo to the provided value.
    
    This sets the tempo in microseconds per quarter note,
    using the provided value.
    """
    
    name = "SetTempo"
    type = TEMPO_SET
    legnth = 3

    def __init__(self, bt1, bt2, bt3) -> None:
        super().__init__(bt1, bt2, bt3)
        
        self.bt1 = bt1
        self.bt2 = bt2
        self.bt3 = bt3


class SMPTEOffset(BaseMetaMesage):
    """
    Designates where the SMPTE time is supposed to start
    for the given track.
    
    This event should be present at the start of the track
    in SMPTE format.
    """

    name = "SMPTEOffset"
    type = SMPTE_OFFSET
    legnth = 5

    def __init__(self, hr, mn, se, fr, ff) -> None:
        super().__init__(hr, mn, se, fr, ff)
        
        self.hr = hr
        self.mn = mn
        self.se = se
        self.fr = fr
        self.ff = ff


class TimeSignature(BaseMetaMesage):
    """
    Sets the time signature.
    
    The first value represents the numerator,
    and the second represents the denominator,
    which should be a negative power of two.
    
    The next value is the number of MIDI clocks per metronome click,
    and the final value expresses the number of notated 32nd notes
    in a quarter note(24 MIDI clocks).
    """

    name = "TimeSignature"
    type = TIME_SIGNATURE
    legnth = 4

    def __init__(self, numerator, denominator, cpm, npq) -> None:
        super().__init__(numerator, denominator, cpm, npq)
        
        self.numerator = numerator  # Numerator of the time signature
        self.denominator = denominator  # Denominator of time signature
        self.cpm = cpm  # MIDI clocks per metronome click
        self.npq = npq  # 32nd notes per quarter note


class KeySignature(BaseMetaMesage):
    """
    Sets the key signature.

    TODO: Document this better
    
    sf = -7: 7 flats
    sf = -1: 1 flat
    sf = 0: key of C
    sf = 1: 1 sharp
    sf = 7: 7 sharps
    mi = 0: major key
    mi = 1: minor key
    """

    name = "KeySignature"
    type = KEY_SIGNATURE
    legnth = 2
    
    def __init__(self, sf, mi) -> None:
        super().__init__(sf, mi)
        
        self.sf = sf
        self.mi = mi


class Reserved(BaseMetaMesage):
    """
    Special meta events for sequencers to implement.
    """

    name = "Reserved"
    type = RESERVED
    legnth = -1


# A tuple of ALL meta events:

META_EVENTS = (SequenceNumber, MetaText, CopyrightNotice, TrackName, InstrumentName,
               Lyric, Marker, CuePoint, ChannelPrefix, EndOfTrack, SetTempo, SMPTEOffset, 
               TimeSignature, KeySignature, Reserved)
