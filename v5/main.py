
from argparse import ArgumentParser
from Server import Server, Address
from Peer import Peer

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
    server = Server(args.port)
    addresses = []
    if args.bootstrap:
        addresses = [Address.from_str(a) for a in args.bootstrap.split(',')]
    peer = Peer(server, args.name)
    peer.register(addresses)


if __name__ == '__main__':
    main()
