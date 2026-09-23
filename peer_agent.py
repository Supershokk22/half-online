"""Per-PC bridge between the UE4SS file bridge and the private relay — assinado: shokk."""
from __future__ import annotations

import argparse
import asyncio
import base64
import json
import logging
import time
from pathlib import Path, PurePosixPath

from websockets.asyncio.client import connect

PROTOCOL = 2
LEASE_SECONDS = 6
MAX_SYNC_FRAME = 1_000_000  # one file_sync payload (lua/py/cmd/md/pak) per message.

# Everything that lives in the game/repo runtime is syncable; only editor
# sources, build leftovers and logs stay local.
SYNC_EXCLUDE_PREFIXES = (
    ".git/",
    "logs/",
    "HalfOpenWorldV1/Content/",
    "HalfOpenWorldV1/Source/",
)
SYNC_ALLOWED_ROOTS = (
    "peer_agent.py",
    "relay_server.py",
    "real_launcher.py",
    "test_fake_client.py",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "GUIA-PARA-IA.md",
    "HANDSHAKE-VERINE.md",
    "INSTALAR-MOD-FASE-1.cmd",
    "INSTALAR-MOD-FASE-1.ps1",
    "LEIA-ME-PORTATIL.txt",
    "PLANO-PROGRESSO.md",
    "README.md",
    "requirements.txt",
    "STATUS-TECNICO.md",
    "start_host_relay.cmd",
    "start_peer_agent.cmd",
    "ABRIR-HALF-SWORD-ONLINE-REAL.cmd",
    "ABRIR-LAUNCHER-PORTATIL.cmd",
    "CONECTAR.cmd",
    "CONECTAR-AMIGO.cmd",
    "CONECTAR-AMIGO-FIX.cmd",
    "HOSTEAR.cmd",
    "HalfSwordOnlineRealMod/",
    "HalfOpenWorldV1/HalfSwordBridge/",
    "HalfOpenWorldV1/Z_HalfOpenWorldV1_Test.pak",
    "HalfOpenWorldV1/JOGAR-V1.cmd",
    "HalfOpenWorldV1/README.md",
    "HalfOpenWorldV1/CONTINUAR-IA.md",
    "HalfOpenWorldV1/GUIA-PARA-OUTRA-IA.md",
    "HalfOpenWorldV1/STATUS-RETOMADA.md",
    "HalfOpenWorldV1/half_sword_map_pak.txt",
    "HalfOpenWorldV1/HalfOpenWorldV1.uproject",
    "HalfOpenWorldV1/Config/",
    "HalfOpenWorldV1/Scripts/",
)


def sync_safe_relative(raw_rel: str) -> str | None:
    """Normalize a repo-relative path; reject traversal / anything off-list."""
    raw_rel = raw_rel.replace("\\", "/").lstrip("/")
    if not raw_rel or ".." in raw_rel.split("/") or "\x00" in raw_rel:
        return None
    candidate = PurePosixPath(raw_rel)
    candidate_str = str(candidate)
    if any(candidate_str.startswith(excluded) for excluded in SYNC_EXCLUDE_PREFIXES):
        return None
    allowed = any(candidate_str == root or candidate_str.startswith(root) for root in SYNC_ALLOWED_ROOTS)
    if not allowed:
        return None
    if candidate.suffix not in {".lua", ".py", ".cmd", ".md", ".txt", ".pak", ".json", ".ini", ".ps1", ".uproject"}:
        return None
    parts = candidate.parts
    if any(part in {"", ".", ".."} for part in parts):
        return None
    return candidate_str


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


def append_chat(path: Path, sender: str, text: str) -> None:
    """Append one incoming chat line; the local AI/user polls this file."""
    try:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(f"[{time.strftime('%H:%M:%S')}] {sender}: {text}\n")
    except OSError:
        pass


def write_session(path: Path, session: str, role: str, room: str, players: int) -> None:
    """Publish a short-lived accepted-room lease for the UE4SS bridge.

    The game must never trust a left-over role/control file.  It may only act
    while this lease is fresh and belongs to the current relay session.
    """
    expiry = int(time.time()) + LEASE_SECONDS
    line = f"v2 {session} {role} {room} {expiry} {players} openworld-v1\n"
    write_bridge_text(path, line)


