# -*- coding: utf-8 -*-
from hyper.packages.hyperframe.frame import (
    Frame, DataFrame, RstStreamFrame, SettingsFrame,
    PushPromiseFrame, PingFrame, WindowUpdateFrame, HeadersFrame,
    ContinuationFrame, BlockedFrame, GoAwayFrame,
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

class TestHyperConnection(object):
    def test_receive_unexpected_stream_id(self):
        frames = []

        def data_callback(frame):
            frames.append(frame)

        c = HTTP20Connection('www.google.com')
        c._send_cb = data_callback

        f = DataFrame(-1)
        data = memoryview(b"hi there sir")
        c._consume_frame_payload(f, data)
        
        print("0--0")
        f = frames[0]
        assert len(frames) == 1
        assert f.stream_id == -1
        assert isinstance(f, RstStreamFrame)
        assert f.error_code == 1
        
        
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