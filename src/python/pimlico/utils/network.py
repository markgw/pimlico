import socket


def get_unused_local_port():
    """
    Find a local port that's not currently being used, which we'll be able to bind a service to once this
    function returns.

    """
    return get_unused_local_ports(1)[0]


def get_unused_local_ports(n):
    """
    Find a number of local ports not currently in use. Binds each port found before looking for the next one.
    If you just called get_unused_local_port() multiple times, you'd get to same answer coming back.

    """
    sockets = []
    try:
        for i in range(n):
            # Bind a new socket
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(('localhost', 0))
            sockets.append(s)

        # Get the port numbers used by each socket
        ports = [s.getsockname()[1] for s in sockets]
    finally:
        # Close all opened sockets
        for s in sockets:
            s.close()
    return ports
