# encoding: utf-8

"""An example raw IOLoop/IOStream example.

Taken from http://nichol.as/asynchronous-servers-in-python by Nicholas Piël.
"""

import errno
import functools
import socket

from marrow.util.compat import exception
from marrow.io import ioloop, iostream

log = __import__('logging').getLogger(__name__)
chunk = b"a" * 1024 * 1024


def connection_ready(sock, fd, events):
    while True:
        try:
            connection, address = sock.accept()
        
        except socket.error:
            exc = exception().exception
            if exc.args[0] not in (errno.EWOULDBLOCK, errno.EAGAIN):
                raise
            
            return
        
        connection.setblocking(0)
        stream = iostream.IOStream(connection)
        
        def write_chunk(stream, chunks_written=0):
            if chunks_written == 4:
                stream.close()
                return
            
            stream.write(chunk, functools.partial(write_chunk, stream, chunks_written+1))
        
        stream.write(b"HTTP/1.0 200 OK\r\nContent-Length: 4194304\r\n\r\n", functools.partial(write_chunk, stream))


if __name__ == '__main__':
    import logging
    
    logging.basicConfig(level=logging.DEBUG)
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setblocking(0)
    sock.bind(("", 8010))
    sock.listen(5000)
    
    io_loop = ioloop.IOLoop.instance()
    io_loop.set_blocking_log_threshold(2)
    callback = functools.partial(connection_ready, sock)
    io_loop.add_handler(sock.fileno(), callback, io_loop.READ)
    try:
        io_loop.start()
    except KeyboardInterrupt:
        io_loop.stop()
        log.info("exited cleanly")
