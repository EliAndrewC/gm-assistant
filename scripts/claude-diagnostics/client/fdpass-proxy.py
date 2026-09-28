#!/usr/bin/env python3
"""ssh ProxyCommand for host-diag: connect to the host's diagnostics Unix socket and hand ssh
the connected descriptor (ProxyUseFdpass=yes), so no bytes are copied through this process and
nothing extra (socat, nc) needs installing in the container.
"""

import socket
import sys

conn = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
conn.connect(sys.argv[1])
socket.send_fds(socket.socket(fileno=1), [b"\0"], [conn.fileno()])
