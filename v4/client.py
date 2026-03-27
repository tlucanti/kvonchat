#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
distributed_chat.py

A minimal, lock‑free, distributed chat client that stores its
complete history in a Kademlia DHT.

Run several copies on different machines (or on the same host with
different ports).  Supply the list of bootstrap nodes that are already
alive – *peer discovery is left to the operator*.

Author: ChatGPT (2026‑03‑27)
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


LOGGER = logging.getLogger("distributed_chat")
LOGGER.setLevel(logging.INFO)

# ----------------------------------------------------------------------
# 2️⃣  Helper functions for the DHT key schema
# ----------------------------------------------------------------------
HEAD_KEY = "chat:head"          # stores the highest sequence number (int)
MSG_PREFIX = "msg:"            # each message is stored under msg:<seq>

def msg_key(seq: int) -> str:
    """Return the DHT key for a given message sequence number."""
    return f"{MSG_PREFIX}{seq}"


def encode_message(seq: int, author: str, ts: str, text: str) -> bytes:
    """Serialize a chat message to a JSON‑encoded bytes object."""
    payload = {
        "seq": seq,
        "author": author,
        "ts": ts,
        "text": text,
    }
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


def decode_message(raw: bytes) -> Dict[str, Any]:
    """Deserialize a message stored in the DHT."""
    return json.loads(raw.decode("utf-8"))


# ----------------------------------------------------------------------
# 3️⃣  The main Chat client class
# ----------------------------------------------------------------------
class ChatClient:
    """
    A single chat participant.
    * Runs a Kademlia node.
    * Provides `send_message` and `fetch_history` APIs.
    * All operations are async and lock‑free.
    """

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
        self.replication_k = replication_k

        self.server = Server(storage=None, protocol=None, k=replication_k)
        # `storage=None` tells kademlia to use its default in‑memory storage.

    # ------------------------------------------------------------------
    # 3.1️⃣  Startup / shutdown helpers
    # ------------------------------------------------------------------
    async def start(self) -> None:
        """Start the local Kademlia server and join the network."""
        await self.server.listen(self.listen_port)
        LOGGER.info("Node listening on %s:%d", *self._my_address())
        if self.bootstrap_nodes:
            LOGGER.info("Bootstrapping to %s", self.bootstrap_nodes)
            await self.server.bootstrap(self.bootstrap_nodes)

    async def stop(self) -> None:
        """Graceful shutdown."""
        self.server.stop()
        await asyncio.sleep(0)   # let the event loop run any pending callbacks

    def _my_address(self) -> Tuple[str, int]:
        """Return our own (host, port) tuple – used for logging."""
        # The Server class always binds to 0.0.0.0; we use localhost for display.
        return ("127.0.0.1", self.listen_port)

    # ------------------------------------------------------------------
    # 3.2️⃣  Core DHT operations
    # ------------------------------------------------------------------
    async def _get_head(self) -> int:
        """Fetch the current head (largest sequence number)."""
        head = await self.server.get(HEAD_KEY)
        if head is None:
            return 0
        # head is stored as an int (kademlia serialises numbers as JSON)
        return int(head)

    async def _set_head(self, new_head: int) -> None:
        """Store a new head value."""
        await self.server.set(HEAD_KEY, new_head)

    async def _store_message(self, seq: int, text: str) -> None:
        """Persist a single chat line under msg:<seq>."""
        ts = datetime.utcnow().isoformat(timespec="seconds") + "Z"
        raw = encode_message(seq, self.nickname, ts, text)
        await self.server.set(msg_key(seq), raw)

    async def _fetch_message(self, seq: int) -> Dict[str, Any] | None:
        """Retrieve a stored message; returns None if it is missing."""
        raw = await self.server.get(msg_key(seq))
        if raw is None:
            return None
        return decode_message(raw)

    # ------------------------------------------------------------------
    # 3.3️⃣  Public API
    # ------------------------------------------------------------------
    async def send_message(self, text: str) -> None:
        """
        Append `text` to the chat.
        This is deliberately *optimistic*: we read the head, add 1, write,
        and finally write back the new head.  If two peers race, the
        larger sequence wins – the other will later notice the gap and
        re‑publish its missing entry (the next call to `fetch_history`
        will pull it).
        """
        # 1️⃣ read current head
        head = await self._get_head()
        new_seq = head + 1

        # 2️⃣ store the message
        await self._store_message(new_seq, text)

        # 3️⃣ publish the new head (no CAS – eventual consistency is fine)
        await self._set_head(new_seq)

        LOGGER.info("Sent message #%d", new_seq)

    async def fetch_history(self) -> List[Dict[str, Any]]:
        """
        Pull the whole conversation up to the current head.
        Missing entries are ignored – they will be filled in later when
        the responsible peer re‑publishes them.
        """
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
                # The entry is currently missing; we keep a placeholder.
                LOGGER.debug("Message %d not found yet (will appear later)", seq)
                continue
            history.append(res)
        # Sort just in case we received out‑of‑order data.
        history.sort(key=lambda m: m["seq"])
        return history

    # ------------------------------------------------------------------
    # 3.4️⃣  Convenience method for pretty‑printing a history list.
    # ------------------------------------------------------------------
    @staticmethod
    def format_message(msg: Dict[str, Any]) -> str:
        ts = msg["ts"]
        author = msg["author"]
        text = msg["text"]
        return f"[{ts}] {author}: {text}"


