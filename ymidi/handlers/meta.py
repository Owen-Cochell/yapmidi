"""
This file contains various builtin meta handlers.

These meta handler can be very useful for
filtering/altering events,
as well as changing the state of yap-midi
when certain events are received.
"""

import asyncio

from typing import Any, Union

from ymidi.handlers.base import MetaHandler
from ymidi.events.base import BaseEvent


class EventFilter(MetaHandler):
    """
    EventFilter - Filters MIDI events

    This meta handler allows events to be filtered.
    We will ALWAYS return None upon being handled,
    which will drop the events we are registered to.

    Use this class with caution!
    Be sure to not accidentally register this meta handler to an important event,
    unless this is your intention! 
    """

    NAME = "EventFilter"
    PRIORITY = 1
    
    def handle(self, event: BaseEvent) -> None:
        """
        As stated above, we simply return None to drop the event

        :param event: Event to filter
        :type event: BaseEvent
        :return: None
        :rtype: None
        """

        # Return None:

        return None


class AdvancedEventFilter(MetaHandler):
    """
    AdvancedEventFilter - Filters events with a twist!

    We are very similar to EventFilter.
    However, we have the added functionality of calling 
    external code to check if the event is valid.

    We use a checker function to determine if the event is valid.
    The checker function should return True for a valid event,
    and False for an invalid event.
    We will drop invalid events,
    and let valid events pass through unaltered.
    You can pass your checker function to the 'checker' parameter
    during instantiation.
    Any extra arguments will be passed along to the checker function.
    Your checker function should take at least one argument,
    which will be the event to check.
    THIS CHECKER FUNCTION MUST BE AN ASYNCIO COROUTENE!

    Because function calls can be somewhat expensive performance wise,
    we are separate from EventFilter,
    as some people want to always drop events regardless of their content or external factors.
    be sure that your checker function is fast enough for high speed processing!

    The same logic applies from EventFilter,
    be careful which events your register this handler under!
    We MIGHT drop events depending on the checker function,
    so make sure this won't drop important events!
    """

    NAME = "AdvancedEventFilter"
    PRIORITY = 1

    def __init__(self, checker: Any, *args, **kwargs) -> None:
        super().__init__()

        self.checker = checker  # Checker function
        self.args = args  # Args to pass to the checker function
        self.kwargs = kwargs  # Keyword args to pass to the checker function

    async def handle(self, event: BaseEvent) -> Union[BaseEvent, None]:
        """
        Checks the given event against our checker function.

        :param event: Event to check
        :type event: BaseEvent
        :return: Returns event if valid, None if not
        :rtype: Union[BaseEvent, None]
        """

        # Run our checker function:

        result = await self.checker(event, self.args, self.kwargs)

        # Check our result:

        if result:

            # Passed the check! Return the event:

            return event

        # Failed the check, return None:

        return None
