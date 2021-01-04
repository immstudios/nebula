"""Representation of an OSC message in a pythonesque way."""

__all__ = ["OSCMessage"]


from .osc_types import *

from typing import List, Iterator, Any


class OSCMessage(object):
    """Representation of a parsed datagram representing an OSC message.

    An OSC message consists of an OSC Address Pattern followed by an OSC
    Type Tag String followed by zero or more OSC Arguments.
    """

    def __init__(self, dgram: bytes) -> None:
        self._dgram = dgram
        self._parameters = []
        self._parse_datagram()

    def _parse_datagram(self) -> None:
        try:
            self._address_regexp, index = get_string(self._dgram, 0)
            if not self._dgram[index:]:
                # No params is legit, just return now.
                return

            # Get the parameters types.
            type_tag, index = get_string(self._dgram, index)
            if type_tag.startswith(','):
                type_tag = type_tag[1:]

            params = []
            param_stack = [params]
            # Parse each parameter given its type.
            for param in type_tag:
                if param == "i":  # Integer.
                    val, index = get_int(self._dgram, index)
                elif param == "h":  # Integer.
                    val, index = get_int(self._dgram, index)
                elif param == "f":  # Float.
                    val, index = get_float(self._dgram, index)
                elif param == "d":  # Double.
                    val, index = get_double(self._dgram, index)
                elif param == "s":  # String.
                    val, index = get_string(self._dgram, index)
                elif param == "b":  # Blob.
                    val, index = get_blob(self._dgram, index)
                elif param == "r":  # RGBA.
                    val, index = get_rgba(self._dgram, index)
                elif param == "m":  # MIDI.
                    val, index = get_midi(self._dgram, index)
                elif param == "t":  # osc time tag:
                    val, index = get_timetag(self._dgram, index)
                elif param == "T":  # True.
                    val = True
                elif param == "F":  # False.
                    val = False
                elif param == "[":  # Array start.
                    array = []
                    param_stack[-1].append(array)
                    param_stack.append(array)
                elif param == "]":  # Array stop.
                    if len(param_stack) < 2:
                        raise ParseError('Unexpected closing bracket in type tag: {0}'.format(type_tag))
                    param_stack.pop()
                # TODO: Support more exotic types as described in the specification.
                else:
                    logging.warning('Unhandled parameter type: {0}'.format(param))
                    continue
                if param not in "[]":
                    param_stack[-1].append(val)
            if len(param_stack) != 1:
                raise ParseError('Missing closing bracket in type tag: {0}'.format(type_tag))
            self._parameters = params
        except OSCParseError as pe:
            raise ParseError('Found incorrect datagram, ignoring it', pe)

    @property
    def address(self) -> str:
        """Returns the OSC address regular expression."""
        return self._address_regexp

    @staticmethod
    def dgram_is_message(dgram: bytes) -> bool:
        """Returns whether this datagram starts as an OSC message."""
        return dgram.startswith(b'/')

    @property
    def size(self) -> int:
        """Returns the length of the datagram for this message."""
        return len(self._dgram)

    @property
    def dgram(self) -> bytes:
        """Returns the datagram from which this message was built."""
        return self._dgram

    @property
    def params(self) -> List[Any]:
        """Convenience method for list(self) to get the list of parameters."""
        return list(self)

    def __iter__(self) -> Iterator[float]:
        """Returns an iterator over the parameters of this message."""
        return iter(self._parameters)