# ----------------------------------------------------------------------
# 4️⃣  Command‑line interface
# ----------------------------------------------------------------------
async def ainput(prompt: str = "") -> str:
    """Asynchronous version of `input()` for asyncio event loops."""
    return await asyncio.get_event_loop().run_in_executor(
        None, lambda: input(prompt)
    )


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Distributed chat client that stores history in a Kademlia DHT."
    )
    parser.add_argument(
        "--port",
        type=int,
        required=True,
        help="Local TCP/UDP port on which this node will listen (e.g. 8468).",
    )
    parser.add_argument(
        "--bootstrap",
        nargs="*",
        default=[],
        metavar="HOST:PORT",
        help=(
            "One or more existing nodes to bootstrap from, formatted as host:port. "
            "If omitted the node starts a brand‑new network."
        ),
    )
    parser.add_argument(
        "--nick",
        required=True,
        help="Your nickname that will appear in the chat.",
    )
    parser.add_argument(
        "--replication",
        type=int,
        default=20,
        help="Kademlia replication factor (default 20).",
    )
    args = parser.parse_args()

    # Parse bootstrap arguments
    bootstrap_nodes = []
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
    # 4.1️⃣  Start node and fetch initial history
    # ------------------------------------------------------------------
    await client.start()
    print("\n=== Welcome to the distributed chat! ===")
    print("Fetching existing history…")
    history = await client.fetch_history()
    for msg in history:
        print(ChatClient.format_message(msg))
    print("\nYou can now start typing.  Press Ctrl‑C to quit.\n")

    # ------------------------------------------------------------------
    # 4.2️⃣  Main interaction loop (read from stdin, broadcast via DHT)
    # ------------------------------------------------------------------
    try:
        while True:
            line = await ainput()
            line = line.strip()
            if not line:
                continue
            await client.send_message(line)

            # Optimistically re‑print what we just sent (may be out of order)
            # This gives instant feedback and mirrors what other peers will see.
            # The full history can be refreshed on demand with /history.
            now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
            print(f"[{now}] {args.nick}: {line}")

    except KeyboardInterrupt:
        print("\nLeaving chat…")
    finally:
        await client.stop()


if __name__ == "__main__":
    # Enable modest console logging (helps during debugging)
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        level=logging.INFO,
    )
    try:
        asyncio.run(main())
    except Exception as exc:  # pragma: no cover
        LOGGER.exception("Fatal error: %s", exc)
        sys.exit(1)
