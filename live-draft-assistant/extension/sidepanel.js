const BASE = "http://127.0.0.1:8765";
let state = null;

const $ = (id) => document.getElementById(id);
const escapeHtml = (value) => String(value ?? "").replace(
  /[&<>'"]/g,
  (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" })[char],
);

async function request(path, options = {}) {
  const response = await fetch(`${BASE}${path}`, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || `Local assistant returned ${response.status}`);
  return data;
}

function render(next) {
  state = next;
  $("mode").textContent = next.mode === "yahoo-live" ? "Yahoo live" : "Manual";
  $("next-pick").textContent = next.draft.next_overall ?? "✓";
  $("turn-status").textContent = next.draft.complete
    ? "Draft complete"
    : next.draft.is_my_turn
      ? "YOU ARE ON THE CLOCK"
      : `Owner ${next.draft.current_slot} is picking`;
  $("next-mine").textContent = next.draft.complete
    ? ""
    : `Your next owned pick: ${next.draft.next_my_pick ?? "—"} · ${next.draft.picks_until_turn ?? "—"} before you`;
  $("turn-card").classList.toggle("mine", Boolean(next.draft.is_my_turn));

  $("recommendations").innerHTML = next.recommendations.length
    ? next.recommendations.map((player, index) => `
      <article class="player">
        <div class="player-row">
          <span class="rank">${index + 1}</span>
          <div><strong>${escapeHtml(player.name)}</strong><small>${escapeHtml(player.position)} · ${escapeHtml(player.team)} · ADP ${player.adp ?? "—"}</small></div>
          <small>${escapeHtml(player.reason || "")}</small>
        </div>
      </article>`).join("")
    : '<div class="player">No rankings loaded.</div>';

  $("roster").innerHTML = next.roster.length
    ? next.roster.map((player) => `
      <div class="roster-item"><span class="pos">${escapeHtml(player.position || "?")}</span><strong>${escapeHtml(player.name)}</strong><span>${escapeHtml(player.team || "")}</span></div>`).join("")
    : '<div class="roster-item">No players rostered yet.</div>';

  const special = next.special_rules || {};
  const parts = [];
  if (special.keeper_league) parts.push(`${special.keeper_count} keepers`);
  if (special.custom_pick_count) parts.push(`${special.custom_pick_count} custom picks`);
  $("special").textContent = parts.join(" · ") || "Normal snake";
  $("error").textContent = (next.errors || []).join("\n");
}

async function refresh() {
  try {
    render(await request("/api/state"));
  } catch (error) {
    $("mode").textContent = "Offline";
    $("error").textContent = "Start run_windows.bat, then press Refresh.\n" + error.message;
  }
}

$("refresh").addEventListener("click", async () => {
  try {
    await request("/api/refresh?force=true", { method: "POST" });
  } catch (_) {
    // State refresh below will show a useful connection error.
  }
  await refresh();
});

$("copy").addEventListener("click", async () => {
  if (!state) return;
  await navigator.clipboard.writeText(state.chatgpt_prompt);
  const button = $("copy");
  const previous = button.textContent;
  button.textContent = "Copied";
  setTimeout(() => { button.textContent = previous; }, 1200);
});

$("open-dashboard").addEventListener("click", () => {
  window.open(BASE, "_blank", "noopener");
});

refresh();
setInterval(refresh, 3000);
