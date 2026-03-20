# rendezvous.py
"""
Simple UDP rendez‑vous server.

Usage:
    python rendezvous.py <listen_port>
Example:
    python rendezvous.py 9999
"""

import socket, sys, threading, time
from common import receiver, sender

# ----------------------------------------------------------------------
# Data structures (in‑memory, single‑session only – good enough for demo)
# ----------------------------------------------------------------------
peers = {}          # maps client-id (0 or 1) -> (public_ip, public_port)

def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    LISTEN_PORT = int(sys.argv[1])
    srv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    srv.bind(('', LISTEN_PORT))
    srv.settimeout(0.5)

    print(f"[SERVER] Listening on UDP {srv.getsockname()}")

    # ------------------------------------------------------------------
    # 1️⃣  Wait for the *first* two distinct clients to register.
    # ------------------------------------------------------------------
    while len(peers) < 2:
        try:
            data, addr = srv.recvfrom(1024)
            # Each client just sends any data – the first packet registers it.
            if addr not in peers.values():
                client_id = len(peers)          # 0 for the first, 1 for the second
                peers[client_id] = addr
                print(f"[SERVER] Registered client {client_id} => {addr}")
        except socket.timeout:
            continue
        except KeyboardInterrupt:
            print("\n[SERVER] Shutting down")
            srv.close()
            sys.exit(0)

    # ------------------------------------------------------------------
    # 2️⃣  Exchange the endpoints.
    # ------------------------------------------------------------------
    a_addr, b_addr = peers[0], peers[1]
    srv.sendto(f"PEER {b_addr[0]} {b_addr[1]}\n".encode(), a_addr)
    srv.sendto(f"PEER {a_addr[0]} {a_addr[1]}\n".encode(), b_addr)
    print("[SERVER] Exchanged endpoints – now acting as pure forwarder if needed")

    # ------------------------------------------------------------------
    # 3️⃣  (Optional) act as a *relay* if direct punching fails.
    #     In this demo we just forward everything we receive.
    # ------------------------------------------------------------------
    stop_evt = threading.Event()
    recv_thread = threading.Thread(target=receiver, args=(srv, stop_evt), daemon=True)
    recv_thread.start()

    try:
        while True:
            try:
                data, src = srv.recvfrom(4096)
                # Figure out the *other* client and forward.
                dst = b_addr if src == a_addr else a_addr
                srv.sendto(data, dst)
            except socket.timeout:
                continue
    except KeyboardInterrupt:
        print("\n[SERVER] Bye")
    finally:
        stop_evt.set()
        srv.close()
        recv_thread.join()

if __name__ == '__main__':
    main()
