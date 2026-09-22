"""Launcher do Half Online — assinado: shokk."""
from __future__ import annotations

import asyncio
import json
import os
import re
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

ROOT   = Path(__file__).resolve().parent
PYTHON = Path(sys.executable)
LOG_DIR     = ROOT / "logs"
RELAY_PORT  = 8790
BRIDGE_DIR  = Path(os.environ.get("LOCALAPPDATA", ".")) / "HalfSwordUE5" / "Saved" / "HalfSwordOnlineReal"
TUNNEL_RE   = re.compile(r"https://[a-zA-Z0-9\-]+\.trycloudflare\.com")

CLOUDFLARED_CANDIDATES = [
    ROOT / "cloudflared.exe",
    ROOT / "bin" / "cloudflared.exe",
    Path(r"C:\Users\shokk123\Desktop\cloudflared.exe"),
    Path(os.environ.get("LOCALAPPDATA", ".")) / "cloudflared.exe",
]


def find_cloudflared() -> Path | None:
    for p in CLOUDFLARED_CANDIDATES:
        if p.exists():
            return p
    for name in ("cloudflared.exe", "cloudflared"):
        try:
            r = subprocess.run(["where", name], capture_output=True, text=True, timeout=3,
                               creationflags=subprocess.CREATE_NO_WINDOW)
            if r.returncode == 0 and r.stdout.strip():
                return Path(r.stdout.strip().splitlines()[0])
        except Exception:
            pass
    return None


def port_open(port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(0.3)
        return s.connect_ex(("127.0.0.1", port)) == 0


# ─── Relay in-process ────────────────────────────────────────────────────────

_relay_thread: threading.Thread | None = None
_relay_loop:   asyncio.AbstractEventLoop | None = None


def start_relay_inprocess() -> bool:
    """Sobe o relay_server dentro deste processo. Retorna True quando a porta abre."""
    global _relay_thread, _relay_loop

    if port_open(RELAY_PORT):
        return True

    # Import normal: no Python 3.14, dataclasses precisam encontrar o modulo
    # registrado em sys.modules durante a criacao das classes.
    from relay_server import Relay
    relay = Relay()

    def _run():
        global _relay_loop
        from websockets.asyncio.server import serve as ws_serve

        async def _serve():
            async with ws_serve(
                relay.handler, "0.0.0.0", RELAY_PORT,
                max_size=2048, ping_interval=15, ping_timeout=15,
                reuse_address=True,
            ):
                await asyncio.Future()

        _relay_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_relay_loop)
        _relay_loop.run_until_complete(_serve())

    _relay_thread = threading.Thread(target=_run, daemon=True, name="relay")
    _relay_thread.start()

    for _ in range(30):          # ate 6 s
        time.sleep(0.2)
        if port_open(RELAY_PORT):
            return True
    return False


# ─── UI ──────────────────────────────────────────────────────────────────────

