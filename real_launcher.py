"""Launcher do Half Online para duas instalações independentes — assinado: shokk."""
from __future__ import annotations

import os
import json
import socket
import subprocess
import sys
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

ROOT = Path(sys.executable).resolve().parent.parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
PYTHON = ROOT.parent / "production" / ".venv" / "Scripts" / "python.exe"
LOG_DIR = ROOT / "logs"
RELAY_PORT = 8790
BRIDGE_DIR = Path(os.environ.get("LOCALAPPDATA", ".")) / "HalfSwordUE5" / "Saved" / "HalfSwordOnlineReal"
TAILSCALE_EXES = (
    Path(r"C:\Program Files\Tailscale\tailscale.exe"),
    Path(r"C:\Program Files (x86)\Tailscale\tailscale.exe"),
)


def tailscale_ip() -> str:
    executable = next((candidate for candidate in TAILSCALE_EXES if candidate.exists()), None)
    command = [str(executable)] if executable else ["tailscale"]
    try:
        result = subprocess.run([*command, "ip", "-4"], capture_output=True, text=True, timeout=3,
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().splitlines()[0]
    except (OSError, subprocess.SubprocessError):
        pass
    return ""


def port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(0.25)
        return probe.connect_ex(("127.0.0.1", port)) == 0


class RealLauncher(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Half Sword Online — Multiplayer Real (Fase 1)")
        self.geometry("760x520")
        self.minsize(700, 500)
        self.configure(bg="#11151d")
        self.name = tk.StringVar(value="Jogador")
        self.room = tk.StringVar(value="duelo")
        self.server = tk.StringVar(value=tailscale_ip())
        self.status = tk.StringVar(value="Instale Tailscale nos dois PCs antes de começar.")
        self.room_status = tk.StringVar(value="Sala: aguardando host")
        self.room_locked = False
        self.agent: subprocess.Popen[bytes] | None = None
        self.relay: subprocess.Popen[bytes] | None = None
        self._style()
        self._build()
        self.after(500, self._poll_room_status)
        self.protocol("WM_DELETE_WINDOW", self.close)

    def _style(self) -> None:
        style = ttk.Style(self); style.theme_use("clam")
        style.configure(".", background="#11151d", foreground="#e8edf6", font=("Segoe UI", 10))
        style.configure("TFrame", background="#11151d")
        style.configure("Card.TFrame", background="#1b2431")
        style.configure("Title.TLabel", background="#11151d", foreground="#e7b953", font=("Segoe UI Semibold", 21))
        style.configure("Card.TLabel", background="#1b2431", foreground="#e8edf6")
        style.configure("Hint.TLabel", background="#1b2431", foreground="#a9b6c7")
        style.configure("TEntry", fieldbackground="#0f141d", foreground="#e8edf6", insertcolor="#e8edf6")
        style.configure("Accent.TButton", background="#d08d31", foreground="#10141a", font=("Segoe UI Semibold", 10), padding=(14, 9))
        style.map("Accent.TButton", background=[("active", "#e8af57")])
        style.configure("TButton", background="#2c3a4e", foreground="#edf2fa", padding=(12, 8))

    def _build(self) -> None:
        root = ttk.Frame(self, padding=22); root.pack(fill="both", expand=True)
        ttk.Label(root, text="HALF SWORD ONLINE", style="Title.TLabel").pack(anchor="w")
        ttk.Label(root, text="Fase 1 — cada jogador abre sua própria Steam e sua própria cópia do jogo.").pack(anchor="w", pady=(2, 16))
        settings = ttk.Frame(root, style="Card.TFrame", padding=16); settings.pack(fill="x")
        ttk.Label(settings, text="Dados da sala", style="Card.TLabel", font=("Segoe UI Semibold", 13)).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))
        ttk.Label(settings, text="Seu nome", style="Hint.TLabel").grid(row=1, column=0, sticky="w")
        ttk.Label(settings, text="Nome da sala", style="Hint.TLabel").grid(row=1, column=1, sticky="w", padx=(10, 0))
        ttk.Label(settings, text="IP Tailscale do host", style="Hint.TLabel").grid(row=1, column=2, sticky="w", padx=(10, 0))
        ttk.Entry(settings, textvariable=self.name).grid(row=2, column=0, sticky="ew")
        ttk.Entry(settings, textvariable=self.room).grid(row=2, column=1, sticky="ew", padx=(10, 0))
        ttk.Entry(settings, textvariable=self.server).grid(row=2, column=2, sticky="ew", padx=(10, 0))
        settings.columnconfigure(0, weight=1); settings.columnconfigure(1, weight=1); settings.columnconfigure(2, weight=1)

        host = ttk.Frame(root, style="Card.TFrame", padding=16); host.pack(fill="x", pady=(12, 0))
        ttk.Label(host, text="Eu vou hospedar", style="Card.TLabel", font=("Segoe UI Semibold", 13)).pack(anchor="w")
        ttk.Label(host, text="Inicia o relay privado e conecta seu mod. Envie o IP mostrado para seu amigo.", style="Hint.TLabel").pack(anchor="w", pady=(4, 10))
        line = ttk.Frame(host, style="Card.TFrame"); line.pack(fill="x")
        ttk.Button(line, text="Hospedar sala", style="Accent.TButton", command=self.host_room).pack(side="left")
        ttk.Button(line, text="Copiar endereço", command=self.copy_address).pack(side="left", padx=8)
        self.host_address = ttk.Label(line, text="", style="Hint.TLabel"); self.host_address.pack(side="left", padx=6)
        admin = ttk.Frame(host, style="Card.TFrame"); admin.pack(fill="x", pady=(10, 0))
        ttk.Label(admin, textvariable=self.room_status, style="Hint.TLabel").pack(side="left")
        self.lock_button = ttk.Button(admin, text="Trancar sala", command=self.toggle_lock, state="disabled")
        self.lock_button.pack(side="right")
        self.bot_remove_button = ttk.Button(admin, text="Remover oponente", command=lambda: self.game_command("bot remove"), state="disabled")
        self.bot_remove_button.pack(side="right", padx=(0, 8))
        self.bot_add_button = ttk.Button(admin, text="Adicionar oponente", command=lambda: self.game_command("bot spawn"), state="disabled")
        self.bot_add_button.pack(side="right", padx=(0, 8))
        self.spar_clear_button = ttk.Button(admin, text="Limpar bot do Spar", command=lambda: self.game_command("spar clear"), state="disabled")
        self.spar_clear_button.pack(side="right", padx=(0, 8))
        ttk.Label(host, text="Painel do host: oponente de treino parado; o avatar do amigo só aparece quando ele entrar.", style="Hint.TLabel").pack(anchor="w", pady=(8, 0))

        client = ttk.Frame(root, style="Card.TFrame", padding=16); client.pack(fill="x", pady=(12, 0))
        ttk.Label(client, text="Eu vou entrar", style="Card.TLabel", font=("Segoe UI Semibold", 13)).pack(anchor="w")
        ttk.Label(client, text="Cole o IP Tailscale do host, use o mesmo nome da sala e conecte seu mod.", style="Hint.TLabel").pack(anchor="w", pady=(4, 10))
        line = ttk.Frame(client, style="Card.TFrame"); line.pack(fill="x")
        ttk.Button(line, text="Entrar na sala", style="Accent.TButton", command=self.join_room).pack(side="left")
        ttk.Button(line, text="Abrir Half Sword", command=self.launch_game).pack(side="left", padx=8)

        bottom = ttk.Frame(root); bottom.pack(fill="x", pady=(18, 0))
        ttk.Label(bottom, textvariable=self.status).pack(side="left")
        ttk.Button(bottom, text="Parar conexão", command=self.stop).pack(side="right")
        ttk.Label(root, text="assinado: shokk", style="Title.TLabel",
                  font=("Segoe UI Semibold", 10)).pack(anchor="e", pady=(8, 0))

    def _runtime_ok(self) -> bool:
        if getattr(sys, "frozen", False):
            required = (ROOT / "relay_server" / "relay_server.exe", ROOT / "peer_agent" / "peer_agent.exe")
            if all(item.exists() for item in required): return True
            messagebox.showerror("Arquivos ausentes", "A pasta portátil está incompleta. Extraia todos os arquivos do ZIP.")
            return False
        if PYTHON.exists(): return True
        messagebox.showerror("Dependências ausentes", "O Python do launcher não foi encontrado. Copie a pasta completa do projeto.")
        return False

    def _start(self, arguments: list[str], log_name: str) -> subprocess.Popen[bytes]:
        LOG_DIR.mkdir(exist_ok=True)
        log = (LOG_DIR / log_name).open("ab")
        if getattr(sys, "frozen", False):
            component = Path(arguments[0]).stem
            executable = ROOT / component / f"{component}.exe"
            command = [str(executable), *arguments[1:]]
        else:
            command = [str(PYTHON), *arguments]
        return subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))

    def _validate(self, require_server: bool) -> tuple[str, str, str] | None:
        name, room, address = self.name.get().strip(), self.room.get().strip(), self.server.get().strip()
        if not name or not room:
            messagebox.showwarning("Dados incompletos", "Informe seu nome e a sala."); return None
        if require_server and not address:
            messagebox.showwarning("IP ausente", "Cole o IP Tailscale do host."); return None
        return name, room, address

    def host_room(self) -> None:
        values = self._validate(False)
        if not values or not self._runtime_ok(): return
        name, room, _ = values
        if not port_open(RELAY_PORT): self.relay = self._start(["relay_server.py", "--host", "0.0.0.0", "--port", str(RELAY_PORT)], "relay.log")
        if self.agent and self.agent.poll() is None: self.agent.terminate()
        self.agent = self._start(["peer_agent.py", "--server", f"ws://127.0.0.1:{RELAY_PORT}", "--room", room, "--name", name, "--role", "host"], "peer-host.log")
        address = tailscale_ip()
        self.server.set(address)
        self.host_address.config(text=f"Envie: {address}:{RELAY_PORT}" if address else "Tailscale não conectado")
        self.lock_button.config(state="normal")
        self.bot_add_button.config(state="normal")
        self.bot_remove_button.config(state="normal")
        self.spar_clear_button.config(state="normal")
        self.status.set("Host conectado. Abra Half Sword depois que o mod estiver instalado.")

    def join_room(self) -> None:
        values = self._validate(True)
        if not values or not self._runtime_ok(): return
        name, room, address = values
        if self.agent and self.agent.poll() is None: self.agent.terminate()
        endpoint = address if address.startswith("ws://") else f"ws://{address}:{RELAY_PORT}"
        self.agent = self._start(["peer_agent.py", "--server", endpoint, "--room", room, "--name", name, "--role", "client"], "peer-client.log")
        self.lock_button.config(state="disabled")
        self.bot_add_button.config(state="disabled")
        self.bot_remove_button.config(state="disabled")
        self.spar_clear_button.config(state="disabled")
        self.status.set("Tentando entrar. O host precisa estar com a mesma sala aberta.")

    def toggle_lock(self) -> None:
        BRIDGE_DIR.mkdir(parents=True, exist_ok=True)
        control = "lock off" if self.room_locked else "lock on"
        (BRIDGE_DIR / "mp_control.txt").write_text(control + "\n", encoding="utf-8")
        self.status.set("Enviando comando do host...")

    def game_command(self, command: str) -> None:
        BRIDGE_DIR.mkdir(parents=True, exist_ok=True)
        (BRIDGE_DIR / "mp_game_control.txt").write_text(command + "\n", encoding="utf-8")
        self.status.set("Comando do painel enviado ao jogo.")

    def _poll_room_status(self) -> None:
        status_file = BRIDGE_DIR / "mp_room_status.json"
        try:
            payload = json.loads(status_file.read_text(encoding="utf-8"))
            players = payload.get("players", [])
            self.room_locked = bool(payload.get("locked", False))
            names = ", ".join(str(player.get("name", "Jogador")) for player in players) or "aguardando"
            state = "trancada" if self.room_locked else "aberta"
            self.room_status.set(f"Sala {state} — {len(players)}/2: {names}")
            self.lock_button.config(text="Destrancar sala" if self.room_locked else "Trancar sala")
        except (OSError, ValueError, TypeError):
            pass
        self.after(500, self._poll_room_status)

    def copy_address(self) -> None:
        address = tailscale_ip()
        if not address:
            messagebox.showwarning("Tailscale", "Conecte o Tailscale antes de copiar o endereço."); return
        self.clipboard_clear(); self.clipboard_append(address)
        self.status.set("IP Tailscale copiado.")

    def launch_game(self) -> None:
        try: os.startfile("steam://rungameid/2397300")  # type: ignore[attr-defined]
        except OSError as exc: messagebox.showerror("Steam", str(exc))

    def stop(self) -> None:
        for process in (self.agent, self.relay):
            if process and process.poll() is None: process.terminate()
        self.agent = None; self.relay = None
        self.status.set("Conexão local encerrada.")

    def close(self) -> None:
        self.stop(); self.destroy()


if __name__ == "__main__":
    RealLauncher().mainloop()
