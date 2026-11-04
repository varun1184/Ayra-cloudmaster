import asyncio
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI(title="Ayra Cloud Master")

# Track whether your local PC node is connected
pc_node_status = {
    "is_online": False,
    "last_heartbeat": None,
    "websocket": None
}


@app.get("/", response_class=HTMLResponse)
def read_root():
    status_color = "#10B981" if pc_node_status["is_online"] else "#EF4444"
    status_text = "ONLINE (PC Connected)" if pc_node_status["is_online"] else "OFFLINE (PC Sleeping)"

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Ayra Cloud Master</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                background-color: #0f172a;
                color: #f8fafc;
                margin: 0;
                padding: 20px;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
            }}
            .card {{
                background: #1e293b;
                padding: 24px;
                border-radius: 16px;
                box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
                width: 100%;
                max-width: 400px;
                box-sizing: border-box;
                text-align: center;
            }}
            h1 {{ font-size: 22px; margin-bottom: 4px; color: #38bdf8; }}
            .subtitle {{ font-size: 13px; color: #64748b; margin-bottom: 20px; }}
            .badge {{
                display: inline-block;
                padding: 8px 16px;
                border-radius: 20px;
                font-weight: bold;
                font-size: 13px;
                background-color: {status_color};
                color: white;
                margin-bottom: 20px;
                letter-spacing: 0.5px;
            }}
            .info {{
                background: #0f172a;
                padding: 12px;
                border-radius: 8px;
                font-size: 13px;
                color: #94a3b8;
                text-align: left;
                margin-bottom: 20px;
            }}
            button {{
                background: #38bdf8;
                color: #0f172a;
                border: none;
                padding: 12px;
                border-radius: 8px;
                font-weight: bold;
                width: 100%;
                cursor: pointer;
                font-size: 14px;
            }}
            button:active {{ background: #0ea5e9; }}
        </style>
        <!-- Auto-refresh page every 5 seconds to keep mobile status live -->
        <meta http-equiv="refresh" content="5">
    </head>
    <body>
        <div class="card">
            <h1>🤖 Ayra Cloud Master</h1>
            <div class="subtitle">Hybrid Cloud-Local Assistant</div>
            <div>
                <span class="badge">{status_text}</span>
            </div>
            <div class="info">
                <p style="margin: 0 0 6px 0;"><b>Cloud Status:</b> Active 24/7</p>
                <p style="margin: 0;"><b>Last PC Heartbeat:</b><br>{str(pc_node_status["last_heartbeat"]) if pc_node_status["last_heartbeat"] else "Never"}</p>
            </div>
            <button onclick="location.reload()">Manual Refresh</button>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.websocket("/ws/pc-node")
async def websocket_pc_endpoint(websocket: WebSocket):
    await websocket.accept()
    pc_node_status["is_online"] = True
    pc_node_status["last_heartbeat"] = datetime.now()
    pc_node_status["websocket"] = websocket
    print("--> PC Node Connected successfully!")

    try:
        while True:
            data = await websocket.receive_text()
            if data == "PING":
                pc_node_status["last_heartbeat"] = datetime.now()
                pc_node_status["is_online"] = True
                await websocket.send_text("PONG")
            elif data.startswith("TASK_RESULT:"):
                print(f"Result from PC: {data}")
    except WebSocketDisconnect:
        pc_node_status["is_online"] = False
        pc_node_status["websocket"] = None
        print("--> PC Node Disconnected!")


async def check_pc_health():
    while True:
        await asyncio.sleep(15)
        if pc_node_status["last_heartbeat"]:
            elapsed = (datetime.now() - pc_node_status["last_heartbeat"]).total_seconds()
            if elapsed > 45:
                pc_node_status["is_online"] = False


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(check_pc_health())