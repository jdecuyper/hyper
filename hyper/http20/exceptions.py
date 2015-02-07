# -*- coding: utf-8 -*-
"""
hyper/http20/exceptions
~~~~~~~~~~~~~~~~~~~~~~~

This defines exceptions used in the HTTP/2 portion of hyper.
"""
class HTTP20Error(Exception):
    """
    The base class for all of ``hyper``'s HTTP/2-related exceptions.
    """
    pass


class HPACKEncodingError(HTTP20Error):
    """
    An error has been encountered while performing HPACK encoding.
    """
    pass


class HPACKDecodingError(HTTP20Error):
    """
    An error has been encountered while performing HPACK decoding.
    """
    pass


class ConnectionError(HTTP20Error):
    """
    The remote party signalled an error affecting the entire HTTP/2
    connection, and the connection has been closed.
    """
    pass


class ProtocolError(HTTP20Error):
    """
    The remote party violated the HTTP/2 protocol.
    """
    pass


class ALPNFailureError(HTTP20Error):
    """
    The ALPN/NPN negotiation has returned a protocol that hyper doesn't
    support.
    """
    def __init__(self, actual_protocol, connection):
        super(ALPNFailureError, self).__init__()

        self.actual_protocol = actual_protocol
        self.connection = connection


# Create our own ConnectionResetError.
try:  # pragma: no cover
    ConnectionResetError = ConnectionResetError
except NameError:  # pragma: no cover
    class ConnectionResetError(Exception):
        """
        A HTTP/2 connection was unexpectedly reset.
        """
