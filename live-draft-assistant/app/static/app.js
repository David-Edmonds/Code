const pollMs = Number(document.body.dataset.pollSeconds || 5) * 1000;
let latestState = null;
let configHydrated = false;
let wasMyTurn = false;

const $ = (id) => document.getElementById(id);
const escapeHtml = (value) => String(value ?? "").replace(
  /[&<>'"]/g,
  (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" })[char],
);

function toast(message) {
  const el = $("toast");
  el.textContent = message;
  el.classList.remove("hidden");
  setTimeout(() => el.classList.add("hidden"), 2300);
}

function turnAlert() {
  try {
    const context = new AudioContext();
    const oscillator = context.createOscillator();
    const gain = context.createGain();
    oscillator.connect(gain);
    gain.connect(context.destination);
    oscillator.frequency.value = 720;
    gain.gain.setValueAtTime(0.08, context.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, context.currentTime + 0.35);
    oscillator.start();
    oscillator.stop(context.currentTime + 0.35);
  } catch (_) {
    // Browser audio can remain blocked until the page has received a click.
  }
}

async function request(url, options = {}) {
  const response = await fetch(url, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || `Request failed (${response.status})`);
  return data;
}

function render(state) {
  latestState = state;
  $("mode-pill").textContent = state.mode === "yahoo-live" ? "Yahoo live" : "Manual backup";
  const turn = state.draft.is_my_turn;
  if (turn && !wasMyTurn) turnAlert();
  wasMyTurn = turn;

  $("turn-pill").textContent = state.draft.complete
    ? "DRAFT COMPLETE"
    : turn
      ? "YOU ARE ON THE CLOCK"
      : `Slot ${state.draft.current_slot} is picking`;
  $("turn-pill").classList.toggle("my-turn", turn);
  $("next-pick").textContent = state.draft.next_overall ?? "✓";
  $("turn-detail").textContent = state.draft.complete
    ? "Your roster is complete."
    : turn
      ? "Pick now. Use the first name unless late news changes it."
      : `Your next turn is pick ${state.draft.next_my_pick ?? "—"}.`;
  $("completed-picks").textContent = state.draft.completed;
  $("until-turn").textContent = state.draft.picks_until_turn ?? "—";
  $("next-my-pick").textContent = state.draft.next_my_pick ?? "—";

  $("recommendations").innerHTML = state.recommendations.length
    ? state.recommendations.map((player, index) => `
      <article class="recommendation">
        <div class="recommendation-rank">${index + 1}</div>
        <h3>${escapeHtml(player.name)}</h3>
        <p class="meta">${escapeHtml(player.position)} · ${escapeHtml(player.team)} · ADP ${player.adp ?? "—"}</p>
        <p>${escapeHtml(player.reason || "")}</p>
      </article>`).join("")
    : '<p class="helper">No rankings loaded yet. Connect Yahoo, refresh, or import a CSV.</p>';

  $("roster").innerHTML = state.roster.length
    ? state.roster.map((player) => `
      <div class="list-row"><span class="position">${escapeHtml(player.position || "?")}</span><strong>${escapeHtml(player.name)}</strong><span class="meta">${escapeHtml(player.team || "")}</span></div>`).join("")
    : '<p class="helper">No players drafted yet.</p>';

  $("recent-picks").innerHTML = state.recent_picks.length
    ? state.recent_picks.map((pick) => `
      <div class="list-row"><span>${pick.pick}</span><strong>${escapeHtml(pick.player_name || pick.player_id || "Unknown")}</strong><span class="meta">${escapeHtml(pick.position || "")}</span></div>`).join("")
    : '<p class="helper">The board is empty.</p>';

  $("available-table").innerHTML = state.available.map((player, index) => `
    <tr><td>${index + 1}</td><td><strong>${escapeHtml(player.name)}</strong></td><td>${escapeHtml(player.position)}</td><td>${escapeHtml(player.team)}</td><td>${player.custom_rank ?? player.yahoo_rank ?? "—"}</td><td>${player.adp ?? "—"}</td><td>${escapeHtml(player.injury_status || "—")}</td><td>${escapeHtml(player.reason || "")}</td></tr>`).join("");

  $("player-options").innerHTML = state.available.map(
    (player) => `<option value="${escapeHtml(player.name)}">${escapeHtml(player.position)} · ${escapeHtml(player.team)}</option>`,
  ).join("");

  $("errors").textContent = (state.errors || []).join("\n");
  $("last-refresh").textContent = `Updated ${new Date(state.last_refresh).toLocaleTimeString()}`;

  if (!configHydrated) {
    const cfg = state.config;
    $("teams").value = cfg.teams;
    $("slot").value = cfg.slot;
    $("rounds").value = cfg.rounds;
    $("team-id").value = cfg.team_id;
    $("league-id").value = cfg.league_id;
    $("scoring").value = cfg.scoring;
    configHydrated = true;
  }
}

async function refreshState() {
  try {
    render(await request("/api/state"));
  } catch (error) {
    $("errors").textContent = error.message;
  }
}

$("refresh-button").addEventListener("click", async () => {
  try {
    await request("/api/refresh?force=true", { method: "POST" });
    await refreshState();
    toast("Sources refreshed");
  } catch (error) {
    toast(error.message);
  }
});

$("copy-button").addEventListener("click", async () => {
  if (!latestState) return;
  await navigator.clipboard.writeText(latestState.chatgpt_prompt);
  toast("Live draft context copied");
});

$("ai-button").addEventListener("click", async () => {
  const output = $("ai-result");
  output.classList.remove("hidden");
  output.textContent = "Reviewing…";
  try {
    output.textContent = (await request("/api/ai-review", { method: "POST" })).answer;
  } catch (error) {
    output.textContent = error.message;
  }
});

$("manual-name").addEventListener("change", () => {
  if (!latestState) return;
  const selected = latestState.available.find(
    (player) => player.name.toLowerCase() === $("manual-name").value.trim().toLowerCase(),
  );
  if (!selected) return;
  $("manual-position").value = selected.position || "";
  $("manual-team").value = selected.team || "";
});

$("manual-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    await request("/api/manual/pick", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        player_name: $("manual-name").value,
        position: $("manual-position").value,
        nfl_team: $("manual-team").value,
      }),
    });
    $("manual-name").value = "";
    $("manual-position").value = "";
    $("manual-team").value = "";
    await refreshState();
    $("manual-name").focus();
  } catch (error) {
    toast(error.message);
  }
});

$("undo-button").addEventListener("click", async () => {
  try {
    const result = await request("/api/manual/undo", { method: "POST" });
    await refreshState();
    toast(`Removed ${result.removed.player_name}`);
  } catch (error) {
    toast(error.message);
  }
});

$("config-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    await request("/api/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        teams: Number($("teams").value),
        slot: Number($("slot").value),
        rounds: Number($("rounds").value),
        team_id: Number($("team-id").value),
        league_id: $("league-id").value,
        scoring: $("scoring").value,
      }),
    });
    configHydrated = false;
    toast("League setup saved");
    await refreshState();
  } catch (error) {
    toast(error.message);
  }
});

$("rankings-file").addEventListener("change", async (event) => {
  const file = event.target.files[0];
  if (!file) return;
  const form = new FormData();
  form.append("file", file);
  try {
    const result = await request("/api/rankings/upload", { method: "POST", body: form });
    toast(`${result.players} rankings imported`);
    await refreshState();
  } catch (error) {
    toast(error.message);
  }
});

refreshState();
setInterval(refreshState, pollMs);