# ---------------------------------------------------------------------------
# Live file sync (v2): every change in the repo pushes through the relay and
# is applied on the other side automatically. No git involved after the first
# `git pull` that brings this file itself.
# ---------------------------------------------------------------------------

def allowed_watch_snapshot(watch_dir: Path) -> dict[str, tuple[int, int]]:
    """rel -> (mtime_ns, size) for every syncable file under watch_dir."""
    snapshot: dict[str, tuple[int, int]] = {}
    try:
        for path in watch_dir.rglob("*"):
            if not path.is_file():
                continue
            try:
                rel = path.relative_to(watch_dir)
            except ValueError:
                continue
            if not sync_safe_relative(str(rel).replace("\\", "/")):
                continue
            try:
                stat = path.stat()
            except OSError:
                continue
            if stat.st_size <= 700_000:
                snapshot[str(rel).replace("\\", "/")] = (stat.st_mtime_ns, stat.st_size)
    except OSError:
        pass
    return snapshot


def build_sync_payload(watch_dir: Path, rel: str) -> str | None:
    """Read one allowed file and return a ready-to-send file_sync frame."""
    source = watch_dir.joinpath(*PurePosixPath(rel).parts)
    try:
        data = source.read_bytes()
    except OSError:
        return None
    if len(data) > 700_000:
        return None
    payload = json.dumps(
        {"type": "file_sync", "path": rel, "encoding": "base64", "content": base64.b64encode(data).decode("ascii")},
        separators=(",", ":"),
    )
    return payload if len(payload) <= 900_000 else None


async def resend_all(ws, watch_dir: Path) -> None:
    """Full repo push triggered by a client's sync_request (late joiner)."""
    if not watch_dir:
        return
    for rel in sorted(allowed_watch_snapshot(watch_dir)):
        payload = build_sync_payload(watch_dir, rel)
        if payload:
            try:
                await ws.send(payload)
            except Exception:
                return


async def sync_loop(ws, watch_dir: Path, chat_file: Path) -> None:
    """Watch ALLOWED repo files; any edit is base64-pushed over the room."""
    previous: dict[str, tuple[int, int]] = {}
    while True:
        current = allowed_watch_snapshot(watch_dir)
        changed = [rel for rel, key in current.items() if previous.get(rel) != key]
        for rel in sorted(changed):
            payload = build_sync_payload(watch_dir, rel)
            if payload:
                try:
                    await ws.send(payload)
                    append_chat(chat_file, "SYNC", f"enviado: {rel} ({len(payload)}b frame)")
                    logging.info("file_sync sent: %s", rel)
                except Exception as exc:
                    logging.warning("file_sync send failed for %s: %s", rel, exc)
        previous = current
        await asyncio.sleep(0.8)


