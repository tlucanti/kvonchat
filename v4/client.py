#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
distributed_chat.py

A lock‑free, distributed chat client that stores the whole chat history
in a Kademlia DHT.  Peer‑discovery is omitted – you supply bootstrap nodes
via the command line.

Requires:  pip install kademlia==0.2.1
"""

import sys
import asyncio
import argparse
import json
import logging
from datetime import datetime
from typing import List, Tuple, Dict, Any

# ----------------------------------------------------------------------
# 1️⃣  Kademlia node utilities
# ----------------------------------------------------------------------
from kademlia.network import Server  # asyncio‑based Kademlia implementation

loglevel = logging.ERROR


LOGGER = logging.getLogger("distributed_chat")
LOGGER.setLevel(loglevel)

# ----------------------------------------------------------------------
# 2️⃣  DHT key schema helpers
# ----------------------------------------------------------------------
HEAD_KEY = "chat:head"          # stores the latest sequence number (int)
MSG_PREFIX = "msg:"            # each chat line is stored under msg:<seq>


def msg_key(seq: int) -> str:
    """DHT key for a given message sequence number."""
    return f"{MSG_PREFIX}{seq}"


def encode_message(seq: int, author: str, ts: str, text: str) -> bytes:
    """Serialize a chat message to JSON‑encoded bytes."""
    payload = {"seq": seq, "author": author, "ts": ts, "text": text}
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


def decode_message(raw: bytes) -> Dict[str, Any]:
    """Deserialize a message retrieved from the DHT."""
    return json.loads(raw.decode("utf-8"))


# ----------------------------------------------------------------------
# 3️⃣  Chat client implementation
# ----------------------------------------------------------------------
class ChatClient:
    """Single chat participant that talks to a Kademlia DHT."""

    def __init__(
        self,
        listen_port: int,
        bootstrap_nodes: List[Tuple[str, int]],
        nickname: str,
        replication_k: int = 20,
    ):
        self.listen_port = listen_port
        self.bootstrap_nodes = bootstrap_nodes
        self.nickname = nickname

        # ------------------------------------------------------------------
        # NOTE:  The current kademlia.Server signature is:
        #   Server(ksize=20, alpha=3, node_id=None, storage=None)
        # `ksize` is the replication factor (the “k” from the paper).
        # ------------------------------------------------------------------
        self.server = Server(ksize=replication_k, storage=None)

    # ------------------------------------------------------------------
    # 3.1️⃣  Lifecycle helpers
    # ------------------------------------------------------------------
    async def start(self) -> None:
        """Start listening and bootstrap to known peers."""
        await self.server.listen(self.listen_port)
        LOGGER.info("Node listening on %s:%d", *self._my_address())
        if self.bootstrap_nodes:
            LOGGER.info("Bootstrapping to %s", self.bootstrap_nodes)
            await self.server.bootstrap(self.bootstrap_nodes)

    async def stop(self) -> None:
        """Graceful shutdown."""
        self.server.stop()
        await asyncio.sleep(0)   # let pending callbacks run

    def _my_address(self) -> Tuple[str, int]:
        """Return a printable (host, port) pair."""
        return ("127.0.0.1", self.listen_port)

    # ------------------------------------------------------------------
    # 3.2️⃣  Raw DHT operations
    # ------------------------------------------------------------------
    async def _get_head(self) -> int:
        """Return the current highest sequence number (0 if none)."""
        head = await self.server.get(HEAD_KEY)
        return int(head) if head is not None else 0

    async def _set_head(self, new_head: int) -> None:
        """Persist a new head value."""
        await self.server.set(HEAD_KEY, new_head)

    async def _store_message(self, seq: int, text: str) -> None:
        """Store a single chat line under `msg:<seq>`."""
        ts = datetime.utcnow().isoformat(timespec="seconds") + "Z"
        raw = encode_message(seq, self.nickname, ts, text)
        await self.server.set(msg_key(seq), raw)

    async def _fetch_message(self, seq: int) -> Dict[str, Any] | None:
        """Retrieve a stored message; returns ``None`` if absent."""
        raw = await self.server.get(msg_key(seq))
        return decode_message(raw) if raw is not None else None

    # ------------------------------------------------------------------
    # 3.3️⃣  Public API
    # ------------------------------------------------------------------
    async def send_message(self, text: str) -> None:
        """Append a line to the chat (optimistic, no CAS)."""
        head = await self._get_head()
        new_seq = head + 1
        await self._store_message(new_seq, text)
        await self._set_head(new_seq)
        LOGGER.info("Sent message #%d", new_seq)

    async def fetch_history(self) -> List[Dict[str, Any]]:
        """Pull the entire conversation up to the current head."""
        head = await self._get_head()
        if head == 0:
            return []

        tasks = [self._fetch_message(seq) for seq in range(1, head + 1)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        history: List[Dict[str, Any]] = []
        for seq, res in enumerate(results, start=1):
            if isinstance(res, Exception):
                LOGGER.warning("Error fetching %s: %s", msg_key(seq), res)
                continue
            if res is None:
                LOGGER.debug("Message %d missing (will appear later)", seq)
                continue
            history.append(res)

        history.sort(key=lambda m: m["seq"])
        return history

    @staticmethod
    def format_message(msg: Dict[str, Any]) -> str:
        return f"[{msg['ts']}] {msg['author']}: {msg['text']}"


# ----------------------------------------------------------------------
# 4️⃣  Command‑line interface
# ----------------------------------------------------------------------
async def ainput(prompt: str = "") -> str:
    """Async wrapper around built‑in ``input``."""
    return await asyncio.get_event_loop().run_in_executor(
        None, lambda: input(prompt)
    )


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Distributed chat client using a Kademlia DHT."
    )
    parser.add_argument(
        "--port",
        type=int,
        required=True,
        help="Local port for this node (e.g. 8468).",
    )
    parser.add_argument(
        "--bootstrap",
        nargs="*",
        default=[],
        metavar="HOST:PORT",
        help="Existing nodes to bootstrap from (host:port).",
    )
    parser.add_argument(
        "--nick",
        required=True,
        help="Your nickname shown in the chat.",
    )
    parser.add_argument(
        "--replication",
        type=int,
        default=20,
        help="Kademlia replication factor (default 20).",
    )
    args = parser.parse_args()

    # Parse bootstrap specifications
    bootstrap_nodes: List[Tuple[str, int]] = []
    for spec in args.bootstrap:
        try:
            host, port_str = spec.split(":")
            bootstrap_nodes.append((host, int(port_str)))
        except Exception:
            parser.error(f"Invalid bootstrap spec '{spec}'. Use host:port.")

    client = ChatClient(
        listen_port=args.port,
        bootstrap_nodes=bootstrap_nodes,
        nickname=args.nick,
        replication_k=args.replication,
    )

    # ------------------------------------------------------------------
    # Start node and show existing history
    # ------------------------------------------------------------------
    await client.start()
    print("\n=== Welcome to the distributed chat! ===")
    print("Fetching existing history…")
    for msg in await client.fetch_history():
        print(ChatClient.format_message(msg))

    print("\nYou can now start typing.  Press Ctrl‑C to quit.\n")

    # ------------------------------------------------------------------
    # Main REPL loop
    # ------------------------------------------------------------------
    try:
        while True:
            line = (await ainput()).strip()
            if not line:
                continue
            await client.send_message(line)

            now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
            print(f"[{now}] {args.nick}: {line}")

    except KeyboardInterrupt:
        print("\nLeaving chat…")
    finally:
        await client.stop()


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        level=loglevel,
    )
    try:
        asyncio.run(main())
    except Exception as exc:  # pragma: no cover
        LOGGER.exception("Fatal error: %s", exc)
        sys.exit(1)
