# common.py – helper functions used by both scripts
import socket
import threading
import sys

def start_receiver(sock: socket.socket, stop_event: threading.Event):
    """
    Continuously read from the socket and print incoming lines.
    Runs in its own thread.
    """
    while not stop_event.is_set():
        try:
            data, addr = sock.recvfrom(4096)          # UDP is message‑oriented
            if not data:
                continue
            # Decode and strip the trailing newline that the sender adds.
            line = data.decode('utf-8', errors='replace').rstrip('\r\n')
            print(f"\r< {addr[0]}:{addr[1]} | {line}\n> ", end='', flush=True)
        except socket.timeout:
            continue
        except OSError:
            # Socket closed – exit the thread.
            break
        except Exception as exc:
            print(f"\n[receiver error] {exc}", file=sys.stderr)

def start_sender(sock: socket.socket, remote_addr):
    """
    Read lines from stdin and send them to the remote address.
    The function returns when the user types '!quit' or hits Ctrl‑C.
    """
    try:
        while True:
            line = input("> ")
            if line.strip() == "!quit":
                break
            # Append a newline, the receiver strips it for nice printing.
            sock.sendto((line + "\n").encode('utf-8'), remote_addr)
    except (KeyboardInterrupt, EOFError):
        pass   # graceful exit
