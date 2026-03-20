# common.py
import socket
import threading
import sys

def receiver(sock: socket.socket, stop_evt: threading.Event):
    """Print incoming UDP packets to stdout."""
    while not stop_evt.is_set():
        try:
            data, addr = sock.recvfrom(4096)
            if not data:
                continue
            line = data.decode(errors='replace').rstrip('\r\n')
            print(f"\r< {addr[0]}:{addr[1]} | {line}\n> ", end='', flush=True)
        except socket.timeout:
            continue
        except OSError:
            break   # socket closed
        except Exception as e:
            print(f"\n[receiver error] {e}", file=sys.stderr)

def sender(sock: socket.socket, remote):
    """Read from stdin and send to remote."""
    try:
        while True:
            line = input("> ")
            if line.strip() == "!quit":
                break
            sock.sendto((line + "\n").encode(), remote)
    except (KeyboardInterrupt, EOFError):
        pass
