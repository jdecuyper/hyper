# -*- coding: utf-8 -*-
from hyper.packages.hyperframe.frame import (
    Frame, DataFrame, RstStreamFrame, SettingsFrame,
    PushPromiseFrame, PingFrame, WindowUpdateFrame, HeadersFrame,
    ContinuationFrame, BlockedFrame, GoAwayFrame, FRAME_MAX_LEN
)
from hyper.packages.hpack.hpack_compat import Encoder, Decoder
from hyper.http20.connection import HTTP20Connection
from hyper.http20.stream import (
    Stream, STATE_HALF_CLOSED_LOCAL, STATE_OPEN, MAX_CHUNK, STATE_CLOSED
)
from hyper.http20.response import HTTP20Response, HTTP20Push
from hyper.http20.exceptions import (
    HPACKDecodingError, HPACKEncodingError, ProtocolError, ConnectionError,
)
from hyper.http20.window import FlowControlManager
from hyper.http20.util import (
    combine_repeated_headers, split_repeated_headers, h2_safe_headers
)
from hyper.common.headers import HTTPHeaderMap
from hyper.compat import zlib_compressobj
from hyper.contrib import HTTP20Adapter
import hyper.http20.errors as errors
import errno
import os
import pytest
import socket
import zlib
from io import BytesIO


def decode_frame(frame_data):
    f, length = Frame.parse_frame_header(frame_data[:9])
    f.parse_body(memoryview(frame_data[9:9 + length]))
    assert 9 + length == len(frame_data)
    return f


class TestHyperConnection(object):
    
     # A rst frame is sent in case the frame size is too long
     # when sending a reset frame, also check that stream was removed from the map
     # Should we have a  test for _update_settings?
     def test_connection_sends_rst_frame_if_frame_size_too_large(self):
        sock = DummySocket()
        d = DataFrame(1)
        d.data = b'hi there sir'
        sock.buffer = BytesIO(d.serialize())
        
        def send_rst_frame(stream_id, error_code):
            assert stream_id == 1
            assert error_code == 6

        c = HTTP20Connection('www.google.com')
        # Lower the maximum frame size settings in order to force the 
        # connection to send a reset frame with error code: FRAME_SIZE_ERROR
        c._settings[SettingsFrame.SETTINGS_MAX_FRAME_SIZE] = 10
        c._sock = sock
        c._send_rst_frame = send_rst_frame
        c.request('GET', '/')
        
        # Read the frame.
        c._recv_cb()
        
     def test_connection_stream_is_remove_on_frame_size_error(self):
        sock = DummySocket()
        d = DataFrame(1)
        d.data = b'hi there sir'
        sock.buffer = BytesIO(d.serialize())

        c = HTTP20Connection('www.google.com')
        # Lower the maximum frame size settings in order to force the 
        # connection to send a reset frame with error code: FRAME_SIZE_ERROR
        c._settings[SettingsFrame.SETTINGS_MAX_FRAME_SIZE] = 10
        c._sock = sock
        c.request('GET', '/')

        assert len(c.streams) == 1
        # Read the frame.
        c._recv_cb()        
        assert len(c.streams) == 0
    
# Some utility classes for the tests.
class NullEncoder(object):
    @staticmethod
    def encode(headers):
        return '\n'.join("%s%s" % (name, val) for name, val in headers)

class FixedDecoder(object):
    def __init__(self, result):
        self.result = result

    def decode(self, headers):
        return self.result

class DummySocket(object):
    def __init__(self):
        self.queue = []
        self.buffer = BytesIO()
        self.can_read = False

    def send(self, data):
        self.queue.append(data)

    def recv(self, l):
        return memoryview(self.buffer.read(l))

    def close(self):
        pass


class DummyFitfullySocket(DummySocket):
    def recv(self, l):
        length = l
        if l != 9 and l >= 4:
            length = int(round(l / 2))
        return memoryview(self.buffer.read(length))


class DummyStream(object):
    def __init__(self, data, trailers=None):
        self.data = data
        self.data_frames = []
        self.closed = False
        self.response_headers = {}
        self._remote_closed = False
        self.trailers = trailers

        if self.trailers is None:
            self.trailers = []

    def _read(self, *args, **kwargs):
        try:
            read_len = min(args[0], len(self.data))
        except IndexError:
            read_len = len(self.data)

        d = self.data[:read_len]
        self.data = self.data[read_len:]

        if not self.data:
            self._remote_closed = True

        return d

    def _read_one_frame(self):
        try:
            return self.data_frames.pop(0)
        except IndexError:
            return None

    def close(self):
        if not self.closed:
            self.closed = True
        else:
            assert False

    def gettrailers(self):
        return self.trailers
