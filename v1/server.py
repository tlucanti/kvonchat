# udp_server.py
"""
Simple UDP “chat server” that works with a single client.
Run on a machine that is reachable from the Internet (public IP, or
router forwarding UDP port X to this host).

Usage:
    python udp_server.py  <listen_port>
Example:
    python udp_server.py 9999
"""

import socket
import threading
import sys
from common import start_receiver, start_sender

def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    LISTEN_PORT = int(sys.argv[1])

    # --------------------------------------------------------------
    # 1️⃣  Create a UDP socket bound to all local interfaces.
    # --------------------------------------------------------------
    srv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    srv_sock.bind(('', LISTEN_PORT))          # '' == INADDR_ANY
    srv_sock.settimeout(1.0)                  # make recvfrom non‑blocking

    print(f"[SERVER] Listening on UDP {srv_sock.getsockname()}")

    # --------------------------------------------------------------
    # 2️⃣  Wait for the first packet – that will be the NAT client
    #    announcing itself.  The client’s (public) address becomes the
    #    “chat peer”.
    # --------------------------------------------------------------
    print("[SERVER] Waiting for first packet from the client …")
    while True:
        try:
            data, client_addr = srv_sock.recvfrom(4096)
            print(f"[SERVER] Got first packet from {client_addr}")
            break
        except socket.timeout:
            continue
        except KeyboardInterrupt:
            print("\n[SERVER] Exiting")
            srv_sock.close()
            sys.exit(0)

    # --------------------------------------------------------------
    # 3️⃣  Start a background thread that prints everything we receive.
    # --------------------------------------------------------------
    stop_event = threading.Event()
    recv_thread = threading.Thread(target=start_receiver,
                                   args=(srv_sock, stop_event),
                                   daemon=True)
    recv_thread.start()

    # --------------------------------------------------------------
    # 4️⃣  Main loop – read from stdin and send to the client.
    # --------------------------------------------------------------
    try:
        start_sender(srv_sock, client_addr)
    finally:
        # Clean‑up
        stop_event.set()
        srv_sock.close()
        recv_thread.join()
        print("\n[SERVER] Bye!")

if __name__ == '__main__':
    main()
