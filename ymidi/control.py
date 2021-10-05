"""
This class contains components for representing
and working with MIDI controllers.
"""


class Controller:
    """
    Controller - Class for all controller actions!

    A MIDI Controller is a component that keeps track
    of certain parameters.
    These parameters are generally used for modifying tones
    with a controller other than a keyboard key.

    Controllers are numbered 0-119,
    which are mapped to a value 0-128.
    The controller numbers are defined by the MIDI specifications,
    and usuers will probably use yap-midi constants to access them.

    Some controllers have an LSB,
    meaning that they are mapped to other controllers
    that act as an least significant byte to increase the resolution
    from 128 steps to 16,384 steps.
    The controllers used as LSB are usually 32-63,
    and correspond to 0-31 respectively.
    Users can change this mapping, 
    and even map multiple controllers,
    allowing for an extremely high resolution!
    TODO: Add example here

    We have no understanding of controller mappings!
    Users should rely on some high-level tool or contants
    to find meaning in controller numbers.

    Usually, each channel has their own controllers to work with,
    meaning that this class will probably be used multiple times
    in high-level components.

    We offer tools to resolve hex values to simple python ints,
    as well as converting controllers into their high-resolution counterparts.
    """

    def __init__(self) -> None:
        
        self._control = []  # List contaning controller numbers