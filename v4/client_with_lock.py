#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Distributed single‑room chat that stores the whole history in a Kademlia DHT.
No automatic peer‑discovery – you must give each instance a bootstrap list
(host:port pairs) manually.

Requirements:
    pip install kademlia aiohttp
"""

import asyncio
import json
import sys
import time
import uuid
from argparse import ArgumentParser
from typing import List, Tuple, Dict, Any

from kademlia.network import Server

# ----------------------------------------------------------------------
# Configuration constants (feel free to tune)
# ----------------------------------------------------------------------
CHAT_LOG_KEY = "chat:log"          # DHT key for the complete JSON log
CHAT_LOCK_KEY = "chat:lock"        # DHT key for a very simple lock
LOCK_TTL = 5.0                     # seconds the lock is considered valid
POLL_INTERVAL = 2.0                # seconds between background log polls
MAX_RETRIES = 5                    # how many times we retry a lock acquisition
RETRY_BACKOFF = 0.5                # base back‑off (seconds) for retries

# ----------------------------------------------------------------------
# Type aliases
# ----------------------------------------------------------------------
Message = Dict[str, Any]   # {"ts": float, "author": str, "text": str}
Log = List[Message]

# ----------------------------------------------------------------------
# DHT helper functions (all async)
# ----------------------------------------------------------------------
async def get_log(server: Server) -> Log:
    """Return the current chat log (empty list if the key does not exist)."""
    try:
        raw = await server.get(CHAT_LOG_KEY)
        if raw is None:
            return []
        return json.loads(raw)
    except Exception as exc:            # pragma: no cover   (just safety‑net)
        print(f"[WARN] get_log failed: {exc}", file=sys.stderr)
        return []


async def put_log(server: Server, log: Log) -> None:
    """Serialise and store the whole chat log."""
    data = json.dumps(log)
    await server.set(CHAT_LOG_KEY, data)


# ----------------------------------------------------------------------
# Simple *optimistic* lock implementation
#
# Because the kademlia library has no built‑in TTL we store a small JSON
# payload: {"owner": <uuid>, "ts": <timestamp>}.  When a client tries to
# acquire the lock it reads the payload, checks the age, and if the lock
# is stale (or does not exist) writes its own payload.
#
# This is **not** a full linearizable lock – it is good enough for a low‑
# traffic chat where only a handful of participants write at the same time.
# ----------------------------------------------------------------------
def _make_lock_value(owner_id: str) -> str:
    """Encode the lock payload as a JSON string."""
    return json.dumps({"owner": owner_id, "ts": time.time()})


def _decode_lock_value(raw: Any) -> Tuple[str, float]:
    """Return (owner_id, ts) from the stored payload.  Handles malformed data."""
    try:
        data = json.loads(raw)
        return data.get("owner", ""), float(data.get("ts", 0))
    except Exception:
        return "", 0.0


async def acquire_lock(server: Server) -> bool:
    """Try to become the owner of CHAT_LOCK_KEY. Returns True on success."""
    my_id = str(uuid.uuid4())
    lock_payload = _make_lock_value(my_id)

    # 1️⃣  Read the current lock (if any)
    current_raw = await server.get(CHAT_LOCK_KEY)

    if current_raw is None:
        # Nobody holds the lock → try to write ours
        await server.set(CHAT_LOCK_KEY, lock_payload)
        # Verify that we really own it (race condition safety)
        verify_raw = await server.get(CHAT_LOCK_KEY)
        owner, _ = _decode_lock_value(verify_raw)
        return owner == my_id

    # 2️⃣  A lock exists – see whether it is still fresh
    owner, ts = _decode_lock_value(current_raw)
    if time.time() - ts > LOCK_TTL:
        # Existing lock is stale → overwrite it
        await server.set(CHAT_LOCK_KEY, lock_payload)
        verify_raw = await server.get(CHAT_LOCK_KEY)
        owner2, _ = _decode_lock_value(verify_raw)
        return owner2 == my_id

    # 3️⃣  Lock is still valid – we cannot acquire it now
    return False


async def release_lock(server: Server) -> None:
    """Delete the lock key (best‑effort)."""
    try:
        # Setting the key to `None` removes it – the library translates that
        # to a DELETE RPC.
        await server.set(CHAT_LOCK_KEY, None)
    except Exception:
        pass


# ----------------------------------------------------------------------
# Chat client class (the user‑facing part)
# ----------------------------------------------------------------------
class ChatClient:
    def __init__(
        self,
        username: str,
        listen_port: int,
        bootstrap: List[Tuple[str, int]],
        loop: asyncio.AbstractEventLoop,
    ):
        self.username = username
        self.listen_port = listen_port
        self.bootstrap = bootstrap
        self.loop = loop
        self.dht = Server()
        self.last_seen_index = -1  # index of the most recent message we printed

    async def start(self) -> None:
        # 1️⃣  Bind the local DHT node (UDP)
        await self.dht.listen(self.listen_port)

        # 2️⃣  Join the overlay using the manually supplied peers
        if self.bootstrap:
            await self.dht.bootstrap(self.bootstrap)

        print(f"[INFO] DHT listening on 0.0.0.0:{self.listen_port}")

        # 3️⃣  Print the complete history that already exists (new client case)
        await self._print_new_messages(initial=True)

        # 4️⃣  Background task that keeps the UI up‑to‑date
        self.loop.create_task(self._poll_loop())

    async def _poll_loop(self) -> None:
        while True:
            await asyncio.sleep(POLL_INTERVAL)
            await self._print_new_messages()

    async def _print_new_messages(self, initial: bool = False) -> None:
        """Fetch the log and output everything we have not seen yet."""
        log = await get_log(self.dht)
        start = 0 if initial else self.last_seen_index + 1
        for idx in range(start, len(log)):
            msg = log[idx]
            ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(msg["ts"]))
            print(f"[{ts}] {msg['author']}: {msg['text']}")
        self.last_seen_index = len(log) - 1

    async def send_message(self, text: str) -> None:
        """Append a new entry to the shared log.  Retries if the lock is busy."""
        for attempt in range(1, MAX_RETRIES + 1):
            got = await acquire_lock(self.dht)
            if got:
                try:
                    # ---- critical section -------------------------------------------------
                    log = await get_log(self.dht)
                    log.append(
                        {"ts": time.time(), "author": self.username, "text": text}
                    )
                    await put_log(self.dht, log)
                    # -----------------------------------------------------------------------
                finally:
                    await release_lock(self.dht)
                # Print our own line right away (so the UI feels snappy)
                await self._print_new_messages()
                return
            else:
                backoff = RETRY_BACKOFF * (2 ** (attempt - 1))
                await asyncio.sleep(backoff)

        print(
            "[ERROR] Could not obtain the lock after several retries – message lost.",
            file=sys.stderr,
        )

    def shutdown(self) -> None:
        """Stop the local DHT node.  No `await` needed because `stop()` is synchronous."""
        self.dht.stop()


# ----------------------------------------------------------------------
# CLI parsing helpers
# ----------------------------------------------------------------------
def parse_bootstrap(arglist: List[str]) -> List[Tuple[str, int]]:
    """Transform 'host1:port1,host2:port2' → [('host1', port1), …]"""
    peers: List[Tuple[str, int]] = []
    for item in arglist:
        if not item:
            continue
        host, port = item.split(":")
        peers.append((host, int(port)))
    return peers


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------
async def async_main() -> None:
    parser = ArgumentParser(description="Distributed chat client (Kademlia DHT)")
    parser.add_argument("--user", required=True, help="Your nickname")
    parser.add_argument(
        "--port", type=int, required=True, help="UDP/TCP port for the local DHT node"
    )
    parser.add_argument(
        "--bootstrap",
        default="",
        help="Comma‑separated list of existing peers (host:port).  Empty → single node.",
    )
    args = parser.parse_args()

    bootstrap_peers = parse_bootstrap(args.bootstrap.split(","))

    loop = asyncio.get_event_loop()
    client = ChatClient(
        username=args.user,
        listen_port=args.port,
        bootstrap=bootstrap_peers,
        loop=loop,
    )

    await client.start()

    # ------------------------------------------------------------------
    # Simple REPL – read lines from stdin and forward them to the DHT
    # ------------------------------------------------------------------
    try:
        while True:
            line = await loop.run_in_executor(None, sys.stdin.readline)
            if not line:                      # EOF
                break
            line = line.rstrip("\n")
            if line.strip() == "":
                continue
            await client.send_message(line)
    except (KeyboardInterrupt, EOFError):
        print("\n[INFO] Exiting…")
    finally:
        client.shutdown()


if __name__ == "__main__":
    asyncio.run(async_main())
