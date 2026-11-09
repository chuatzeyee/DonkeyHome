// DonkeyHome wizard page. Plain JavaScript, no build step. Every URL is relative (Home Assistant ingress).
"use strict";

const NAME_RE = /^[A-Za-z0-9][A-Za-z0-9 '&-]{0,39}$/;
const ROOM_IDEAS = ["Living Room", "Kitchen", "Bedroom", "Bathroom", "Dining Room", "Study", "Kids Room",
  "Entrance", "Hallway", "Laundry", "Garage", "Balcony", "Garden"];
const DELAYS = [5, 10, 15, 20, 30, 60];
// Which kind of device each yes/no choice needs, to say "you have 2 of these" or "none yet".
const CHOICE_DEVICES = {
  lights_off_when_leaving: [["light", "light", "lights"]],
  climate_off_when_leaving: [["climate", "aircon or heater", "aircons or heaters"], ["fan", "fan", "fans"]],
  media_off_when_leaving: [["media_player", "TV or speaker", "TVs or speakers"]],
  lock_when_leaving: [["lock", "door lock", "door locks"]],
  vacuum_when_away: [["vacuum", "robot vacuum", "robot vacuums"]],
  blinds: [["cover", "blind or curtain", "blinds or curtains"]],
};
const STEPS = ["Your home", "Rooms", "People", "Coming and going", "Choices", "Check"];

const S = { step: 0, info: null, a: null, busy: false, error: null, result: null };
const screen = document.getElementById("screen");

// ------------------------------------------------------------ tiny DOM helper (text is never parsed as HTML)
function h(tag, attrs, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === false || v === null || v === undefined) continue;
    if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else if (k === "class") el.className = v;
    else el.setAttribute(k, v === true ? "" : v);
  }
  for (const kid of kids.flat()) if (kid !== null && kid !== undefined && kid !== false)
    el.append(kid instanceof Node ? kid : document.createTextNode(String(kid)));
  return el;
}
const note = (kind, title, ...body) => h("div", { class: "note " + kind }, title ? h("strong", {}, title) : null, ...body);
const topLink = (href, text) => h("a", { href, target: "_top" }, text);

