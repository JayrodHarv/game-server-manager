let ws = null;

async function createServer() {
  const name = document.getElementById("server-name").value;
  const game = document.getElementById("game").value;

  const res = await fetch("/servers/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: name,
      game: game,
      config: {
        rcon_password: "password"
      }
    })
  });

  const data = await res.json();
  alert(JSON.stringify(data));
}

function connectConsole() {
  const server = document.getElementById("console-server").value;
  const consoleEl = document.getElementById("console");

  consoleEl.textContent = "";

  ws = new WebSocket(`ws://${location.host}/ws/servers/${server}`);

  ws.onopen = () => {
    consoleEl.textContent += "[connected]\n";
  };

  ws.onmessage = (event) => {
    consoleEl.textContent += event.data + "\n";
    consoleEl.scrollTop = consoleEl.scrollHeight;
  };

  ws.onclose = () => {
    consoleEl.textContent += "\n[disconnected]\n";
  };
}

function handleCommand(event) {
  if (event.key === "Enter" && ws) {
    const cmd = event.target.value.trim();
    if (!cmd) return;

    ws.send(cmd);
    event.target.value = "";
  }
}