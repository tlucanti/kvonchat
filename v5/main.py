
import threading
from argparse import ArgumentParser

from Server import Server, Address
from Client import Client

def parse_args():
    parser = ArgumentParser(description="Distributed chat client")

    _ = parser.add_argument("--name", required=True, help="nickname")
    _ = parser.add_argument(
        "--port", type=int, required=True, help="UDP port for the local node"
    )
    _ = parser.add_argument(
        "--bootstrap",
        default=None,
        help="Comma‑separated list of existing peers (host:port)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    client = Client(args.name, args.port)

    if args.bootstrap:
        addresses = [Address.from_str(a) for a in args.bootstrap.split(',')]
    else:
        addresses = []

    client.run(addresses)


if __name__ == '__main__':
    import sys
    sys.exit(main())
