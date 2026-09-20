import asyncio
import json
import math
import time

try:
    import websockets
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets"])
    import websockets

ROOM = "duelo"
SERVER = "ws://127.0.0.1:8790"
PLAYER = "AmigoFalso"
PROTOCOL = 1

async def run():
    async with websockets.connect(SERVER, max_size=2**20) as ws:
        await ws.send(json.dumps({"type": "hello", "protocol": PROTOCOL, "name": PLAYER, "role": "client", "room": ROOM}))
        resp = json.loads(await asyncio.wait_for(ws.recv(), timeout=5))
        print(f"[OK] Conectado como {PLAYER} na sala '{ROOM}'")
        
        try:
            while True:
                extra = await asyncio.wait_for(ws.recv(), timeout=0.3)
                data = json.loads(extra)
                if data.get("type") == "room.status":
                    players = [p["name"] for p in data.get("players", [])]
                    print(f"  Sala: {', '.join(players)}")
        except asyncio.TimeoutError:
            pass

        print("[OK] Enviando snapshots em tempo real (20Hz)...\n")
        
        start = time.time()
        host_positions = []
        sent = 0
        
        for i in range(200):
            t = time.time() - start
            x = 50.0 + math.sin(t * 0.5) * 30.0
            y = 50.0 + math.cos(t * 0.3) * 20.0
            z = 1.5 + math.sin(t * 0.8) * 0.2
            yaw = (t * 45) % 360
            
            state = [round(x, 4), round(y, 4), round(z, 4), 0.0, round(yaw, 4), 0.0]
            await ws.send(json.dumps({"type": "snapshot", "state": state}))
            sent += 1
            
            try:
                while True:
                    resp = await asyncio.wait_for(ws.recv(), timeout=0.02)
                    data = json.loads(resp)
                    if data.get("type") == "snapshot":
                        s = data.get("state", [0,0,0])
                        host_positions.append((s[0], s[1], s[2]))
            except asyncio.TimeoutError:
                pass
            
            if sent % 20 == 0:
                hp = host_positions[-1] if host_positions else (0,0,0)
                print(f"  [{sent}/200] Voce: ({x:.0f},{y:.0f},{z:.0f}) | Host: ({hp[0]:.0f},{hp[1]:.0f},{hp[2]:.0f}) | {len(host_positions)} recv")
            
            await asyncio.sleep(0.05)

        print(f"\n[FIM] {sent} snapshots enviados, {len(host_positions)} recebidos do host")

asyncio.run(run())
