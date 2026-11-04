import asyncio
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI(title="Ayra Cloud Master")

# Track whether your local PC node is connected
pc_node_status = {
    "is_online": False,
    "last_heartbeat": None,
    "websocket": None
}

@app.get("/")
def read_root():
    return {
        "status": "Ayra Cloud Master Active",
        "pc_node_online": pc_node_status["is_online"],
        "last_seen": str(pc_node_status["last_heartbeat"])
    }

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