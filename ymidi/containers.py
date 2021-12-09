"""
Components that house MIDI events.    
"""


class Track(list):
    """
    A track of MIDI events.
    
    We offer some useful helper methods that make
    altering and adding MIDI events a relatively painless affair.

    We inherit the default python list,
    so we support all list operations.
    """
    
    def __init__(self, *args):
        
        super().__init__(*args)

        self.name = ''  # Name of the track