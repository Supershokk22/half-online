"""Per-PC bridge between the UE4SS file bridge and the private relay — assinado: shokk."""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import time
from pathlib import Path

from websockets.asyncio.client import connect

PROTOCOL = 2
LEASE_SECONDS = 6


def write_bridge_text(path: Path, content: str) -> bool:
    """Write a tiny bridge file without dropping the socket on Windows locks.

    UE4SS/Lua may briefly hold the destination without FILE_SHARE_DELETE, which
    makes Path.replace() raise WinError 5. Retry the atomic path first, then use
    a direct overwrite; a missed frame is preferable to disconnecting the peer.
    """
    temp = path.with_suffix(".tmp")
    for _ in range(4):
        try:
            temp.write_text(content, encoding="utf-8")
            temp.replace(path)
            return True
        except PermissionError:
            time.sleep(0.01)
        except OSError as exc:
            logging.debug("atomic bridge write failed for %s: %s", path.name, exc)
            break
    for _ in range(4):
        try:
            path.write_text(content, encoding="utf-8")
            try:
                temp.unlink(missing_ok=True)
            except OSError:
                pass
            return True
        except PermissionError:
            time.sleep(0.01)
        except OSError as exc:
            logging.warning("bridge write skipped for %s: %s", path.name, exc)
            return False
    logging.warning("bridge write skipped for %s: file remained locked", path.name)
    return False


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
    write_bridge_text(path, content)


def write_room_status(path: Path, message: dict[str, object]) -> None:
    write_bridge_text(path, json.dumps(message, separators=(",", ":")))


def clear_file(path: Path) -> None:
    """Remove state that belonged to a player who is no longer in the room."""
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def request_game_action(path: Path, action: str) -> None:
    """Small host/client-to-mod command; the UE4SS mod consumes it safely."""
    write_bridge_text(path, action + "\n")


def write_session(path: Path, session: str, role: str, room: str, players: int) -> None:
    """Publish a short-lived accepted-room lease for the UE4SS bridge.

    The game must never trust a left-over role/control file.  It may only act
    while this lease is fresh and belongs to the current relay session.
    """
    expiry = int(time.time()) + LEASE_SECONDS
    line = f"v2 {session} {role} {room} {expiry} {players} openworld-v1\n"
    write_bridge_text(path, line)


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
            elif raw_control.startswith("game "):
                await ws.send(json.dumps({"type": "admin", "action": "game_control", "value": raw_control}, separators=(",", ":")))
                previous_control = raw_control
        await asyncio.sleep(0.05)  # 20 Hz file bridge; bounded and low overhead.


async def lease_loop(session_path: Path, session: str, args: argparse.Namespace, state: dict[str, int]) -> None:
    while True:
        write_session(session_path, session, args.role, args.room, state["players"])
        await asyncio.sleep(1)


async def run(args: argparse.Namespace) -> None:
    bridge = Path(args.bridge).expanduser()
    bridge.mkdir(parents=True, exist_ok=True)
    outbound, inbound = bridge / "mp_outbound.txt", bridge / "mp_inbound.txt"
    control, room_status = bridge / "mp_control.txt", bridge / "mp_room_status.json"
    game_control, role_file = bridge / "mp_game_control.txt", bridge / "mp_role.txt"
    session_file, world_control = bridge / "mp_session.txt", bridge / "mp_openworld_control.txt"
    # A reopened host must not see the last session's ghost avatar while alone.
    clear_file(inbound)
    for path in (game_control, role_file, session_file, world_control, room_status):
        clear_file(path)
    while True:
        try:
            async with connect(args.server, max_size=2_048, ping_interval=15, ping_timeout=15) as ws:
                await ws.send(json.dumps({"type": "hello", "protocol": PROTOCOL, "name": args.name, "role": args.role, "room": args.room}))
                welcome = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
                if welcome.get("type") == "error":
                    raise RuntimeError(welcome.get("code", "relay_error"))
                if welcome.get("type") != "welcome" or not isinstance(welcome.get("session"), str):
                    raise RuntimeError("invalid_welcome")
                session = welcome["session"]
                state = {"players": int(welcome.get("players", 1))}
                logging.info("connected to room %s as %s", args.room, args.role)
                write_bridge_text(role_file, args.role + "\n")
                write_session(session_file, session, args.role, args.room, state["players"])
                if args.openworld:
                    request_game_action(world_control, f"openworld start {session}")
                sender = asyncio.create_task(send_loop(ws, outbound, control))
                lease = asyncio.create_task(lease_loop(session_file, session, args, state))
                try:
                    async for raw in ws:
                        message = json.loads(raw)
                        if message.get("type") == "snapshot":
                            write_inbound(inbound, message["state"])
                        elif message.get("type") == "room.status":
                            if message.get("session") == session:
                                state["players"] = len(message.get("players", []))
                            write_room_status(room_status, message)
                        elif message.get("type") in {"peer.left", "room.closed"}:
                            clear_file(inbound)
                            clear_file(world_control)
                        elif message.get("type") == "game.control":
                            request_game_action(game_control, str(message.get("command", "")))
                        elif message.get("type") == "error":
                            logging.warning("relay error: %s", message.get("code"))
                finally:
                    sender.cancel()
                    lease.cancel()
                    await asyncio.gather(sender, lease, return_exceptions=True)
                    # A failed socket must instantly revoke game authority and
                    # prevent a stale automatic travel on the next launch.
                    clear_file(inbound)
                    clear_file(session_file)
                    clear_file(world_control)
        except Exception as exc:
            logging.warning("connection unavailable: %s; retrying in 3s", exc)
            await asyncio.sleep(3)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Half Sword Online Real Multiplayer peer bridge")
    parser.add_argument("--server", required=True, help="URL WebSocket do relay: ws:// ou wss://")
    parser.add_argument("--room", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--role", choices=("host", "client"), required=True)
    parser.add_argument("--openworld", action="store_true", help="Envia o jogador para o lobby Open World ao conectar")
    parser.add_argument("--bridge", default=str(Path.home() / "AppData/Local/HalfSwordUE5/Saved/HalfSwordOnlineReal"))
    options = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    asyncio.run(run(options))
