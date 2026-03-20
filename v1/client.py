# udp_client.py
"""
Simple UDP “chat client” that works from behind a NAT.
Run on a machine that does **not** have a public IP.
The client only needs to know the server’s public IP and port.

Usage:
    python udp_client.py  <server_ip> <server_port>
Example:
    python udp_client.py 203.0.113.42 9999
"""

import socket
import threading
import sys
from common import start_receiver, start_sender

def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)

    SERVER_IP   = sys.argv[1]
    SERVER_PORT = int(sys.argv[2])
    SERVER_ADDR = (SERVER_IP, SERVER_PORT)

    # --------------------------------------------------------------
    # 1️⃣  Create a UDP socket.  We **do not** bind it to a specific
    #    local port – the OS picks an available one (this is what the
    #    NAT uses for its “hole”).
    # --------------------------------------------------------------
    cli_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    cli_sock.settimeout(1.0)                 # for clean shutdown

    # --------------------------------------------------------------
    # 2️⃣  *Punch* the NAT hole: send a tiny “hello” packet to the server.
    #    The first packet from the client is what allocates a mapping
    #    inside the NAT, allowing the server’s replies to get back.
    # --------------------------------------------------------------
    try:
        cli_sock.sendto(b'HELLO\n', SERVER_ADDR)
        print(f"[CLIENT] Sent initial packet to {SERVER_ADDR}")
    except OSError as exc:
        print(f"[CLIENT] Unable to send initial packet: {exc}", file=sys.stderr)
        sys.exit(1)

    # --------------------------------------------------------------
    # 3️⃣  Start a background thread that prints any incoming lines.
    # --------------------------------------------------------------
    stop_event = threading.Event()
    recv_thread = threading.Thread(target=start_receiver,
                                   args=(cli_sock, stop_event),
                                   daemon=True)
    recv_thread.start()

    # --------------------------------------------------------------
    # 4️⃣  Main loop – read from stdin and forward to the server.
    # --------------------------------------------------------------
    try:
        start_sender(cli_sock, SERVER_ADDR)
    finally:
        # Clean‑up
        stop_event.set()
        cli_sock.close()
        recv_thread.join()
        print("\n[CLIENT] Bye!")

if __name__ == '__main__':
    main()