async function api(method, path, body) {
  let resp;
  try {
    resp = await fetch(path, { method, headers: { "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : undefined, cache: "no-store" });
  } catch (e) {
    throw new Error("Could not reach DonkeyHome. Check that Home Assistant is running, then try again.");
  }
  let out;
  try { out = await resp.json(); } catch (e) { throw new Error("DonkeyHome sent an unexpected reply (" + resp.status + ")."); }
  if (!out.ok) throw new Error(out.error || "Something went wrong.");
  return out.data;
}

// ------------------------------------------------------------ start
async function load() {
  render(h("div", { class: "steps" }, h("p", { class: "row" }, h("span", { class: "spinner" }), " Looking at your Home Assistant...")));
  try {
    S.info = await api("GET", "api/discover");
  } catch (e) {
    render(note("bad", "DonkeyHome couldn't talk to Home Assistant.", h("p", {}, e.message)),
      actions(null, h("button", { class: "primary", onclick: load }, "Try again")));
    return;
  }
  const i = S.info, saved = i.saved || {};
  const defaults = Object.fromEntries(i.choices.map(c => [c.key, c.default]));
  const rooms = saved.rooms || i.areas.map(x => x.name).filter(n => NAME_RE.test(n));
  S.a = {
    ...defaults, ...saved,
    home_name: cleanName(saved.home_name || i.home_name) || "Home",
    rooms,
    arrival_room: saved.arrival_room && rooms.includes(saved.arrival_room) ? saved.arrival_room : entranceRoom(rooms),
    notify: saved.notify || i.phones.map(p => p.service),
    leave_delay_minutes: saved.leave_delay_minutes || 10,
  };
  S.a.people = i.people.map(p => cleanName(p.name)).filter(Boolean);
  delete S.a.area_ids; // looked up again when setting up, in case rooms were renamed
  go(0);
}
// The room most likely by the front door.
const entranceRoom = rooms => ["entrance", "hall", "foyer", "living", "lounge"]
  .map(word => rooms.find(r => r.toLowerCase().includes(word))).find(Boolean) || rooms[0] || "";
const cleanName = n => (NAME_RE.test((n || "").trim()) ? n.trim() : "");

// ------------------------------------------------------------ layout
function render(...nodes) {
  screen.replaceChildren(...nodes.flat(2).filter(n => n !== null && n !== undefined && n !== false));
  const bar = document.getElementById("progress");
  bar.replaceChildren(...STEPS.map((label, n) => h("li", {
    class: n + 1 < S.step ? "done" : n + 1 === S.step ? "now" : "", title: label })));
  const focus = screen.querySelector("h1");
  if (focus) { focus.setAttribute("tabindex", "-1"); focus.focus({ preventScroll: true }); }
  window.scrollTo(0, 0);
}
function actions(back, next) {
  return h("div", { class: "actions" },
    back ? h("button", { class: "secondary", onclick: back }, "Back") : h("span"), next);
}
function nextButton(label, ok, onclick) {
  return h("button", { class: "primary", disabled: !ok, onclick }, label);
}
function header(n, title, intro) {
  return [h("div", { class: "step-label" }, `Step ${n} of ${STEPS.length}`), h("h1", {}, title),
    intro ? h("p", { class: "muted" }, intro) : null];
}
function go(n) { S.step = n; S.error = null; SCREENS[n](); }

// ------------------------------------------------------------ screens
const SCREENS = [welcome, homeName, rooms, people, comingGoing, choices, review];

function welcome() {
  const i = S.info;
  render(
    h("div", { class: "hero" }, h("img", { src: "donkey.svg", alt: "" })),
    h("h1", {}, S.info.saved ? "Welcome back!" : "Hi! Let's set up your home."),
    h("p", {}, "I'll ask you six short questions about your home. Then I set up one-tap routines like ",
      h("strong", {}, "Good Night"), " and ", h("strong", {}, "Leaving Home"),
      ", switch the house off when everyone has left, and make you a simple dashboard."),
    h("p", {}, "It takes about 5 minutes. Nothing changes until the very last button, and I keep a backup of anything I touch."),
    S.info.saved ? note("good", "Your previous answers are filled in.", "Change what you like and set it up again.") : null,
    i.warnings.length ? note("warn", "Heads up", h("p", {}, i.warnings.join(" "))) : null,
    actions(null, nextButton("Let's start", true, () => go(1))));
}

function homeName() {
  const input = h("input", { type: "text", id: "home", value: S.a.home_name, maxlength: 40, autocomplete: "off" });
  const err = h("p", { class: "small", style: "color: var(--bad)" });
  const next = () => {
    const v = input.value.trim().replace(/\s+/g, " ");
    if (!NAME_RE.test(v)) { err.textContent = "Please use 1 to 40 letters, numbers or spaces."; input.focus(); return; }
    S.a.home_name = v; go(2);
  };
  input.addEventListener("keydown", e => { if (e.key === "Enter") next(); });
  render(...header(1, "What do you call your home?", "This becomes the name of your dashboard."),
    h("label", { class: "field", for: "home" }, "Home name"), input, err,
    h("p", { class: "muted small" }, "For example: The Tan Home, Beach House, Flat 12."),
    actions(() => go(0), nextButton("Next", true, next)));
}

function rooms() {
  const known = [...new Set([...S.info.areas.map(a => a.name).filter(n => NAME_RE.test(n)), ...S.a.rooms])];
  const ideas = ROOM_IDEAS.filter(r => !known.some(k => k.toLowerCase() === r.toLowerCase()));
  const toggle = name => {
    const has = S.a.rooms.includes(name);
    S.a.rooms = has ? S.a.rooms.filter(r => r !== name) : [...S.a.rooms, name];
    rooms();
  };
  const chip = name => h("button", { class: "chip", "aria-pressed": String(S.a.rooms.includes(name)), onclick: () => toggle(name) },
    h("span", { class: "tick", "aria-hidden": "true" }, S.a.rooms.includes(name) ? "✓" : "+"), name);
  const input = h("input", { type: "text", id: "newroom", placeholder: "Type a room name", maxlength: 40, autocomplete: "off" });
  const err = h("p", { class: "small", style: "color: var(--bad)" });
  const add = () => {
    const v = input.value.trim().replace(/\s+/g, " ");
    if (!NAME_RE.test(v)) { err.textContent = "Please use letters, numbers and spaces only."; return; }
    if (S.a.rooms.some(r => r.toLowerCase() === v.toLowerCase())) { err.textContent = "You already have that room."; return; }
    S.a.rooms = [...S.a.rooms, v]; rooms();
    document.getElementById("newroom").focus();
  };
  input.addEventListener("keydown", e => { if (e.key === "Enter") add(); });
  render(...header(2, "Which rooms do you have?",
      "Tap to choose. Rooms Home Assistant doesn't have yet are created for you."),
    known.length ? [h("h2", {}, "Your rooms"), h("div", { class: "chips" }, known.map(chip))] : null,
    ideas.length ? [h("h2", {}, "More ideas"), h("div", { class: "chips" }, ideas.map(chip))] : null,
    h("h2", {}, "Something else?"),
    h("div", { class: "row" }, input, h("button", { class: "secondary", onclick: add }, "Add")), err,
    h("p", { class: "muted small" }, `${S.a.rooms.length} chosen. You can add or remove rooms any time by running DonkeyHome again.`),
    actions(() => go(1), nextButton("Next", S.a.rooms.length > 0, () => {
      if (!S.a.rooms.includes(S.a.arrival_room)) S.a.arrival_room = entranceRoom(S.a.rooms);
      go(3);
    })));
}

function people() {
  const i = S.info;
  const togglePhone = svc => {
    S.a.notify = S.a.notify.includes(svc) ? S.a.notify.filter(s => s !== svc) : [...S.a.notify, svc];
    people();
  };
  const recheck = async () => {
    try { S.info = { ...S.info, ...(await api("GET", "api/discover")) }; } catch (e) { /* keep what we had */ }
    const found = S.info.phones.map(p => p.service);
    S.a.notify = [...new Set([...S.a.notify.filter(s => found.includes(s)), ...found])];
    people();
  };
  render(...header(3, "Who lives here?", "Home Assistant knows when everyone has left by the Home Assistant app on each person's phone."),
    i.people.length
      ? h("ul", { class: "people" }, i.people.map(p => h("li", {}, h("span", {}, p.name),
          p.tracked ? h("span", { class: "badge good" }, "Phone connected") : h("span", { class: "badge warn" }, "No phone yet"))))
      : note("warn", "Nobody is set up yet.", "That's fine, you can add people later."),
    i.people.some(p => !p.tracked) || !i.people.length
      ? note("warn", "To connect a phone (2 minutes per person):",
          h("ol", {}, h("li", {}, "Install the free ", h("strong", {}, "Home Assistant"), " app from the App Store or Google Play."),
            h("li", {}, "Open it, pick this home and log in. Each person should use their own login: create them under ",
              topLink("/config/person", "Settings > People"), "."),
            h("li", {}, "Allow location ", h("strong", {}, "Always"), " and allow ", h("strong", {}, "notifications"), "."),
            h("li", {}, "Come back here and press ", h("strong", {}, "Check again"), ".")),
          h("button", { class: "secondary", onclick: recheck }, "Check again"))
      : null,
    h("h2", {}, "Send messages to these phones"),
    i.phones.length
      ? h("div", { class: "chips" }, i.phones.map(p => h("button", {
          class: "chip", "aria-pressed": String(S.a.notify.includes(p.service)), onclick: () => togglePhone(p.service) },
          h("span", { class: "tick", "aria-hidden": "true" }, S.a.notify.includes(p.service) ? "✓" : "+"), p.label)))
      : h("p", { class: "muted" }, "No phones with the app yet. Messages will appear under the bell in Home Assistant until you add one; run DonkeyHome again afterwards."),
    actions(() => go(2), nextButton("Next", true, () => go(4))));
}

function comingGoing() {
  const sel = h("select", { id: "arrive" }, S.a.rooms.map(r => h("option", { value: r, selected: r === S.a.arrival_room }, r)));
  sel.addEventListener("change", () => { S.a.arrival_room = sel.value; });
  const delay = h("select", { id: "delay" }, DELAYS.map(m => h("option", { value: m, selected: m === S.a.leave_delay_minutes },
    m === 10 ? "10 minutes (recommended)" : `${m} minutes`)));
  delay.addEventListener("change", () => { S.a.leave_delay_minutes = Number(delay.value); });
  render(...header(4, "Coming and going"),
    h("label", { class: "field", for: "arrive" }, "When you come home after dark, which room should light up?"), sel,
    h("p", { class: "muted small" }, "Usually the room by your front door."),
    h("label", { class: "field", for: "delay" }, "How long after the last person leaves should the house switch off?"), delay,
    h("p", { class: "muted small" }, "A short wait stops it switching off when someone just pops out with the rubbish."),
    note("good", "This starts switched off.",
      "Once everyone's phone is connected, turn on ", h("strong", {}, "Automatic leave and arrive"), " on your dashboard."),
    actions(() => go(3), nextButton("Next", true, () => go(5))));
}

function choiceHint(key) {
  const kinds = CHOICE_DEVICES[key];
  if (!kinds) return "Every Sunday at 10:00, only when something needs a new battery.";
  const parts = kinds.map(([d, one, many]) => [S.info.counts[d] || 0, one, many]).filter(([n]) => n > 0);
  if (!parts.length) return `You have no ${kinds.map(k => k[2]).join(" or ")} yet. It starts working when you add one.`;
  return "You have " + parts.map(([n, one, many]) => `${n} ${n === 1 ? one : many}`).join(" and ") + ".";
}

function choices() {
  render(...header(5, "What should happen?", "Tick what you'd like. Untick anything you're not sure about; you can change it later."),
    S.info.choices.map(c => {
      const box = h("input", { type: "checkbox", checked: !!S.a[c.key] });
      box.addEventListener("change", () => { S.a[c.key] = box.checked; });
      return h("label", { class: "option" }, box,
        h("span", {}, h("span", { class: "title" }, c.question.replace(/\?$/, "")), h("br"), h("span", { class: "hint" }, choiceHint(c.key))));
    }),
    actions(() => go(4), nextButton("Next", true, () => go(6))));
}

function review() {
  const a = S.a, i = S.info;
  const yes = i.choices.filter(c => a[c.key]).map(c => c.question.replace(/\?$/, ""));
  const phones = i.phones.filter(p => a.notify.includes(p.service)).map(p => p.label);
  const newRooms = a.rooms.filter(r => !i.areas.some(x => x.name.toLowerCase() === r.toLowerCase()));
  const pre = h("pre", {}, "Loading...");
  const details = h("details", {}, h("summary", {}, "Show the technical details (the files I'll write)"), pre);
  details.addEventListener("toggle", async () => {
    if (!details.open) return;
    try {
      const files = await api("POST", "api/preview", a);
      pre.textContent = Object.entries(files).map(([name, text]) => `### ${name}\n${text}`).join("\n");
    } catch (e) { pre.textContent = e.message; }
  });
  render(...header(6, "Ready? Here's the plan."),
    h("ul", { class: "summary" },
      h("li", {}, h("span", {}, "Home"), h("span", {}, a.home_name)),
      h("li", {}, h("span", {}, "Rooms"), h("span", {}, a.rooms.join(", "),
        newRooms.length ? h("span", { class: "muted" }, ` (new: ${newRooms.join(", ")})`) : null)),
      h("li", {}, h("span", {}, "Lights up on arrival"), h("span", {}, a.arrival_room)),
      h("li", {}, h("span", {}, "Switch off after"), h("span", {}, `${a.leave_delay_minutes} minutes away`)),
      h("li", {}, h("span", {}, "Messages to"), h("span", {}, phones.length ? phones.join(", ") : "The bell in Home Assistant")),
      h("li", {}, h("span", {}, "You chose"), yes.length ? h("ul", {}, yes.map(y => h("li", {}, y))) : h("span", {}, "Nothing extra"))),
    i.config_status === "custom"
      ? note("warn", "Someone has edited this Home Assistant's settings file by hand.",
          "DonkeyHome will replace configuration.yaml. A copy is kept in the donkeyhome_backups folder. If someone else set up this Home Assistant, ask them first.")
      : null,
    note("good", "You're safe.",
      "I back up every file I change. Home Assistant then checks the new setup; if it finds any problem, I put everything back and nothing changes. Your own automations are never touched."),
    details,
    actions(() => go(5), h("button", { class: "primary", onclick: run }, "Set up my home")));
}

// ------------------------------------------------------------ doing it
async function run() {
  S.step = STEPS.length + 1;
  render(h("h1", {}, "Setting up your home..."),
    h("ul", { class: "steps" }, h("li", {}, h("span", { class: "spinner" }), "Creating rooms, saving a backup, writing and checking. This takes up to a minute.")));
  let result;
  try {
    result = await api("POST", "api/apply", S.a);
  } catch (e) {
    render(h("h1", {}, "That didn't work, but nothing was changed."),
      note("bad", null, h("p", {}, e.message)),
      h("p", {}, "Try again in a minute. If it keeps failing, open the DonkeyHome app's ", h("strong", {}, "Log"), " tab and share what it says when you ask for help."),
      actions(() => go(6), h("button", { class: "primary", onclick: run }, "Try again")));
    return;
  }
  const list = h("ul", { class: "steps" }, result.steps.map(s => h("li", {}, "✅ ", s)));
  const waiting = h("li", {}, h("span", { class: "spinner" }), "Waiting for Home Assistant to come back (about a minute)...");
  list.append(waiting);
  render(h("h1", {}, "Almost there..."), list, h("p", { class: "muted" }, "Please keep this page open."));
  await waitForRestart();
  done(result);
}

async function waitForRestart() {
  const start = Date.now();
  let sawDown = false;
  while (Date.now() - start < 5 * 60 * 1000) {
    await new Promise(r => setTimeout(r, 3000));
    let up = false;
    try { up = (await api("GET", "api/ping")).core; } catch (e) { up = false; }
    if (!up) sawDown = true;
    if (up && (sawDown || Date.now() - start > 45000)) return;
  }
}

function done(result) {
  render(
    h("div", { class: "hero" }, h("img", { src: "donkey.svg", alt: "" })),
    h("h1", {}, "Your home is set up! 🎉"),
    h("p", {}, "Your dashboard ", h("strong", {}, S.a.home_name), " is in the sidebar. Here's what to do next:"),
    h("ol", {},
      h("li", {}, h("strong", {}, "Add your devices"), " (lights, plugs, TV, aircon) under ",
        topLink("/config/integrations/dashboard", "Settings > Devices and services"),
        ". Always pick the right room: the room cards and routines use it."),
      h("li", {}, h("strong", {}, "Try the routines"), " on your dashboard: tap Good Night or Everything Off."),
      h("li", {}, "When everyone's phone shows them at home (", topLink("/config/person", "Settings > People"),
        "), turn on ", h("strong", {}, "Automatic leave and arrive"), " on your dashboard."),
      h("li", {}, "Want to change something? Just open DonkeyHome again. Your answers are remembered.")),
    h("p", { class: "muted small" }, "Your old files are saved in the ", result.backup, " folder."),
    h("div", { class: "actions" }, h("span"), h("a", { class: "primary", href: "/my-home", target: "_top" }, "Open my dashboard")));
}

load();
