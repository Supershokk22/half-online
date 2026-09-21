"""Per-PC bridge between the UE4SS file bridge and the private relay — assinado: shokk."""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import time
from pathlib import Path

from websockets.asyncio.client import connect

PROTOCOL = 1


def parse_state(raw: str) -> list[float] | None:
    pieces = raw.strip().split()
    if len(pieces) != 7 or pieces[0] != "state":
        return None
    try:
        return [float(value) for value in pieces[1:]]
    except ValueError:
        return None


def write_inbound(path: Path, state: list[float]) -> None:
    content = "state " + " ".join(f"{value:.4f}" for value in state) + "\n"
    temp = path.with_suffix(".tmp")
    temp.write_text(content, encoding="utf-8")
    temp.replace(path)


def write_room_status(path: Path, message: dict[str, object]) -> None:
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(message, separators=(",", ":")), encoding="utf-8")
    temp.replace(path)


def clear_file(path: Path) -> None:
    """Remove state that belonged to a player who is no longer in the room."""
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def request_game_action(path: Path, action: str) -> None:
    """Small host/client-to-mod command; the UE4SS mod consumes it safely."""
    temp = path.with_suffix(".tmp")
    temp.write_text(action + "\n", encoding="utf-8")
    temp.replace(path)


async def send_loop(ws, outbound: Path, control: Path) -> None:
    previous = ""
    previous_control = ""
    while True:
        try:
            raw = outbound.read_text(encoding="utf-8")
        except OSError:
            raw = ""
        if raw != previous:
            state = parse_state(raw)
            if state:
                await ws.send(json.dumps({"type": "snapshot", "state": state}, separators=(",", ":")))
                previous = raw
        try:
            raw_control = control.read_text(encoding="utf-8").strip()
        except OSError:
            raw_control = ""
        if raw_control and raw_control != previous_control:
            parts = raw_control.split()
            if len(parts) == 2 and parts[0] == "lock" and parts[1] in {"on", "off"}:
                await ws.send(json.dumps({"type": "admin", "action": "lock", "value": parts[1] == "on"}, separators=(",", ":")))
                previous_control = raw_control
        await asyncio.sleep(0.05)  # 20 Hz file bridge; bounded and low overhead.


async def run(args: argparse.Namespace) -> None:
    bridge = Path(args.bridge).expanduser()
    bridge.mkdir(parents=True, exist_ok=True)
    outbound, inbound = bridge / "mp_outbound.txt", bridge / "mp_inbound.txt"
    control, room_status = bridge / "mp_control.txt", bridge / "mp_room_status.json"
    game_control = bridge / "mp_game_control.txt"
    # A reopened host must not see the last session's ghost avatar while alone.
    clear_file(inbound)
    request_game_action(game_control, "remote remove")
    while True:
        try:
            async with connect(args.server, max_size=2_048, ping_interval=15, ping_timeout=15) as ws:
                await ws.send(json.dumps({"type": "hello", "protocol": PROTOCOL, "name": args.name, "role": args.role, "room": args.room}))
                welcome = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
                if welcome.get("type") == "error":
                    raise RuntimeError(welcome.get("code", "relay_error"))
                logging.info("connected to room %s as %s", args.room, args.role)
                sender = asyncio.create_task(send_loop(ws, outbound, control))
                try:
                    async for raw in ws:
                        message = json.loads(raw)
                        if message.get("type") == "snapshot":
                            write_inbound(inbound, message["state"])
                        elif message.get("type") == "room.status":
                            write_room_status(room_status, message)
                        elif message.get("type") in {"peer.left", "room.closed"}:
                            clear_file(inbound)
                            request_game_action(game_control, "remote remove")
                        elif message.get("type") == "error":
                            logging.warning("relay error: %s", message.get("code"))
                finally:
                    sender.cancel()
                    await asyncio.gather(sender, return_exceptions=True)
        except Exception as exc:
            logging.warning("connection unavailable: %s; retrying in 3s", exc)
            await asyncio.sleep(3)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Half Sword Online Real Multiplayer peer bridge")
    parser.add_argument("--server", required=True, help="URL WebSocket do relay: ws:// ou wss://")
    parser.add_argument("--room", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--role", choices=("host", "client"), required=True)
    parser.add_argument("--bridge", default=str(Path.home() / "AppData/Local/HalfSwordUE5/Saved/HalfSwordOnlineReal"))
    options = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    asyncio.run(run(options))