def apply_file_sync(dest: Path, game_dir: Path | None, rel: str, data: bytes) -> str:
    """Write a received file into the repo AND the live game mods. Returns a summary."""
    try:
        target = dest.joinpath(*PurePosixPath(rel).parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(target.suffix + ".tmp")
        for _ in range(4):
            try:
                tmp.write_bytes(data)
                tmp.replace(target)
                break
            except PermissionError:
                time.sleep(0.01)
            except OSError as exc:
                return f"ERRO gravando {rel}: {exc}"
        else:
            return f"ERRO gravando {rel}: arquivo bloqueado"
        if game_dir:
            mapping = {
                "HalfSwordOnlineRealMod/Scripts/main.lua": game_dir / "HalfswordUE5/Binaries/Win64/ue4ss/Mods/HalfSwordOnlineRealMod/Scripts/main.lua",
                "HalfOpenWorldV1/HalfSwordBridge/Scripts/main.lua": game_dir / "HalfswordUE5/Binaries/Win64/ue4ss/Mods/HalfSwordBridge/Scripts/main.lua",
                "HalfOpenWorldV1/Z_HalfOpenWorldV1_Test.pak": game_dir / "HalfswordUE5/Content/Paks/Z_HalfOpenWorldV1_Test.pak",
            }
            game_target = mapping.get(rel)
            if game_target:
                try:
                    game_target.parent.mkdir(parents=True, exist_ok=True)
                    game_tmp = game_target.with_suffix(game_target.suffix + ".tmp")
                    game_tmp.write_bytes(data)
                    game_tmp.replace(game_target)
                except OSError as exc:
                    return f"{rel} gravado no repo, mas ERRO no jogo: {exc}"
        note = f"OK: {rel} ({len(data)} bytes)"
        if game_dir and rel in mapping:
            note += " [aplicado no jogo]"
        return note
    except OSError as exc:
        return f"ERRO: {rel}: {exc}"


async def send_loop(ws, outbound: Path, control: Path, chat_send: Path) -> None:
    previous = ""
    previous_control = ""
    previous_chat = ""
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
        try:
            raw_chat = chat_send.read_text(encoding="utf-8", errors="replace")
        except OSError:
            raw_chat = ""
        if raw_chat.strip() and raw_chat != previous_chat:
            line = raw_chat.strip().splitlines()[0]
            if line:
                await ws.send(json.dumps({"type": "chat", "text": line[:400]}, separators=(",", ":")))
                previous_chat = raw_chat
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
    chat_file, chat_send = bridge / "mp_chat.txt", bridge / "mp_chat_send.txt"
    sync_log = bridge / "mp_sync_log.txt"
    watch_dir = Path(args.sync_watch).expanduser() if args.sync_watch else None
    sync_dest = Path(args.sync_dest).expanduser() if args.sync_dest else None
    game_dir = Path(args.game_dir).expanduser() if args.game_dir else None
    # A reopened host must not see the last session's ghost avatar while alone.
    clear_file(inbound)
    for path in (game_control, role_file, session_file, world_control, room_status):
        clear_file(path)
    while True:
        try:
            async with connect(args.server, max_size=1_048_576, ping_interval=15, ping_timeout=15) as ws:
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
                sender = asyncio.create_task(send_loop(ws, outbound, control, chat_send))
                lease = asyncio.create_task(lease_loop(session_file, session, args, state))
                syncer = asyncio.create_task(sync_loop(ws, watch_dir, chat_file)) if watch_dir else None
                # Late-join / reconnect: ask the author side for the full repo.
                if sync_dest:
                    try:
                        await ws.send(json.dumps({"type": "sync_request"}, separators=(",", ":")))
                    except Exception:
                        pass
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
                        elif message.get("type") == "chat":
                            append_chat(chat_file, str(message.get("from", "?")), str(message.get("text", "")))
                            logging.info("[CHAT] %s: %s", message.get("from"), message.get("text"))
                        elif message.get("type") == "file_sync":
                            if not sync_dest:
                                continue
                            rel = sync_safe_relative(str(message.get("path", "")))
                            if not rel:
                                append_chat(chat_file, "SYNC", f"recusado (fora da allowlist): {message.get('path')}")
                                continue
                            try:
                                raw_bytes = base64.b64decode(str(message.get("content", "")))
                            except Exception:
                                continue
                            result = apply_file_sync(sync_dest, game_dir, rel, raw_bytes)
                            append_chat(sync_log, "SYNC", result)
                            append_chat(chat_file, "SYNC", result)
                            logging.info("file_sync received: %s", result)
                            # ACK back to the host so the author sees the result live.
                            try:
                                await ws.send(json.dumps({"type": "chat", "text": "[SYNC-ACK] " + result[:300]}, separators=(",", ":")))
                            except Exception:
                                pass
                        elif message.get("type") == "sync_request" and watch_dir:
                            await resend_all(ws, watch_dir)
                        elif message.get("type") == "error":
                            logging.warning("relay error: %s", message.get("code"))
                finally:
                    sender.cancel()
                    lease.cancel()
                    if syncer:
                        syncer.cancel()
                    await asyncio.gather(sender, lease, *((syncer,) if syncer else ()), return_exceptions=True)
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
    parser.add_argument("--sync-watch", help="Dir do repo local: mudanças são empurradas ao vivo (lado que edita)")
    parser.add_argument("--sync-dest", help="Dir do repo local onde receber updates automaticamente (lado que aplica)")
    parser.add_argument("--game-dir", help="Raiz do Half Sword (ex.: C:\\Program Files (x86)\\Steam\\steamapps\\common\\Half Sword); aplica mods no jogo ao receber")
    parser.add_argument("--bridge", default=str(Path.home() / "AppData/Local/HalfSwordUE5/Saved/HalfSwordOnlineReal"))
    options = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    asyncio.run(run(options))
