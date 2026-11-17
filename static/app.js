// Skills shown as checkboxes. Names must match the backend's ALIASES keys.
const SKILLS = [
  "Python", "JavaScript", "HTML/CSS", "React", "Tailwind CSS", "FastAPI",
  "SQL", "Git", "Docker", "REST APIs", "Machine Learning", "Pandas",
  "Statistics", "Data Visualization"
];

const esc = s => String(s).replace(/[&<>"']/g, c =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

// Build the skill checkboxes
document.getElementById("skillChecks").innerHTML = SKILLS.map((s, i) =>
  `<label class="check" for="sk${i}"><input type="checkbox" id="sk${i}" value="${esc(s)}"> ${esc(s)}</label>`
).join("");

let report = null; // latest analysis from the backend, sent with each chat question

async function postJSON(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error("Server returned " + res.status);
  return res.json();
}

document.getElementById("runBtn").addEventListener("click", runAnalysis);

async function runAnalysis() {
  const results = document.getElementById("results");
  const name = document.getElementById("name").value.trim();
  const resume = document.getElementById("resume").value;
  const skills = [...document.querySelectorAll("#skillChecks input:checked")].map(b => b.value);

  if (skills.length === 0 && !resume.trim()) {
    results.innerHTML = `<div class="panel empty">Tick a skill or paste your resume to see your report.</div>`;
    return;
  }

  results.innerHTML = `<div class="panel empty">Analyzing your profile…</div>`;

  try {
    report = await postJSON("/api/analyze", { name, resume, skills });

    // Tick the skills the backend found in the resume
    document.querySelectorAll("#skillChecks input").forEach(b => {
      b.checked = report.skills.includes(b.value);
    });

    renderReport(report);
  } catch (err) {
    results.innerHTML = `<div class="panel empty">Could not reach the analysis server. Start it with <b>uvicorn main:app --reload</b> and open <b>http://127.0.0.1:8000</b>.</div>`;
  }
}

function renderReport(r) {
  const who = r.name ? esc(r.name) : "You";
  const verb = r.name ? "has" : "have";

  const bars = Object.entries(r.scores).map(([role, pct]) => `
    <div class="bar-row">
      <div class="bar-label"><span>${esc(role)}</span><span>${pct}%</span></div>
      <div class="bar"><span style="width:${pct}%"></span></div>
    </div>`).join("");

  const gaps = r.gaps.length
    ? r.gaps.map(g => `<span class="chip">${esc(g.skill)} · ${g.level}</span>`).join("")
    : `<span class="chip ok">No gaps. Great fit!</span>`;

  const recs = [...r.opportunities, ...r.courses].map(o => `
    <div class="opp">
      <div><b>${esc(o.title)}</b><span>${esc(o.note)}</span></div>
      <div class="tag">${esc(o.kind)}</div>
    </div>`).join("") || `<span class="muted">No recommendations for this profile yet.</span>`;

  const road = r.roadmap.map(s => `
    <div class="road-item">
      <div class="road-num">W${s.week}</div>
      <div><b>${esc(s.title)}</b><p>${esc(s.text)}</p></div>
    </div>`).join("");

  document.getElementById("results").innerHTML = `
    <div class="panel fade">
      <h3>📊 ${who}'s career match</h3>
      <p class="muted">${who} ${verb} ${r.skills.length} skill(s): ${r.skills.map(esc).join(", ") || "none"}.</p>
      <div class="stats">
        <div class="stat"><b>${r.skills.length}</b><span>Skills detected</span></div>
        <div class="stat"><b>${r.best_pct}%</b><span>Top match</span></div>
        <div class="stat"><b>${r.gaps.length}</b><span>Skill gaps</span></div>
      </div>
      <div style="margin-top:18px">${bars}</div>
    </div>

    <div class="panel fade">
      <h3>🧩 Skill gaps for ${esc(r.best_role)}</h3>
      <div class="chips">${gaps}</div>
    </div>

    <div class="panel fade">
      <h3>💼 Recommended for you</h3>
      ${recs}
    </div>

    <div class="panel fade">
      <h3>🛤️ Your personalized learning path</h3>
      <div class="road">${road}</div>
    </div>

    <div class="panel fade">
      <h3>🎤 Interview practice: ${esc(r.best_role)}</h3>
      ${r.interview.map((q, i) => `
        <div class="rec">
          <div><b>${i + 1}. ${esc(q)}</b></div>
          <div class="tag">Q${i + 1}</div>
        </div>`).join("")}
    </div>

    <div class="panel fade">
      <h3>🤖 AI Career Assistant</h3>
      <div class="chat">
        <div class="msgs" id="chatMsgs">
          <div class="msg bot">Hi${r.name ? " " + esc(r.name) : ""}! Ask me about your gaps, internships, hackathons, or your roadmap.</div>
        </div>
        <div class="chat-row">
          <input type="text" id="chatIn" placeholder="e.g. What should I learn first?" maxlength="200">
          <button id="chatBtn" class="btn chat-send">Ask</button>
        </div>
      </div>
    </div>`;

  document.getElementById("chatBtn").addEventListener("click", sendChat);
  document.getElementById("chatIn").addEventListener("keydown", e => {
    if (e.key === "Enter") sendChat();
  });
  document.getElementById("results").scrollIntoView({ behavior: "smooth", block: "start" });
}

function addMessage(who, text) {
  const box = document.getElementById("chatMsgs");
  const div = document.createElement("div");
  div.className = "msg " + who;
  div.textContent = text; // textContent keeps typed text safe
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
}

async function sendChat() {
  const input = document.getElementById("chatIn");
  const text = input.value.trim();
  if (!text) return;

  addMessage("me", text);
  input.value = "";

  try {
    const data = await postJSON("/api/chat", { question: text, report });
    addMessage("bot", data.answer);
  } catch (err) {
    addMessage("bot", "The assistant is offline. Start the server and try again.");
  }
}
