const socket = new WebSocket('ws://tre.local:8765');
const statusText = document.getElementById('status');
const dataContainer = document.getElementById('dataContainer');
const pollBtn = document.getElementById('pollBtn');
const speedSlider = document.getElementById('speedSlider');
const speedValue = document.getElementById('speedValue');

let pollingInterval = null;
let isPolling = false;


// Update the label when slider moves
speedSlider.oninput = () => {
  speedValue.innerText = speedSlider.value;
  // If already polling, restart with new speed immediately
  if (isPolling) {
    startPolling();
  }
};

pollBtn.onclick = () => {
  if (isPolling) {
    stopPolling();
  } else {
    startPolling();
  }
};

function startPolling() {
  if (socket.readyState !== WebSocket.OPEN) return alert("Not connected!");

  // Clear any existing timer first
  if (pollingInterval) clearInterval(pollingInterval);

  isPolling = true;
  pollBtn.innerText = "Stop Polling";
  pollBtn.style.backgroundColor = "#ff4444"; // Visual cue for "Stop"

  const ms = parseFloat(speedSlider.value) * 1000;

  // Immediate first read, then start the interval
  socket.send(JSON.stringify({ "cmd": "read" }));
  pollingInterval = setInterval(() => {
    socket.send(JSON.stringify({ "cmd": "read" }));
  }, ms);
}

function stopPolling() {
  isPolling = false;
  pollBtn.innerText = "Start Polling";
  pollBtn.style.backgroundColor = "#007bff";
  clearInterval(pollingInterval);
}

socket.onopen = () => {
  statusText.innerText = "Connected";
  statusText.style.color = "green";
};

socket.onmessage = (event) => {
  const response = JSON.parse(event.data);
  if (response.type === "data" && response.nodes) {
    renderTable(response.nodes);
    // Pass the temperature to our new chart function
    if (response.nodes.Temperature !== undefined) {
      updateChart(response.nodes.Temperature);
    }
  }
};

function renderTable(nodes) {
  let html = `<table><thead><tr><th>Param</th><th>Value</th></tr></thead><tbody>`;
  for (const [key, value] of Object.entries(nodes)) {
    // Simple logic to highlight errors
    const isAlert = (value === true && (key === 'OverTemperature' || key === 'HighPressure'));
    const rowClass = isAlert ? 'class="alert"' : '';

    html += `<tr ${rowClass}><td>${key}</td><td>${value}</td></tr>`;
  }
  html += `</tbody></table>`;
  dataContainer.innerHTML = html;
}

document.getElementById('readBtn').onclick = () => {
  if (socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({ "cmd": "read" }));
  }
};
