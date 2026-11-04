import asyncio
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Form
from fastapi.responses import HTMLResponse

app = FastAPI(title="Ayra Cloud Master")

pc_node_status = {
    "is_online": False,
    "last_heartbeat": None,
    "websocket": None,
    "last_command": "None",
    "command_result": "Ready for voice or text commands!"
}


# --- CLOUD-ONLY SKILLS (Executes 24/7 on Render when PC is OFF) ---
def process_cloud_task(command: str) -> str:
    cmd = command.lower().strip()

    if "time" in cmd or "date" in cmd:
        now = datetime.now().strftime("%I:%M %p on %B %d, %Y")
        return f"Current cloud time is {now}."
    elif "hello" in cmd or "hi" in cmd or "ayra" in cmd:
        return "Hello! Ayra Cloud Master is active and listening."
    elif "status" in cmd:
        pc_state = "online" if pc_node_status["is_online"] else "offline (sleeping)"
        return f"Cloud backend is 24/7 active. Your home PC is currently {pc_state}."
    else:
        # Fallback for unrecognized cloud-only tasks
        return f"Received cloud request: '{command}'. (PC is offline, so desktop automation is unavailable right now)."


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
        <title>Ayra Voice & Cloud Control</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                background-color: #0f172a;
                color: #f8fafc;
                margin: 0;
                padding: 16px;
                display: flex;
                flex-direction: column;
                align-items: center;
                min-height: 100vh;
            }}
            .card {{
                background: #1e293b;
                padding: 20px;
                border-radius: 16px;
                box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
                width: 100%;
                max-width: 400px;
                box-sizing: border-box;
                text-align: center;
            }}
            h1 {{ font-size: 20px; margin-bottom: 2px; color: #38bdf8; }}
            .subtitle {{ font-size: 12px; color: #64748b; margin-bottom: 16px; }}
            .badge {{
                display: block;
                padding: 6px 12px;
                border-radius: 20px;
                font-weight: bold;
                font-size: 12px;
                background-color: {status_color};
                color: white;
                margin-bottom: 16px;
            }}
            .section {{
                background: #0f172a;
                padding: 14px;
                border-radius: 8px;
                font-size: 13px;
                color: #94a3b8;
                margin-bottom: 16px;
                text-align: left;
            }}
            input[type="text"] {{
                width: 100%;
                padding: 10px;
                border-radius: 8px;
                border: 1px solid #334155;
                background: #0f172a;
                color: white;
                box-sizing: border-box;
                margin-bottom: 10px;
                font-size: 14px;
            }}
            .btn-group {{
                display: flex;
                gap: 8px;
            }}
            button {{
                background: #38bdf8;
                color: #0f172a;
                border: none;
                padding: 12px;
                border-radius: 8px;
                font-weight: bold;
                flex: 1;
                cursor: pointer;
                font-size: 14px;
            }}
            .mic-btn {{
                background: #ef4444;
                color: white;
            }}
            button:active {{ opacity: 0.8; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🤖 Ayra Voice & Cloud</h1>
            <div class="subtitle">24/7 Hybrid Mobile Assistant</div>

            <span class="badge">{status_text}</span>

            <div class="section">
                <b>Last Command:</b><br>{pc_node_status["last_command"]}<br><br>
                <b>Ayra Response:</b><br><span id="response-text" style="color: #38bdf8;">{pc_node_status["command_result"]}</span>
            </div>

            <form id="cmd-form" action="/send-command" method="POST">
                <input type="text" id="cmd-input" name="command" placeholder="Type or click Speak..." required>
                <div class="btn-group">
                    <button type="button" class="mic-btn" onclick="startListening()">🎙️ Speak</button>
                    <button type="submit">Send</button>
                </div>
            </form>
        </div>

        <script>
            // --- Text-to-Speech (Ayra speaks back) ---
            function speakText(text) {{
                if ('speechSynthesis' in window) {{
                    window.speechSynthesis.cancel();
                    const utterance = new SpeechSynthesisUtterance(text);
                    utterance.rate = 1.0;
                    utterance.pitch = 1.0;
                    window.speechSynthesis.speak(utterance);
                }}
            }}

            // Automatically speak Ayra's response on load if it's new
            const currentResponse = "{pc_node_status['command_result']}";
            if (currentResponse && currentResponse !== "Ready for voice or text commands!") {{
                speakText(currentResponse);
            }}

            // --- Speech-to-Text (Voice Recognition) ---
            function startListening() {{
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                if (!SpeechRecognition) {{
                    alert("Voice recognition is not supported on this browser. Try Chrome or Safari.");
                    return;
                }}

                const recognition = new SpeechRecognition();
                recognition.lang = 'en-US';
                recognition.interimResults = false;

                const micBtn = document.querySelector('.mic-btn');
                micBtn.innerText = "🎧 Listening...";
                micBtn.style.background = "#10b981";

                recognition.start();

                recognition.onresult = function(event) {{
                    const transcript = event.results[0][0].transcript;
                    document.getElementById('cmd-input').value = transcript;
                    micBtn.innerText = "🎙️ Speak";
                    micBtn.style.background = "#ef4444";
                    document.getElementById('cmd-form').submit();
                }};

                recognition.onerror = function(event) {{
                    micBtn.innerText = "🎙️ Speak";
                    micBtn.style.background = "#ef4444";
                    alert("Voice recognition error: " + event.error);
                }};
            }}
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.post("/send-command", response_class=HTMLResponse)
async def send_command(command: str = Form(...)):
    pc_node_status["last_command"] = command

    # 1. If PC is online, route command to local workstation
    if pc_node_status["is_online"] and pc_node_status["websocket"]:
        try:
            await pc_node_status["websocket"].send_text(f"CMD:{command}")
            pc_node_status["command_result"] = f"Sent to PC: '{command}'. Executing..."
        except Exception as e:
            pc_node_status["command_result"] = process_cloud_task(command)
    else:
        # 2. If PC is offline, execute cloud-only task 24/7!
        pc_node_status["command_result"] = process_cloud_task(command)

    return HTMLResponse(content="""
        <script>window.location.href='/';</script>
    """)


@app.websocket("/ws/pc-node")
async def websocket_pc_endpoint(websocket: WebSocket):
    await websocket.accept()
    pc_node_status["is_online"] = True
    pc_node_status["last_heartbeat"] = datetime.now()
    pc_node_status["websocket"] = websocket

    try:
        while True:
            data = await websocket.receive_text()
            if data == "PING":
                pc_node_status["last_heartbeat"] = datetime.now()
                pc_node_status["is_online"] = True
                await websocket.send_text("PONG")
            elif data.startswith("TASK_RESULT:"):
                pc_node_status["command_result"] = data.replace("TASK_RESULT:", "").strip()
    except WebSocketDisconnect:
        pc_node_status["is_online"] = False
        pc_node_status["websocket"] = None


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