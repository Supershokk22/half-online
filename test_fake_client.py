"""Self-contained smoke test for the Half Online room relay — assinado: shokk."""
import asyncio
import json

from websockets.asyncio.client import connect
from websockets.asyncio.server import serve

from relay_server import PROTOCOL, Relay


async def hello(ws, name, role, room="teste-final"):
    await ws.send(json.dumps({"type": "hello", "protocol": PROTOCOL,
                              "name": name, "role": role, "room": room}))
    return json.loads(await asyncio.wait_for(ws.recv(), timeout=2))


async def run():
    relay = Relay()
    async with serve(relay.handler, "127.0.0.1", 0, max_size=2048) as server:
        port = server.sockets[0].getsockname()[1]
        url = f"ws://127.0.0.1:{port}"
        async with connect(url) as host:
            host_welcome = await hello(host, "Host", "host")
            assert host_welcome["type"] == "welcome"
            assert host_welcome["session"]

            async with connect(url) as client:
                client_welcome = await hello(client, "Amigo", "client")
                assert client_welcome["type"] == "welcome"
                assert client_welcome["session"] == host_welcome["session"]

                # Drain the initial status plus join/status packets, then prove
                # a compact snapshot relays.
                while True:
                    queued = json.loads(await asyncio.wait_for(host.recv(), timeout=2))
                    if queued.get("type") == "room.status" and len(queued.get("players", [])) == 2:
                        break
                await client.send(json.dumps({"type": "snapshot", "state": [1, 2, 3, 4, 5, 6]}))
                forwarded = json.loads(await asyncio.wait_for(host.recv(), timeout=2))
                assert forwarded["type"] == "snapshot" and forwarded["state"] == [1, 2, 3, 4, 5, 6]

                async with connect(url) as third:
                    rejected = await hello(third, "Terceiro", "client")
                    assert rejected == {"type": "error", "code": "room_full"}

            left = json.loads(await asyncio.wait_for(host.recv(), timeout=2))
            assert left["type"] == "peer.left"
    print("[OK] host/client accepted, session shared, snapshot forwarded, room limit enforced, leave notified")


if __name__ == "__main__":
    asyncio.run(run())
