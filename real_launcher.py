"""Launcher do Half Online — assinado: shokk."""
from __future__ import annotations

import asyncio
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

    import importlib.util
    spec = importlib.util.spec_from_file_location("relay_server", ROOT / "relay_server.py")
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    relay = mod.Relay()

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
        self.geometry("760x560")
        self.minsize(700, 520)
        self.configure(bg="#11151d")

        self.name   = tk.StringVar(value="Jogador")
        self.room   = tk.StringVar(value="duelo")
        self.server = tk.StringVar()
        self.status = tk.StringVar(value="Pronto.")
        self.room_status = tk.StringVar(value="Sala: aguardando host")

        self.room_locked = False
        self.tunnel_url  = ""
        self.agent:  subprocess.Popen | None = None
        self.tunnel: subprocess.Popen | None = None

        self._style()
        self._build()
        self.after(500, self._poll_room_status)
        self.protocol("WM_DELETE_WINDOW", self.close)
        threading.Thread(target=self._auto_update, daemon=True).start()

    # ── estilos ───────────────────────────────────────────────────────────────

    def _style(self) -> None:
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure(".", background="#11151d", foreground="#e8edf6", font=("Segoe UI", 10))
        s.configure("TFrame",       background="#11151d")
        s.configure("Card.TFrame",  background="#1b2431")
        s.configure("Title.TLabel", background="#11151d", foreground="#e7b953",
                    font=("Segoe UI Semibold", 21))
        s.configure("Card.TLabel",  background="#1b2431", foreground="#e8edf6")
        s.configure("Hint.TLabel",  background="#1b2431", foreground="#a9b6c7")
        s.configure("TEntry",       fieldbackground="#0f141d", foreground="#e8edf6",
                    insertcolor="#e8edf6")
        s.configure("Accent.TButton", background="#d08d31", foreground="#10141a",
                    font=("Segoe UI Semibold", 10), padding=(14, 9))
        s.map("Accent.TButton", background=[("active", "#e8af57")])
        s.configure("TButton", background="#2c3a4e", foreground="#edf2fa", padding=(12, 8))

    # ── layout ────────────────────────────────────────────────────────────────

    def _build(self) -> None:
        root = ttk.Frame(self, padding=22)
        root.pack(fill="both", expand=True)

        ttk.Label(root, text="HALF SWORD ONLINE", style="Title.TLabel").pack(anchor="w")
        ttk.Label(root,
                  text="Cada jogador abre sua propria Steam e copia do jogo.",
                  style="Hint.TLabel").pack(anchor="w", pady=(2, 16))

        # ── campos ──
        cfg = ttk.Frame(root, style="Card.TFrame", padding=16)
        cfg.pack(fill="x")
        ttk.Label(cfg, text="Dados da sala", style="Card.TLabel",
                  font=("Segoe UI Semibold", 13)).grid(row=0, column=0, columnspan=3,
                                                        sticky="w", pady=(0, 8))
        for col, txt in enumerate(("Seu nome", "Nome da sala", "URL do host")):
            ttk.Label(cfg, text=txt, style="Hint.TLabel").grid(row=1, column=col,
                                                                sticky="w", padx=(0 if col == 0 else 10, 0))
        ttk.Entry(cfg, textvariable=self.name  ).grid(row=2, column=0, sticky="ew")
        ttk.Entry(cfg, textvariable=self.room  ).grid(row=2, column=1, sticky="ew", padx=(10, 0))
        ttk.Entry(cfg, textvariable=self.server).grid(row=2, column=2, sticky="ew", padx=(10, 0))
        cfg.columnconfigure(0, weight=1)
        cfg.columnconfigure(1, weight=1)
        cfg.columnconfigure(2, weight=2)

        # ── hospedar ──
        host = ttk.Frame(root, style="Card.TFrame", padding=16)
        host.pack(fill="x", pady=(12, 0))
        ttk.Label(host, text="Eu vou hospedar", style="Card.TLabel",
                  font=("Segoe UI Semibold", 13)).pack(anchor="w")
        ttk.Label(host, text="Cria um link publico. Envie o link para seu amigo.",
                  style="Hint.TLabel").pack(anchor="w", pady=(4, 10))

        row1 = ttk.Frame(host, style="Card.TFrame"); row1.pack(fill="x")
        ttk.Button(row1, text="Hospedar sala", style="Accent.TButton",
                   command=self.host_room).pack(side="left")
        ttk.Button(row1, text="Copiar link",
                   command=self.copy_address).pack(side="left", padx=8)
        self.host_address = ttk.Label(row1, text="", style="Hint.TLabel", wraplength=400)
        self.host_address.pack(side="left", padx=6)

        row2 = ttk.Frame(host, style="Card.TFrame"); row2.pack(fill="x", pady=(8, 0))
        ttk.Label(row2, textvariable=self.room_status, style="Hint.TLabel").pack(side="left")
        self.lock_button = ttk.Button(row2, text="Trancar sala",
                                      command=self.toggle_lock, state="disabled")
        self.lock_button.pack(side="right")

        ttk.Label(host, text="Avatar do amigo so aparece quando ele entrar na sala.",
                  style="Hint.TLabel").pack(anchor="w", pady=(8, 0))

        # ── entrar ──
        cli = ttk.Frame(root, style="Card.TFrame", padding=16)
        cli.pack(fill="x", pady=(12, 0))
        ttk.Label(cli, text="Eu vou entrar", style="Card.TLabel",
                  font=("Segoe UI Semibold", 13)).pack(anchor="w")
        ttk.Label(cli, text="Cole o link que o host enviou e clique Entrar na sala.",
                  style="Hint.TLabel").pack(anchor="w", pady=(4, 10))
        row3 = ttk.Frame(cli, style="Card.TFrame"); row3.pack(fill="x")
        ttk.Button(row3, text="Entrar na sala", style="Accent.TButton",
                   command=self.join_room).pack(side="left")
        ttk.Button(row3, text="Abrir Half Sword",
                   command=self.launch_game).pack(side="left", padx=8)

        # ── rodape ──
        bot = ttk.Frame(root); bot.pack(fill="x", pady=(18, 0))
        ttk.Label(bot, textvariable=self.status).pack(side="left")
        ttk.Button(bot, text="Parar conexao", command=self.stop).pack(side="right")
        ttk.Label(root, text="assinado: shokk", style="Title.TLabel",
                  font=("Segoe UI Semibold", 10)).pack(anchor="e", pady=(6, 0))

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

    def _validate(self, need_server: bool) -> tuple[str, str, str] | None:
        name    = self.name.get().strip()
        room    = self.room.get().strip()
        address = self.server.get().strip()
        if not name or not room:
            messagebox.showwarning("Dados incompletos", "Informe seu nome e a sala.")
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
                        ws  = url.replace("https://", "wss://")
                        self.agent = self._spawn(
                            ["peer_agent.py", "--server", ws,
                             "--room", room, "--name", name, "--role", "host"],
                            "peer-host.log",
                        )
                        def _ui(u=url, n=name):
                            self.host_address.config(text=u)
                            self.server.set(u)
                            self.lock_button.config(state="normal")
                            self.room_status.set(f"Sala aberta — {n}")
                            self.status.set("Link criado! Envie para seu amigo.")
                        self.after(0, _ui)
                        return

            self.after(0, lambda: self.status.set(
                "Erro ao criar link. Veja logs/tunnel.log"))

        threading.Thread(target=_bg, daemon=True).start()

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
             "--room", room, "--name", name, "--role", "client"],
            "peer-client.log",
        )
        self.lock_button.config(state="disabled")
        self.status.set("Conectando... O host precisa estar com a sala aberta.")

    def toggle_lock(self) -> None:
        BRIDGE_DIR.mkdir(parents=True, exist_ok=True)
        cmd = "lock off" if self.room_locked else "lock on"
        (BRIDGE_DIR / "mp_control.txt").write_text(cmd + "\n", encoding="utf-8")
        self.status.set("Comando enviado.")

    def _poll_room_status(self) -> None:
        import json
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

    def close(self) -> None:
        self.stop()
        self.destroy()


if __name__ == "__main__":
    RealLauncher().mainloop()