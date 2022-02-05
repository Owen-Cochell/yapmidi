"""
A set of components and tools to test yap-midi components.    
"""

from ymidi.decoder import ModularDecoder
from ymidi.events.voice import NoteEvent
from ymidi.events.system.system_exc import SystemExclusive


def midi_stream():
    # Test MIDI stream decoding:

    """
    This example byte stream is super weird,
    and is actually not valid MIDI data!
    Still, it is good to be able to handle stream interrupts,
    incase some synths implement this feature.
    """

    stream = [0x90,60,0xF8,0xF0,1,2,0xF8,3,4,5,0xF7,64,60,0x80,30,0xF8,0x90,55,55,30,64,78,23,0xF8]

    # Time, Time, SystemExclusive(1,2,3,4,5), On(60,64), Time, On(55,55), Off(30,30), On(60,64), On(78,23), Time 
    decoder = ModularDecoder()
    decoder.load_default()
    final = []

    print(decoder.collection)

    # Decode the data:

    for bts in stream:

        print("Decoding value: {}".format(bts))
        value = decoder.seq_decode(bts)
        print("Response: {}".format(value))

        if value is not None:

            final.append(value)
            
            if isinstance(value, NoteEvent):
                
                print("Pitch: {} ; Velocity: {}".format(value.pitch, value.velocity))

            if isinstance(value, SystemExclusive):
                
                print("SystemExc values: {}".format(value.data))


def variable_decode():
    
    # Test variable length decoding:
    
    stream = [0xF0, 1, 2, 3, 4, 5, 0xF7]
    
    decoder = ModularDecoder()
    decoder.load_default()
    final = []
    
    for bts in stream:
        
        print("Decoding value: {}".format(bts))
        value = decoder.seq_decode(bts)
        print("Response: {}".format(value))
        
        if value is not None:
            
            final.append(value)
            
        if isinstance(value, SystemExclusive):
            
            print("Data: {}".format(value.data))


midi_stream()
