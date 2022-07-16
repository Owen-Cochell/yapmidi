"""
This file contains various errors and exceptions in use by yap-midi    
"""


class YMidiBaseException(BaseException):
    """
    BaseException - Class all exceptions should inherit.

    This class does nothing on it's own,
    but is instead used to identify yap-midi exceptions.
    """

    pass


class StopPlayback(YMidiBaseException):
    """
    Exception raised when playback is over,
    but more events are requested.
    """

    pass


class ModuleCollectionException(YMidiBaseException):
    """
    Parent class for ModuleCollection errors.

    IOModuleErrors are raised when a module component fails,
    such as load, start, stop, unload.
    These classes also contain the exception encountered,
    so it can be worked with and handled.
    """

    def __init__(self, message, exception) -> None:
        super().__init__(message)

        self.exception = exception  # Exception object originally raised


class ModuleLoadException(ModuleCollectionException):
    """
    Exception called when the load() method of a module fails.

    Loading modules with a failing load() method is highly discouraged.
    If this exception is encountered,
    then it can safely be assumed that the module in question has NOT been loaded.

    We also keep a copy of the exception encountered,
    stored under the 'exception' parameter.
    """

    pass


class ModuleStartException(ModuleCollectionException):
    """
    Exception called when the start() method of a module fails.

    Using modules with a failing start() method is highly discouraged.
    If this exception is encountered,
    then the module in question will be removed WITHOUT calling the stop() or unload() method.

    We also keep a copy of the exception encountered,
    stored under the 'exception' parameter.
    """

    pass


class ModuleStopException(ModuleCollectionException):
    """
    Exception called when the stop() method of a module fails.

    Using modules with a failing stop() method is highly discouraged.
    If this exception is encountered,
    then the module in question will be removed WITHOUT calling the unload() method.

    We also keep a copy of the exception encountered,
    stored under the 'exception' parameter.
    """

    pass


class ModuleUnloadException(ModuleCollectionException):
    """
    Exception called when the unload() method of a module fails.

    using modules with a failing unload() method is highly discouraged.
    If this exception is encountered,
    then the module in question will continue to be unloaded.
    It is not recommended to load the module again for future use!

    We also keep a copy of the exception encountered,
    stored under the 'exception' parameter.
    """

    pass
