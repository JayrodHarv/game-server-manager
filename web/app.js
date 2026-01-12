const serverList = document.getElementById("serverList");
const createForm = document.getElementById("createForm");
const createResult = document.getElementById("createResult");
const consoleOutput = document.getElementById("consoleOutput");
const consoleInput = document.getElementById("consoleInput");
const sendConsole = document.getElementById("sendConsole");

let currentServer = null;
let ws = null;

// --- Create server ---
createForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const name = document.getElementById("serverName").value;
  const port = parseInt(document.getElementById("serverPort").value);

  const res = await fetch("/servers/", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({name, port})
  });
  const data = await res.json();
  createResult.innerText = JSON.stringify(data);
});

// --- List servers ---
async function refreshServers() {
  const res = await fetch("/servers/");
  const data = await res.json();
  serverList.innerHTML = "";
  data.forEach(s => {
    const li = document.createElement("li");
    li.innerText = `${s.name} (${s.status})`;
    li.addEventListener("click", () => connectConsole(s.name));
    serverList.appendChild(li);
  });
}
document.getElementById("refreshServers").addEventListener("click", refreshServers);

// --- WebSocket Console ---
function connectConsole(serverName) {
  if (ws) ws.close();
  currentServer = serverName;
  ws = new WebSocket(`ws://${location.host}/ws/servers/${serverName}`);

  ws.onmessage = (event) => {
    consoleOutput.value += event.data + "\n";
    consoleOutput.scrollTop = consoleOutput.scrollHeight;
  };

  ws.onopen = () => {
    consoleOutput.value += `Connected to ${serverName}\n`;
  };

  ws.onclose = () => {
    consoleOutput.value += `Disconnected\n`;
  };
}

// --- Send console commands ---
sendConsole.addEventListener("click", () => {
  const cmd = consoleInput.value;
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(cmd);
    consoleInput.value = "";
  }
});
