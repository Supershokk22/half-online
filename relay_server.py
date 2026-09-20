"""Private-room relay for Half Online — assinado: shokk.

Run this only on a host you control (for occasional play, a Tailscale IP is
enough). It forwards compact player snapshots; it never opens or controls a
game process.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import math
import secrets
from dataclasses import dataclass, field
from typing import Any

from websockets.asyncio.server import ServerConnection, serve

PROTOCOL = 1
MAX_MESSAGE_BYTES = 2_048
LOG = logging.getLogger("half-sword-real-relay")


@dataclass
class Peer:
    connection: ServerConnection
    peer_id: str
    name: str
    role: str
    room_id: str


@dataclass
class Room:
    room_id: str
    host: Peer
    peers: dict[str, Peer] = field(default_factory=dict)
    locked: bool = False


class Relay:
    def __init__(self) -> None:
        self.rooms: dict[str, Room] = {}
        self.peers: dict[ServerConnection, Peer] = {}
        self.lock = asyncio.Lock()

    async def send(self, connection: ServerConnection, message: dict[str, Any]) -> None:
        await connection.send(json.dumps(message, separators=(",", ":")))

    async def broadcast_room(self, room: Room, message: dict[str, Any], skip: Peer | None = None) -> None:
        encoded = json.dumps(message, separators=(",", ":"))
        targets = [peer.connection.send(encoded) for peer in room.peers.values() if peer is not skip]
        if targets:
            await asyncio.gather(*targets, return_exceptions=True)

    async def broadcast_status(self, room: Room) -> None:
        await self.broadcast_room(room, {
            "type": "room.status",
            "room": room.room_id,
            "locked": room.locked,
            "players": [{"id": item.peer_id, "name": item.name, "role": item.role} for item in room.peers.values()],
        })

    async def register(self, connection: ServerConnection, hello: dict[str, Any]) -> Peer | None:
        if hello.get("type") != "hello" or hello.get("protocol") != PROTOCOL:
            await self.send(connection, {"type": "error", "code": "unsupported_protocol"})
            return None
        room_id = str(hello.get("room", "")).strip()[:40]
        name = str(hello.get("name", "")).strip()[:24]
        role = str(hello.get("role", "client"))
        if not room_id or not name or role not in {"host", "client"}:
            await self.send(connection, {"type": "error", "code": "invalid_hello"})
            return None

        async with self.lock:
            room = self.rooms.get(room_id)
            if role == "host":
                if room:
                    await self.send(connection, {"type": "error", "code": "room_already_hosted"})
                    return None
                peer = Peer(connection, secrets.token_urlsafe(12), name, role, room_id)
                room = Room(room_id, peer, {peer.peer_id: peer})
                self.rooms[room_id] = room
            else:
                if not room:
                    await self.send(connection, {"type": "error", "code": "room_not_found"})
                    return None
                if room.locked:
                    await self.send(connection, {"type": "error", "code": "room_locked"})
                    return None
                if len(room.peers) >= 2:
                    await self.send(connection, {"type": "error", "code": "room_full"})
                    return None
                peer = Peer(connection, secrets.token_urlsafe(12), name, role, room_id)
                room.peers[peer.peer_id] = peer
            self.peers[connection] = peer

        await self.send(connection, {"type": "welcome", "peer_id": peer.peer_id, "room": room_id})
        await self.broadcast_room(room, {"type": "peer.joined", "peer": {"id": peer.peer_id, "name": name}}, skip=peer)
        await self.broadcast_status(room)
        LOG.info("%s joined room %s as %s", name, room_id, role)
        return peer

    @staticmethod
    def valid_snapshot(message: dict[str, Any]) -> bool:
        state = message.get("state")
        if not isinstance(state, list) or len(state) != 6:
            return False
        return all(isinstance(value, (int, float)) and math.isfinite(value) and abs(value) < 10_000_000 for value in state)

    async def dispatch(self, peer: Peer, message: dict[str, Any]) -> None:
        message_type = message.get("type")
        room = self.rooms.get(peer.room_id)
        if message_type == "admin":
            if not room or peer is not room.host:
                await self.send(peer.connection, {"type": "error", "code": "host_only"})
                return
            if message.get("action") == "lock":
                room.locked = bool(message.get("value"))
                await self.broadcast_status(room)
                return
            await self.send(peer.connection, {"type": "error", "code": "unknown_admin_action"})
            return
        if message_type != "snapshot" or not self.valid_snapshot(message):
            await self.send(peer.connection, {"type": "error", "code": "invalid_message"})
            return
        if room:
            await self.broadcast_room(room, {"type": "snapshot", "from": peer.peer_id, "state": message["state"]}, skip=peer)

    async def remove(self, peer: Peer) -> None:
        async with self.lock:
            self.peers.pop(peer.connection, None)
            room = self.rooms.get(peer.room_id)
            if not room:
                return
            room.peers.pop(peer.peer_id, None)
            if peer is room.host:
                self.rooms.pop(room.room_id, None)
                recipients = list(room.peers.values())
            else:
                recipients = list(room.peers.values())
        for recipient in recipients:
            try:
                await self.send(recipient.connection, {"type": "room.closed" if peer is room.host else "peer.left"})
            except Exception:
                pass
        if room and peer is not room.host:
            await self.broadcast_status(room)
        LOG.info("%s left room %s", peer.name, peer.room_id)

    async def handler(self, connection: ServerConnection) -> None:
        peer: Peer | None = None
        try:
            raw = await asyncio.wait_for(connection.recv(), timeout=10)
            if not isinstance(raw, str) or len(raw.encode("utf-8")) > MAX_MESSAGE_BYTES:
                return
            peer = await self.register(connection, json.loads(raw))
            if not peer:
                return
            async for raw in connection:
                if not isinstance(raw, str) or len(raw.encode("utf-8")) > MAX_MESSAGE_BYTES:
                    continue
                try:
                    await self.dispatch(peer, json.loads(raw))
                except json.JSONDecodeError:
                    await self.send(connection, {"type": "error", "code": "bad_json"})
        except Exception as exc:
            LOG.debug("connection closed: %s", exc)
        finally:
            if peer:
                await self.remove(peer)


async def main() -> None:
    parser = argparse.ArgumentParser(description="Half Sword Online Real Multiplayer relay")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", default=8790, type=int)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    relay = Relay()
    async with serve(relay.handler, args.host, args.port, max_size=MAX_MESSAGE_BYTES, ping_interval=15, ping_timeout=15, reuse_address=True):
        LOG.info("relay listening on ws://%s:%d", args.host, args.port)
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
