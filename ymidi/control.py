"""
This class contains components for representing
and working with MIDI controllers.
"""

from collections import UserList
from types import MappingProxyType

from ymidi.constants import MAX_INT_VALUE


class Controller(list):
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

    Our low-level structure looks something like this:

    [
        [
            val, [mapped_in,...], [mapped_out,...]
        ],...
    ]

    Where:

    * val - Raw value of the controller
    * mapped_in - Controllers mapped to us
    * mapped_out - Controllers we are mapped to

    Users should NOT attempt to access or alter this structure in any way!
    I mean, their really is nothing stopping you,
    but you shouldn't if you can help it!
    You should use the high-level methods for accessing controllers.

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

    def __init__(self, num=120):
        
        super(list).__init__()

        self._control = []  # List contaning controller values and LSB mappings
        self.num = num  # Number of controllers

        self.reset()

    def reset(self):
        """
        Initializes the controller.

        It configures the internal controller structure
        and prepares this object for operation.
        This zeros out the controllers as well.

        Users can use this method to reset the controllers
        back to a stable state.
        """

        # CLear out the controller list:

        self.clear()
        self._control.clear()

        # Setup the structure:

        for num in range(0, self.num):

            self.append(0)
            self._control.append([0, [], []])

    def set_controller(self, num: int, val: int, reset=True):
        """
        Sets the controller at the given number with the given value.

        We automatically determine the 'true' value of the controller
        by traversing the mapping controllers.
        This is done upon each call of this method,
        allowing resources to fetch the number quickly.

        This function can be called manually,
        but it is usually called using list dunder methods.

        We can optionally disable LSB resets.
        When the master controller is altered,
        all mapped controllers MUST be set to zero.
        Disabling this is necessary for some operations,
        and it can optionally be disabled by the user.

        :param num: Controller number to alter
        :type num: int
        :param val: Value to set the controller to
        :type val: int
        :param reset: Value determining if we should reset all sub-controllers
        :param reset: bool
        """

        # Set the low-level value:

        self._control[num][0] = val

        # Should we clear our low-level controllers:

        if reset:

            # Clear all sub-controllers:

            for sub in self._control[num][1]:

                # Set their value to zero:

                super().__setitem__(sub, 0)
                self._control[sub][0] = 0

        # Re-compute our value:

        self._compute_mapped(num)

        # We should also compute the value we are attached to:

        for map in self._control[num][2]:

            # Call the compute_mapped method:

            self._compute_mapped(map)
 
    def map_controller(self, master: int, map: int, no_parse: bool=False):
        """
        Maps the given controller to another.
        
        This allows controllers to act as the LSB
        to one(or multiple) controllers.
        This allows for the resolution of the mapped
        controller to increase beyond the default 128
        bytes of resolution.

        The 'master' parameter is the controller to be altered,
        and 'map' is the controller to be mapped.
        After this operation, 'map' will be mapped to 'cont'.
        You can map multiple controllers in this manner,
        and the order of resolution is determined by the 
        order of mapped controllers.
        
        For example, the first controller will be LSB 1,
        the second will be LSB 2.
        The algorithm used to determine the final value 
        of the controller is as follows:

        master_val * num_mapped * MAX_INT + ... cont_val(n) * num * MAX_INT

        TODO: Fix equation

        Where:

        * master_val - Value of the master controller
        * num_mapped - Number of controllers mapped to the master
        * MAX_INT - Max MIDI int, usually 128
        * cont_val(n) - Value of nth controller in the chain
        * num - Number of nth controller in the chain

        The least significant controller has the lowest value, 0,
        while the most significant controller, the master,
        has the highest value, n. 

        By default, we parse over the mappings of the 
        mapped controller and attribute them to the master controller.
        This is usually the intention,
        as mapped controllers usually want their mapped
        controllers to be mapped to the master.
        If this is undesirable,
        then you can pass 'no_parse=True' to this method
        and we will NOT parse mappings.

        :param master: Number of the Master controller
        :type cont: int
        :param map: Number of the controller to be mapped to the master
        :type map: int
        :param no_parse: Value determining if we should map sub-controllers to thew master
        :type no_parse: bool
        """

        # Add the controller to the master map list:

        self._control[master][1].insert(0, map)

        # Add the master to the mapped controller:

        self._control[map][2].append(master)

        # Check if we should parse over sub-controllers:

        if not no_parse:

            # Parse over sub-controllers and register them:

            for sub in self._control[map][1]:

                # Map the controller:

                self.map_controller(master, sub)

    def demap_controller(self, master: int, map: int):
        """
        De-maps a given controller from the master controller.

        This will remove the mappings from both the master
        and mapped controllers.
        If the given controller is NOT mapped to the master,
        then a ValueError will be raised.

        :param master: Number of the master controller to alter mappings
        :type master: int
        :param map: Number of controller to remove from master
        :type map: int
        :raises: ValueError: If given controller is not mapped to the master controller
        """

        # Check to see if controller is present:

        if map in self._control[master][1]:

            # Remove the controller:

            self._control[master][1].remove(map)

            # Remove the mapping from the mapped controller:

            self._control[map][2].remove(master)
    
            return

        # Otherwise, raise an error:

        raise ValueError("Sub-controller not present in master!")

    def clear_mappings(self, master: int):
        """
        Clears all mappings from the given controller.

        This will iterate over each sub-controller 
        and remove them.

        :param master: Number of the master controller
        :type master: int
        """

        # Iterate over all mappings:

        for cont in self._control[master][1]:

            # Remove the mapping:

            self.demap_controller(master, cont)

    def _compute_mapped(self, master: int):
        """
        Compute the final mapped value of the given master controller.

        We iterate over it's sub-controllers,
        and compute it's final mapped value.

        There is really no need for end users to call
        this method,
        as it is called automatically where appropriate.

        :param master: Master controller
        :type master: int
        """

        # Compute the high-level value in accordance with mappings:

        val = self._control[master][0]

        if self._control[master][1]:

            print("Computing sub-values")

            val = 0

            # Compute the first value:

            #val += self._control[self._control[master][1][0]][0]

            print("Value after first: {}".format(val))

            for index, map in enumerate(self._control[master][1]):

                # Calculate the value:

                val += self._control[map][0] * (MAX_INT_VALUE ** index)

                print("New value{}: {}".format(map, val))

            # Calculate the final value:

            val += self._control[master][0] * (MAX_INT_VALUE ** (len(self._control[master][1])))

            print("Raw value: {}".format(self._control[master][0]))
            print("Final val: {}".format(val))

        # Finally, set the value:

        super().__setitem__(master, val)

    def __setitem__(self, num: int, val: int):
        """
        Emulates a list-like object.

        We simply call set_controller() under the hood.

        :param num: Controller number to alter
        :type num: int
        :param val: Value to set the controller to
        :type val: int
        """

        self.set_controller(num, val)