class RealLauncher(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Half Sword Online")
        self.geometry("1080x660")
        # The launcher is the external admin surface; keep it available above
        # the windowed game so host actions do not depend on keyboard focus.
        self.attributes("-topmost", True)
        self.minsize(920, 600)
        self.configure(bg="#120f0f")

        self.name   = tk.StringVar(value="Jogador")
        self.room   = tk.StringVar(value="duelo")
        self.server = tk.StringVar()
        self.status = tk.StringVar(value="Pronto.")
        self.room_status = tk.StringVar(value="Nenhuma arena ativa")

        self.room_locked = False
        self.tunnel_url  = ""
        self.agent:  subprocess.Popen | None = None
        self.tunnel: subprocess.Popen | None = None
        # Convites sao mantidos apenas durante a sessao. Uma lista global real
        # depende do servidor-diretorio; historico local nao e sala ativa.
        self.known_rooms: list[dict[str, str]] = []

        self._style()
        self._build()
        self.after(500, self._poll_room_status)
        self.protocol("WM_DELETE_WINDOW", self.close)
        threading.Thread(target=self._auto_update, daemon=True).start()

    # ── estilos ───────────────────────────────────────────────────────────────

    def _style(self) -> None:
        s = ttk.Style(self)
        s.theme_use("clam")
        # Paleta "forja real": escuro quente, metal envelhecido e pergaminho.
        s.configure(".", background="#120f0f", foreground="#eee5d2", font=("Segoe UI", 10))
        s.configure("TFrame",        background="#120f0f")
        s.configure("Card.TFrame",   background="#211a1a")
        s.configure("Title.TLabel",  background="#120f0f", foreground="#d8b26a",
                    font=("Georgia", 24, "bold"))
        s.configure("Card.TLabel",   background="#211a1a", foreground="#f4ecda")
        s.configure("Hint.TLabel",   background="#211a1a", foreground="#b8ac99")
        s.configure("Status.TLabel", background="#120f0f", foreground="#b8ac99")
        s.configure("TEntry", fieldbackground="#171213", foreground="#f4ecda",
                    insertcolor="#d8b26a", bordercolor="#5b4937", lightcolor="#5b4937")
        s.configure("Accent.TButton", background="#a47735", foreground="#160f09",
                    font=("Segoe UI Semibold", 10), padding=(15, 10))
        s.map("Accent.TButton", background=[("active", "#cfaa62"), ("pressed", "#805927")])
        s.configure("TButton", background="#3a2929", foreground="#f1e7d3", padding=(12, 9))
        s.map("TButton", background=[("active", "#563737"), ("pressed", "#2a1b1b")])
        s.configure("Rooms.Treeview", background="#171213", fieldbackground="#171213",
                    foreground="#eadfca", rowheight=40, bordercolor="#4d3a2f")
        s.map("Rooms.Treeview", background=[("selected", "#684127")],
              foreground=[("selected", "#fff8e9")])
        s.configure("Rooms.Treeview.Heading", background="#30231f", foreground="#d8b26a",
                    font=("Segoe UI Semibold", 9), relief="flat")

    # ── layout ────────────────────────────────────────────────────────────────

    def _build(self) -> None:
        root = ttk.Frame(self, padding=(26, 22))
        root.pack(fill="both", expand=True)
        header = ttk.Frame(root)
        header.pack(fill="x", pady=(0, 18))
        ttk.Label(header, text="HALF ONLINE", style="Title.TLabel").pack(side="left")
        ttk.Label(header, text="PRIVATE ARENAS  |  v2.1", style="Status.TLabel",
                  font=("Segoe UI Semibold", 10)).pack(side="left", padx=(12, 0), pady=(8, 0))
        ttk.Button(header, text="Abrir Half Sword", command=self.launch_game).pack(side="right")
        ttk.Label(header, text="Painel externo ativo", style="Status.TLabel").pack(side="right", padx=14)

        body = ttk.Frame(root)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=4, minsize=390)
        body.columnconfigure(1, weight=6, minsize=470)
        body.rowconfigure(0, weight=1)

        left = ttk.Frame(body, style="Card.TFrame", padding=18)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        ttk.Label(left, text="COMANDO DA ARENA", style="Card.TLabel",
                  font=("Segoe UI Semibold", 13)).pack(anchor="w")
        ttk.Label(left, text="Forje uma arena privada ou entre por convite.",
                  style="Hint.TLabel").pack(anchor="w", pady=(3, 16))

        self._field(left, "SEU NOME", self.name)
        self._field(left, "NOME DA SALA", self.room)
        self._field(left, "LINK DO HOST", self.server)

        actions = ttk.Frame(left, style="Card.TFrame")
        actions.pack(fill="x", pady=(5, 12))
        ttk.Button(actions, text="CRIAR SALA", style="Accent.TButton",
                   command=self.host_room).pack(side="left", fill="x", expand=True)
        ttk.Button(actions, text="ENTRAR", command=self.join_room).pack(side="left", padx=(8, 0))
        ttk.Button(left, text="Copiar link da minha sala", command=self.copy_address).pack(anchor="w")

        active = ttk.Frame(left, style="Card.TFrame", padding=12)
        active.pack(fill="x", pady=(16, 0))
        ttk.Label(active, text="ARENA ATIVA", style="Card.TLabel",
                  font=("Segoe UI Semibold", 10)).pack(anchor="w")
        ttk.Label(active, textvariable=self.room_status, style="Hint.TLabel",
                  wraplength=330).pack(anchor="w", pady=(5, 0))
        self.host_address = ttk.Label(active, text="", style="Hint.TLabel", wraplength=330)
        self.host_address.pack(anchor="w", pady=(4, 8))
        self.lock_button = ttk.Button(active, text="Trancar sala",
                                      command=self.toggle_lock, state="disabled")
        self.lock_button.pack(anchor="w")
        admin_row = ttk.Frame(active, style="Card.TFrame")
        admin_row.pack(fill="x", pady=(10, 0))
        ttk.Button(admin_row, text="Spawn bot", command=lambda: self.send_game_admin("game spawn_bot")).pack(side="left")
        ttk.Button(admin_row, text="Spawn item", command=lambda: self.send_game_admin("game spawn_item")).pack(side="left", padx=5)
        ttk.Button(admin_row, text="Limpar", command=lambda: self.send_game_admin("game clear_spawns")).pack(side="left")

        right = ttk.Frame(body, style="Card.TFrame", padding=18)
        right.grid(row=0, column=1, sticky="nsew")
        top = ttk.Frame(right, style="Card.TFrame")
        top.pack(fill="x")
        ttk.Label(top, text="ARENAS DISPONÍVEIS", style="Card.TLabel", font=("Segoe UI Semibold", 13)).pack(side="left")
        ttk.Button(top, text="Atualizar", command=self.refresh_rooms).pack(side="right")
        ttk.Label(right, text="Sessão atual e convites guardados neste PC.",
                  style="Hint.TLabel").pack(anchor="w", pady=(3, 14))

        table = ttk.Frame(right, style="Card.TFrame")
        table.pack(fill="both", expand=True)
        self.rooms_view = ttk.Treeview(table, style="Rooms.Treeview", show="headings",
                                       columns=("room", "owner", "state"), selectmode="browse")
        self.rooms_view.heading("room", text="ARENA")
        self.rooms_view.heading("owner", text="HOST / CONVITE")
        self.rooms_view.heading("state", text="STATUS")
        self.rooms_view.column("room", width=145, minwidth=110, anchor="w")
        self.rooms_view.column("owner", width=245, minwidth=160, anchor="w")
        self.rooms_view.column("state", width=110, minwidth=90, anchor="center")
        scroll = ttk.Scrollbar(table, orient="vertical", command=self.rooms_view.yview)
        self.rooms_view.configure(yscrollcommand=scroll.set)
        self.rooms_view.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.rooms_view.bind("<Double-1>", lambda _event: self.join_selected_room())
        row = ttk.Frame(right, style="Card.TFrame")
        row.pack(fill="x", pady=(14, 0))
        ttk.Button(row, text="Entrar na sala selecionada", style="Accent.TButton",
                   command=self.join_selected_room).pack(side="left")
        ttk.Button(row, text="Remover convite", command=self.remove_selected_room).pack(side="left", padx=8)

        footer = ttk.Frame(root)
        footer.pack(fill="x", pady=(15, 0))
        ttk.Label(footer, textvariable=self.status, style="Status.TLabel").pack(side="left")
        ttk.Button(footer, text="Parar conexao", command=self.stop).pack(side="right")
        ttk.Label(footer, text="assinado: shokk", style="Status.TLabel").pack(side="right", padx=16)
        self.refresh_rooms()

    def _field(self, parent: ttk.Frame, caption: str, variable: tk.StringVar) -> None:
        ttk.Label(parent, text=caption, style="Hint.TLabel",
                  font=("Segoe UI Semibold", 8)).pack(anchor="w", pady=(0, 4))
        ttk.Entry(parent, textvariable=variable).pack(fill="x", pady=(0, 12))

    def _load_known_rooms(self) -> list[dict[str, str]]:
        return []

    def _save_known_rooms(self) -> None:
        return

    def remember_room(self, room: str, url: str, owner: str, state: str = "CONVITE") -> None:
        url = url.strip()
        if not url:
            return
        item = {"room": room, "url": url, "owner": owner, "state": state}
        self.known_rooms = [saved for saved in self.known_rooms if saved.get("url") != url]
        self.known_rooms.insert(0, item)
        self._save_known_rooms()
        self.refresh_rooms()

    def refresh_rooms(self) -> None:
        if not hasattr(self, "rooms_view"):
            return
        self.rooms_view.delete(*self.rooms_view.get_children())
        if self.tunnel_url:
            self.rooms_view.insert("", "end", values=(self.room.get().strip() or "sala", "Voce", "ATIVA"),
                                   tags=("active",))
        for item in self.known_rooms:
            state = item.get("state", "CONVITE")
            self.rooms_view.insert("", "end", values=(item["room"], item.get("owner", "Convite"), state),
                                   tags=(item["url"],))
        self.rooms_view.tag_configure("active", foreground="#f2c768")

    def join_selected_room(self) -> None:
        selected = self.rooms_view.selection()
        if not selected:
            messagebox.showinfo("Salas", "Selecione uma sala primeiro.")
            return
        values = self.rooms_view.item(selected[0], "values")
        if len(values) < 3:
            return
        if values[2] == "ATIVA":
            self.status.set("Esta e a sua sala ativa. Copie o link para convidar um amigo.")
            return
        for item in self.known_rooms:
            if item.get("room") == values[0] and item.get("owner", "Convite") == values[1]:
                self.room.set(item["room"])
                self.server.set(item["url"])
                self.join_room()
                return

    def remove_selected_room(self) -> None:
        selected = self.rooms_view.selection()
        if not selected:
            return
        values = self.rooms_view.item(selected[0], "values")
        if len(values) < 3 or values[2] == "ATIVA":
            return
        self.known_rooms = [item for item in self.known_rooms
                            if not (item.get("room") == values[0] and item.get("owner", "Convite") == values[1])]
        self._save_known_rooms()
        self.refresh_rooms()

    # ── auto-update ───────────────────────────────────────────────────────────

    def _auto_update(self) -> None:
        if not (ROOT / ".git").exists():
            return
        try:
            r = subprocess.run(
                ["git", "-C", str(ROOT), "pull", "--ff-only"],
                capture_output=True, text=True, timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            out = r.stdout.strip()
            if r.returncode == 0 and "Already up to date" not in out and out:
                self.after(0, lambda: self.status.set(
                    "Launcher atualizado! Reinicie se necessario."))
        except Exception:
            pass

    # ── acoes ─────────────────────────────────────────────────────────────────

    def _spawn(self, args: list[str], log_name: str) -> subprocess.Popen:
        LOG_DIR.mkdir(exist_ok=True)
        log = (LOG_DIR / log_name).open("ab")
        return subprocess.Popen(
            [str(PYTHON), *args],
            cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

    def _clear_bridge_session(self) -> None:
        """Remove only the handshake state produced by this launcher."""
        BRIDGE_DIR.mkdir(parents=True, exist_ok=True)
        for name in ("mp_inbound.txt", "mp_session.txt", "mp_openworld_control.txt",
                     "mp_role.txt", "mp_room_status.json"):
            try:
                (BRIDGE_DIR / name).unlink(missing_ok=True)
            except OSError:
                pass

    def _launch_when_accepted(self, role: str, room: str) -> None:
        """Launch only after the relay grants a fresh local session lease."""
        def _wait() -> None:
            deadline = time.time() + 15
            session_file = BRIDGE_DIR / "mp_session.txt"
            while time.time() < deadline:
                try:
                    fields = session_file.read_text(encoding="utf-8").strip().split()
                    if (len(fields) == 7 and fields[0] == "v2" and fields[2] == role
                            and fields[3] == room
                            and int(fields[4]) >= int(time.time())):
                        self.after(0, lambda: (self.status.set("Sala confirmada. Abrindo Half Sword..."),
                                               self.launch_game()))
                        return
                except (OSError, ValueError):
                    pass
                time.sleep(0.2)
            self.after(0, lambda: self.status.set(
                "A sala nao foi confirmada. Confira link, nome da sala e se o host esta online."))
        threading.Thread(target=_wait, daemon=True).start()

    def _validate(self, need_server: bool) -> tuple[str, str, str] | None:
        name    = self.name.get().strip()
        room    = self.room.get().strip()
        address = self.server.get().strip()
        if not name or not room:
            messagebox.showwarning("Dados incompletos", "Informe seu nome e a sala.")
            return None
        if any(char.isspace() for char in room) or len(room) > 32:
            messagebox.showwarning("Nome de sala invalido",
                                   "Use uma palavra sem espacos, com no maximo 32 caracteres.")
            return None
        if len(name) > 24:
            messagebox.showwarning("Nome invalido", "Seu nome pode ter no maximo 24 caracteres.")
            return None
        if need_server and not address:
            messagebox.showwarning("URL ausente", "Cole o link que o host enviou.")
            return None
        return name, room, address

    def host_room(self) -> None:
        values = self._validate(False)
        if not values:
            return
        name, room, _ = values

        # Mata processos antigos
        for exe in ("HalfSwordUE5-Win64-Shipping.exe", "HalfSwordUE5.exe"):
            subprocess.run(["taskkill", "/F", "/IM", exe], capture_output=True,
                           creationflags=subprocess.CREATE_NO_WINDOW)
        self.stop()
        self._clear_bridge_session()

        self.status.set("Iniciando relay...")
        self.update_idletasks()

        def _bg():
            # 1) sobe relay
            ok = start_relay_inprocess()
            if not ok:
                self.after(0, lambda: self.status.set(
                    "Erro: relay nao iniciou. Tente novamente."))
                return

            # 2) acha cloudflared
            cf = find_cloudflared()
            if not cf:
                self.after(0, lambda: self.status.set(
                    "Erro: cloudflared.exe nao encontrado. "
                    "Coloque-o na pasta do projeto ou na Desktop."))
                return

            self.after(0, lambda: self.status.set("Criando link publico... aguarde"))

            # 3) sobe tunnel capturando stdout+stderr
            LOG_DIR.mkdir(exist_ok=True)
            log_path = LOG_DIR / "tunnel.log"
            proc = subprocess.Popen(
                [str(cf), "tunnel", "--url", f"http://127.0.0.1:{RELAY_PORT}"],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            self.tunnel = proc

            # 4) le output ate achar a URL
            with log_path.open("w", encoding="utf-8", errors="replace") as log:
                for raw in proc.stdout:
                    line = raw.decode("utf-8", errors="replace")
                    log.write(line)
                    log.flush()
                    m = TUNNEL_RE.search(line)
                    if m:
                        url = m.group(0)
                        self.tunnel_url = url
                        # O host registra a sala diretamente no relay local.
                        # O link publico e usado apenas pelo amigo; tentar usa-lo
                        # aqui falha enquanto o DNS do Quick Tunnel ainda propaga.
                        ws = f"ws://127.0.0.1:{RELAY_PORT}"
                        self.agent = self._spawn(
                            ["peer_agent.py", "--server", ws,
                             "--room", room, "--name", name, "--role", "host",
                             "--openworld"],
                            "peer-host.log",
                        )
                        def _ui(u=url, n=name):
                            self.host_address.config(text=u)
                            self.server.set(u)
                            self.lock_button.config(state="normal")
                            self.room_status.set(f"Sala aberta — {n}")
                            self.status.set("Link criado! Envie para seu amigo.")
                            self.refresh_rooms()
                            self._launch_when_accepted("host", room)
                        self.after(0, _ui)
                        return

            self.after(0, lambda: self.status.set(
                "Erro ao criar link. Veja logs/tunnel.log"))

        def _bg_safe():
            try:
                _bg()
            except Exception as exc:
                LOG_DIR.mkdir(exist_ok=True)
                with (LOG_DIR / "launcher-error.log").open("a", encoding="utf-8") as log:
                    log.write(f"host_room: {type(exc).__name__}: {exc}\n")
                self.after(0, lambda err=str(exc): self.status.set(
                    f"Falha ao criar sala: {err}"))

        threading.Thread(target=_bg_safe, daemon=True).start()

    def join_room(self) -> None:
        values = self._validate(True)
        if not values:
            return
        name, room, address = values

        for exe in ("HalfSwordUE5-Win64-Shipping.exe", "HalfSwordUE5.exe"):
            subprocess.run(["taskkill", "/F", "/IM", exe], capture_output=True,
                           creationflags=subprocess.CREATE_NO_WINDOW)
        if self.agent and self.agent.poll() is None:
            self.agent.terminate()
        self._clear_bridge_session()

        # normaliza URL
        if address.startswith("https://"):
            ws = address.replace("https://", "wss://")
        elif address.startswith("http://"):
            ws = address.replace("http://", "ws://")
        elif not address.startswith(("ws://", "wss://")):
            ws = f"ws://{address}:{RELAY_PORT}"
        else:
            ws = address

        self.agent = self._spawn(
            ["peer_agent.py", "--server", ws,
             "--room", room, "--name", name, "--role", "client",
             "--openworld"],
            "peer-client.log",
        )
        self.remember_room(room, address, "Convite", "RECENTE")
        self.lock_button.config(state="disabled")
        self.status.set("Conectando... O host precisa estar com a sala aberta.")
        self._launch_when_accepted("client", room)

    def toggle_lock(self) -> None:
        BRIDGE_DIR.mkdir(parents=True, exist_ok=True)
        cmd = "lock off" if self.room_locked else "lock on"
        (BRIDGE_DIR / "mp_control.txt").write_text(cmd + "\n", encoding="utf-8")
        self.status.set("Comando enviado.")

    def send_game_admin(self, command: str) -> None:
        if not self.agent or self.agent.poll() is not None:
            messagebox.showwarning("Admin", "Crie uma sala antes de usar o painel admin.")
            return
        BRIDGE_DIR.mkdir(parents=True, exist_ok=True)
        # Local host actions go straight to the UE4SS bridge. This avoids
        # keyboard focus issues and does not depend on a remote peer relay.
        (BRIDGE_DIR / "mp_openworld_control.txt").write_text(command + "\n", encoding="utf-8")
        self.status.set("Comando admin enviado.")

    def _poll_room_status(self) -> None:
        if not self.agent or self.agent.poll() is not None:
            self.room_status.set("Nenhuma arena ativa")
            self.after(500, self._poll_room_status)
            return
        status_file = BRIDGE_DIR / "mp_room_status.json"
        try:
            payload = json.loads(status_file.read_text(encoding="utf-8"))
            players = payload.get("players", [])
            self.room_locked = bool(payload.get("locked", False))
            names = ", ".join(str(p.get("name", "?")) for p in players) or "aguardando"
            state = "trancada" if self.room_locked else "aberta"
            self.room_status.set(f"Sala {state} — {len(players)}/2: {names}")
            self.lock_button.config(
                text="Destrancar sala" if self.room_locked else "Trancar sala")
        except Exception:
            pass
        self.after(500, self._poll_room_status)

    def copy_address(self) -> None:
        url = self.tunnel_url or self.server.get()
        if not url:
            messagebox.showwarning("Link", "Crie a sala primeiro.")
            return
        self.clipboard_clear()
        self.clipboard_append(url)
        self.status.set("Link copiado!")

    def launch_game(self) -> None:
        try:
            os.startfile("steam://rungameid/2397300")
        except OSError as e:
            messagebox.showerror("Steam", str(e))

    def stop(self) -> None:
        for p in (self.agent, self.tunnel):
            if p and p.poll() is None:
                p.terminate()
        self.agent  = None
        self.tunnel = None
        self.tunnel_url = ""
        self.status.set("Conexao encerrada.")
        self.room_status.set("Nenhuma arena ativa")
        if hasattr(self, "lock_button"):
            self.lock_button.config(state="disabled")
        try:
            self._clear_bridge_session()
        except OSError:
            pass
        self.refresh_rooms()

    def close(self) -> None:
        self.stop()
        self.destroy()


if __name__ == "__main__":
    RealLauncher().mainloop()
