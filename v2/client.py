# client.py
"""
UDP NAT‑hole‑punching client.

Usage:
    python client.py <server_ip> <server_port>
Example:
    python client.py 203.0.113.42 9999
"""

import socket, sys, threading, time
from common import receiver, sender

def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)

    SERVER_IP   = sys.argv[1]
    SERVER_PORT = int(sys.argv[2])
    SERVER_ADDR = (SERVER_IP, SERVER_PORT)

    # ------------------------------------------------------------------
    # 1️⃣  Create a UDP socket – let the OS pick a local port (important
    #     for NAT hole punching).
    # ------------------------------------------------------------------
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(1)

    # ------------------------------------------------------------------
    # 2️⃣  Register with the rendez‑vous server (this creates the NAT mapping).
    # ------------------------------------------------------------------
    print("[CLIENT] Sending HELLO to server")
    sock.sendto(b'HELLO\n', SERVER_ADDR)

    # ------------------------------------------------------------------
    # 3️⃣  Wait for the server to give us the peer's public endpoint.
    # ------------------------------------------------------------------
    peer_addr = None
    while peer_addr is None:
        try:
            data, _ = sock.recvfrom(1024)
            print(f"[CLIENT] Got {data} from server")
            # Expected format: b'PEER <ip> <port>\n'
            parts = data.decode().strip().split()
            if parts[0] == "PEER" and len(parts) == 3:
                peer_addr = (parts[1], int(parts[2]))
                print(f"[CLIENT] Got peer address {peer_addr}")
        except socket.timeout:
            # Resend registration every few seconds in case the first packet got lost.
            print("[CLIENT] Sending HELLO to server")
            sock.sendto(b'HELLO\n', SERVER_ADDR)
            continue
        except KeyboardInterrupt:
            print("\n[CLIENT] Exiting")
            sock.close()
            sys.exit(0)

    # ------------------------------------------------------------------
    # 4️⃣  Start a background thread that prints anything we receive.
    # ------------------------------------------------------------------
    stop_evt = threading.Event()
    recv_thread = threading.Thread(target=receiver, args=(sock, stop_evt), daemon=True)
    recv_thread.start()

    # ------------------------------------------------------------------
    # 5️⃣  Begin aggressive punching: keep sending empty “keep‑alive”
    #     packets to the peer while the user is typing.
    # ------------------------------------------------------------------
    def punch_loop():
        while not stop_evt.is_set():
            try:
                sock.sendto(b'\n', peer_addr)   # a minimal packet – keeps the NAT entry alive
            except OSError:
                break
            time.sleep(10)    # 5 packets per second is enough for most NATs

    punch_thread = threading.Thread(target=punch_loop, daemon=True)
    punch_thread.start()

    # ------------------------------------------------------------------
    # 6️⃣  Normal chat loop – read from stdin and send to the peer.
    # ------------------------------------------------------------------
    try:
        sender(sock, peer_addr)
    finally:
        stop_evt.set()
        sock.close()
        recv_thread.join()
        print("\n[CLIENT] Bye")

if __name__ == '__main__':
    main()
