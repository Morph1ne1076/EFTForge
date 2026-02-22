const API_BASE = "http://127.0.0.1:8000";

let allGuns = [];
let currentGun = null;
let selectedAttachments = {};
let currentBuildData = null;

/* ===========================
   LOAD GUN LIST
=========================== */

fetch(`${API_BASE}/guns`)
  .then(res => res.json())
  .then(data => {
    allGuns = data;
    renderGunList(data);
  });

function renderGunList(guns) {
  const list = document.getElementById("guns");
  list.innerHTML = "";

  guns
    .sort((a, b) => b.base_ergo - a.base_ergo)
    .forEach(gun => {
      const li = document.createElement("li");
      li.textContent = `${gun.name} ｜ Base Ergo: ${gun.base_ergo}`;
      li.style.cursor = "pointer";

      li.onclick = () => {
        currentGun = gun;
        selectedAttachments = {};
        currentBuildData = null;
        loadBaseStats();
        loadSlots();
      };

      list.appendChild(li);
    });
}

/* ===========================
   BASE STATS
=========================== */

function loadBaseStats() {
  const box = document.getElementById("stats");

  box.innerHTML = `
    <h3>武器属性</h3>
    <div>Base Ergo (in-game): ${currentGun.base_ergo}</div>
    <div>Gun Weight: ${currentGun.weight} kg</div>
    <hr />
    <div id="calculated-stats"></div>
  `;

  refreshBuildStats();
}

/* ===========================
   BACKEND BUILD CALCULATION
=========================== */

function refreshBuildStats(callback = null) {
  const attachmentIds = Object.values(selectedAttachments).map(a => a.id);

  fetch(`${API_BASE}/build/calculate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      base_item_id: currentGun.id,
      attachment_ids: attachmentIds
    })
  })
  .then(res => res.json())
  .then(data => {

    currentBuildData = data;

    document.getElementById("calculated-stats").innerHTML = `
      <div>Base Ergo: ${data.base_ergo}</div>
      <div>Base Weight: ${data.base_weight} kg</div>
      <div>Total Weight: ${data.total_weight} kg</div>
      <div>EvoErgoDelta: ${data.evo_ergo_delta}</div>
      <div>OverSwing: ${data.overswing ? "YES" : "NO"}</div>
      <hr/>
      <h3>Final EvoErgoDelta: ${data.evo_ergo_delta}</h3>
    `;

    if (callback) callback();
  });
}

/* ===========================
   SLOT DISPLAY
=========================== */

function loadSlots() {
  fetch(`${API_BASE}/items/${currentGun.id}/slots`)
    .then(res => res.json())
    .then(slots => {

      const box = document.getElementById("slots");
      box.innerHTML = "<h3>改装槽位</h3>";

      slots.forEach(slot => {
        const div = document.createElement("div");
        div.textContent = `• ${slot.slot_name}`;
        div.style.cursor = "pointer";

        div.onclick = () => {
          loadAttachments(slot.id);
        };

        box.appendChild(div);
      });
    });
}

/* ===========================
   ATTACHMENTS
=========================== */

function loadAttachments(slotId) {
  fetch(`${API_BASE}/slots/${slotId}/allowed-items`)
    .then(res => res.json())
    .then(items => {

      const box = document.getElementById("slots");
      box.innerHTML = "<h3>可用配件</h3>";

      if (!currentBuildData) return;

      const currentEED = parseFloat(currentBuildData.evo_ergo_delta);

      items.forEach(item => {

        const div = document.createElement("div");
        div.style.cursor = "pointer";
        div.textContent = `${item.name} ｜ Weight ${item.weight ?? 0} kg ｜ ΔEvo ...`;
        box.appendChild(div);

        // Prepare simulated attachment list
        const simulatedIds = [
          ...Object.entries(selectedAttachments)
            .filter(([key]) => key !== slotId)
            .map(([, val]) => val.id),
          item.id
        ];

        // Backend simulation
        fetch(`${API_BASE}/build/calculate`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            base_item_id: currentGun.id,
            attachment_ids: simulatedIds
          })
        })
        .then(res => res.json())
        .then(simData => {

          const simulatedEED = parseFloat(simData.evo_ergo_delta);
          const delta = (simulatedEED - currentEED).toFixed(2);
          const sign = delta > 0 ? "+" : "";

          div.textContent =
            `${item.name} ｜ Weight ${item.weight ?? 0} kg ｜ ΔEvo ${sign}${delta}`;
        });

        div.onclick = () => {
          selectedAttachments[slotId] = item;

          refreshBuildStats(() => {
            loadAttachments(slotId);
          });
        };
      });
    });
}