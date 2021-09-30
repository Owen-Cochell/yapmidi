"""
This file contains builtin event handlers.

Here is a list of included handlers:

* Nullhandler - Simply does nothing
* PrintHandler - Prints the event to the console
* Raisehandler - Raises a custom exception when called 
"""

from ymidi.handlers.base import BaseHandler
from ymidi.events.base import BaseEvent


class NullHandler(BaseHandler):
    """
    BaseHandler - As per the name, simply does nothing!

    We do not process that event in any way,
    we simply 'pass' when called.
    """

    NAME = "NullHandler"

    async def handle(self, event: BaseEvent):
        """
        Simply do nothing.

        :param event: Event to handle
        :type event: BaseEvent
        """

        pass


class PrintHandler(BaseHandler):
    """
    PrintHandler - Prints the received events to the console.

    We use the print() method to go about this.
    Be warned, this module can seriously slow down yap-midi!
    It is recommended to use this handler for debug purposes only!
    """

    NAME = "PrintHandler"

    async def handle(self, event: BaseEvent):
        """
        Prints the event to the console.

        :param event: Event to print
        :type event: BaseEvent
        """

        # Print the event:

        print(event)


class RaiseHandler(BaseHandler):
    """
    RaiseHandler - Raises a custom exception when invoked.

    Users can define the exception to raise,
    as well as args and keyword args in the init method.
    """

    NAME = "RaiseHandler"

    def __init__(self, excep, *args, **kwargs):

        super().__init__("RaiseHandler")

        self.excep = excep  # Exception to raise
        self.args = args  # Args to pass to the exception
        self.kwargs = kwargs  # Keyword args to pass to the exception

    async def handle(self, event: BaseEvent):
        """
        Raises an exception when invoked.

        :param event: Event to handle
        :type event: BaseEvent
        """

        # Raise our exception:

        raise self.excep(*self.args, **self.kwargs)
