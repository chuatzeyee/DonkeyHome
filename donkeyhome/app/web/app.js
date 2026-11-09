// DonkeyHome setup screens. Plain JavaScript, no build step. Every URL is relative (Home Assistant ingress).
// Look: the DonkeyHome dashboard's (serif question, pill cards, pink room pills, a floating dock with Back/Next).
"use strict";

const NAME_RE = /^[A-Za-z0-9][A-Za-z0-9 '&-]{0,39}$/;
const ROOM_IDEAS = ["Living Room", "Kitchen", "Bedroom", "Bathroom", "Dining Room", "Study", "Kids Room",
  "Entrance", "Hallway", "Laundry", "Garage", "Balcony", "Garden"];
const DELAYS = [5, 10, 15, 20, 30, 60];
// Per yes/no choice: its icon, a short title, and which devices it needs ("you have 2 lights").
const CHOICE_INFO = {
  lights_off_when_leaving: ["lightbulbOutline", "Lights off when everyone leaves", [["light", "light", "lights"]]],
  climate_off_when_leaving: ["snowflake", "Aircon, heating and fans off when everyone leaves",
    [["climate", "aircon or heater", "aircons or heaters"], ["fan", "fan", "fans"]]],
  media_off_when_leaving: ["television", "TVs and speakers off when everyone leaves", [["media_player", "TV or speaker", "TVs or speakers"]]],
  lock_when_leaving: ["lockOutline", "Lock the doors when leaving and at Good Night", [["lock", "door lock", "door locks"]]],
  vacuum_when_away: ["robotVacuum", "Robot vacuum cleans when everyone leaves", [["vacuum", "robot vacuum", "robot vacuums"]]],
  blinds: ["blindsHorizontal", "Blinds open at Good Morning, close at Good Night", [["cover", "blind or curtain", "blinds or curtains"]]],
  battery_check: ["batteryLow", "A weekly list of batteries to change", null],
};
const STEPS = 6;

const S = { step: 0, info: null, a: null };
const page = document.getElementById("page");
const dock = document.getElementById("dock");

// ------------------------------------------------------------ tiny DOM helpers (text is never parsed as HTML)
function h(tag, attrs, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === false || v === null || v === undefined) continue;
    if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else if (k === "class") el.className = v;
    else el.setAttribute(k, v === true ? "" : v);
  }
  for (const kid of kids.flat(3)) if (kid !== null && kid !== undefined && kid !== false)
    el.append(kid instanceof Node ? kid : document.createTextNode(String(kid)));
  return el;
}
function icon(name) {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("aria-hidden", "true");
  const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
  path.setAttribute("d", ICONS[name] || ICONS.homeHeart);
  svg.append(path);
  return svg;
}
const v = (text) => h("span", { class: "v" }, text); // a value pill inside a sentence
const card = (kind, title, ...body) => h("div", { class: "card " + (kind || "") }, title ? h("strong", { class: "h" }, title) : null, ...body);
const topLink = (href, text) => h("a", { href, target: "_top" }, text);
// A pill card: icon circle, title, grey line, optional right-hand part.
function pill({ ic, title, sub, end, on, onclick, icClass, label }) {
  const kids = [h("span", { class: "ic " + (icClass || "") }, icon(ic)),
    h("span", {}, h("span", { class: "t" }, title), sub ? h("span", { class: "s", style: "display:block" }, sub) : null),
    end || h("span")];
  return onclick
    ? h("button", { class: "pill" + (on ? " on" : ""), "aria-pressed": on === undefined ? null : String(on), "aria-label": label, onclick }, kids)
    : h("div", { class: "pill" + (on ? " on" : "") }, kids);
}

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

// ------------------------------------------------------------ layout
function render(content, nav) {
  const top = S.step >= 1 && S.step <= STEPS
    ? [h("div", { class: "top" }, h("img", { src: "donkey.svg", alt: "" }), h("span", { class: "brand" }, "DonkeyHome"),
        h("span", { class: "count" }, `${S.step} of ${STEPS}`)),
       h("div", { class: "bar", "aria-hidden": "true" }, Array.from({ length: STEPS }, (_, n) => h("i", { class: n < S.step ? "on" : "" })))]
    : [h("div", { class: "top" }, h("img", { src: "donkey.svg", alt: "" }), h("span", { class: "brand" }, "DonkeyHome"))];
  page.replaceChildren(...[top, content].flat(3).filter(Boolean));
  dock.replaceChildren();
  dock.hidden = !nav;
  if (nav) {
    if (nav.back) dock.append(h("button", { class: "btn round", "aria-label": "Back", onclick: nav.back }, icon("arrowLeft")));
    else if (nav.hint) dock.append(h("span", { class: "hint" }, nav.hint));
    if (nav.next) dock.append(h("button", { class: "btn dark", disabled: nav.ok === false, onclick: nav.next },
      nav.label || "Next", icon(nav.icon || "arrowRight")));
  }
  const title = page.querySelector("h1");
  if (title) { title.setAttribute("tabindex", "-1"); title.focus({ preventScroll: true }); }
}
function go(n) { S.step = n; SCREENS[n](); window.scrollTo(0, 0); }

// ------------------------------------------------------------ start
async function load() {
  S.step = 0;
  render([h("div", { class: "row", style: "margin-top:40px" }, h("span", { class: "spinner" }), "Looking at your Home Assistant...")]);
  try {
    S.info = await api("GET", "api/discover");
  } catch (e) {
    render([h("h1", {}, "I can't reach Home Assistant"), h("p", { class: "lead" }, e.message)],
      { next: load, label: "Try again", icon: "arrowRight" });
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

// ------------------------------------------------------------ screens
const SCREENS = [welcome, homeName, rooms, people, comingGoing, choices, review];

function welcome() {
  const i = S.info;
  render([
    h("img", { class: "hero-img", src: "donkey.svg", alt: "" }),
    h("h1", {}, i.saved ? "Welcome back" : "Let's set up your home"),
    h("p", { class: "sentence" }, "Six easy questions, about ", v("5 minutes"), ". Then you get ",
      v("one-tap routines"), ", a house that ", v("switches itself off"), " when everyone leaves, and a dashboard that looks like this."),
    h("div", { class: "pills" },
      pill({ ic: "shieldCheckOutline", title: "Nothing changes until the end", sub: "And I back up anything I touch." }),
      i.saved ? pill({ ic: "pencilOutline", title: "Your answers are filled in", sub: "Change what you like and set it up again." }) : null),
    i.warnings.length ? [h("div", { class: "gap" }), card("warn", "Heads up", i.warnings.join(" "))] : null,
  ], { hint: "Tap to begin", next: () => go(1), label: "Let's start" });
}

function homeName() {
  const input = h("input", { type: "text", id: "home", value: S.a.home_name, maxlength: 40, autocomplete: "off",
    "aria-label": "Home name" });
  const err = h("p", { class: "error", role: "alert" });
  const next = () => {
    const val = input.value.trim().replace(/\s+/g, " ");
    if (!NAME_RE.test(val)) { err.textContent = "Please use 1 to 40 letters, numbers or spaces."; input.focus(); return; }
    S.a.home_name = val; go(2);
  };
  input.addEventListener("keydown", e => { if (e.key === "Enter") next(); });
  render([
    h("h1", {}, "What do you call your home?"),
    h("p", { class: "lead" }, "It becomes your dashboard's name. Like The Tan Home, Beach House or Flat 12."),
    input, err,
  ], { back: () => go(0), next });
}

function rooms() {
  const known = [...new Set([...S.info.areas.map(a => a.name).filter(n => NAME_RE.test(n)), ...S.a.rooms])];
  const ideas = ROOM_IDEAS.filter(r => !known.some(k => k.toLowerCase() === r.toLowerCase()));
  const toggle = name => {
    S.a.rooms = S.a.rooms.includes(name) ? S.a.rooms.filter(r => r !== name) : [...S.a.rooms, name];
    rooms();
  };
  const chip = name => h("button", { class: "chip", "aria-pressed": String(S.a.rooms.includes(name)), onclick: () => toggle(name) }, name);
  const input = h("input", { type: "text", id: "newroom", placeholder: "Another room", maxlength: 40, autocomplete: "off",
    "aria-label": "Another room" });
  const err = h("p", { class: "error", role: "alert" });
  const add = () => {
    const val = input.value.trim().replace(/\s+/g, " ");
    if (!NAME_RE.test(val)) { err.textContent = "Please use letters, numbers and spaces only."; return; }
    if (S.a.rooms.some(r => r.toLowerCase() === val.toLowerCase())) { err.textContent = "You already have that room."; return; }
    S.a.rooms = [...S.a.rooms, val]; rooms();
    document.getElementById("newroom").focus();
  };
  input.addEventListener("keydown", e => { if (e.key === "Enter") add(); });
  const n = S.a.rooms.length;
  render([
    h("h1", {}, "Which rooms do you have?"),
    h("p", { class: "lead" }, "Tap to choose. Any room Home Assistant doesn't have yet, I'll create."),
    known.length ? [h("h2", {}, "Your rooms"), h("div", { class: "chips" }, known.map(chip))] : null,
    ideas.length ? [h("h2", {}, "More ideas"), h("div", { class: "chips" }, ideas.map(chip))] : null,
    h("h2", {}, "Something else?"),
    h("div", { class: "row" }, input, h("button", { class: "btn add round", "aria-label": "Add room", onclick: add }, icon("plus"))), err,
  ], { back: () => go(1), ok: n > 0, label: n ? `Next, ${n} room${n === 1 ? "" : "s"}` : "Pick a room", next: () => {
    if (!S.a.rooms.includes(S.a.arrival_room)) S.a.arrival_room = entranceRoom(S.a.rooms);
    go(3);
  } });
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
  const missing = !i.people.length || i.people.some(p => !p.tracked);
  render([
    h("h1", {}, "Who lives here?"),
    h("p", { class: "lead" }, "The Home Assistant app on each phone tells the house when everyone has left."),
    i.people.length
      ? h("div", { class: "pills" }, i.people.map(p => pill({
          ic: p.tracked ? "cellphone" : "accountOutline", icClass: p.tracked ? "ok" : "wait",
          title: p.name, sub: p.tracked ? "Phone connected" : "No phone yet" })))
      : null,
    missing ? [h("div", { class: "gap" }), card("warn", "Connect a phone, 2 minutes each",
      h("ol", {},
        h("li", {}, "Install the free ", h("strong", {}, "Home Assistant"), " app from the App Store or Google Play."),
        h("li", {}, "Open it and log in. Everyone gets their own login: add them under ", topLink("/config/person", "Settings > People"), "."),
        h("li", {}, "Allow location ", h("strong", {}, "Always"), " and allow ", h("strong", {}, "notifications"), ".")),
      h("button", { class: "btn soft", onclick: recheck }, "Check again"))] : null,
    h("h2", {}, "Send messages to"),
    i.phones.length
      ? h("div", { class: "pills" }, i.phones.map(p => pill({
          ic: "cellphone", title: p.label, sub: S.a.notify.includes(p.service) ? "Gets messages" : "No messages",
          on: S.a.notify.includes(p.service), onclick: () => togglePhone(p.service),
          end: h("span", { class: "tick" }, S.a.notify.includes(p.service) ? icon("check") : null) })))
      : h("p", { class: "muted" }, "No phones with the app yet. Until then, messages appear under the bell in Home Assistant. Open DonkeyHome again once a phone is connected."),
  ], { back: () => go(2), next: () => go(4) });
}

function comingGoing() {
  const sel = h("select", { id: "arrive" }, S.a.rooms.map(r => h("option", { value: r, selected: r === S.a.arrival_room }, r)));
  sel.addEventListener("change", () => { S.a.arrival_room = sel.value; });
  const delay = h("select", { id: "delay" }, DELAYS.map(m => h("option", { value: m, selected: m === S.a.leave_delay_minutes },
    m === 10 ? "10 minutes (recommended)" : `${m} minutes`)));
  delay.addEventListener("change", () => { S.a.leave_delay_minutes = Number(delay.value); });
  render([
    h("h1", {}, "Coming and going"),
    h("p", { class: "lead" }, "Two small things about leaving and coming home."),
    h("label", { class: "field", for: "arrive" }, "Light up this room when I'm home after dark"), sel,
    h("div", { class: "gap" }),
    h("label", { class: "field", for: "delay" }, "Switch the house off when everyone's been gone for"), delay,
    h("div", { class: "gap" }),
    pill({ ic: "mapMarkerRadiusOutline", title: "Starts switched off", sub: "Turn on Auto leave on your dashboard once every phone is connected." }),
  ], { back: () => go(3), next: () => go(5) });
}

function choiceHint(key) {
  const kinds = CHOICE_INFO[key][2];
  if (!kinds) return "Sundays at 10:00, only when one is low.";
  const have = kinds.map(([d, one, many]) => [S.info.counts[d] || 0, one, many]).filter(([n]) => n > 0);
  if (!have.length) return `No ${kinds.map(k => k[2]).join(" or ")} yet. Works once you add one.`;
  return "You have " + have.map(([n, one, many]) => `${n} ${n === 1 ? one : many}`).join(" and ") + ".";
}

function choices() {
  const y = window.scrollY;
  render([
    h("h1", {}, "What should happen?"),
    h("p", { class: "lead" }, "Tap to switch each one on or off. You can change them any time."),
    h("div", { class: "pills" }, S.info.choices.map(c => {
      const [ic, title] = CHOICE_INFO[c.key] || ["homeHeart", c.question];
      const on = !!S.a[c.key];
      return pill({ ic, title, sub: choiceHint(c.key), on, label: title,
        onclick: () => { S.a[c.key] = !on; choices(); },
        end: h("span", { class: "tick" }, on ? icon("check") : null) });
    })),
  ], { back: () => go(4), next: () => go(6) });
  window.scrollTo(0, y); // tapping a choice keeps your place
}

function review() {
  const a = S.a, i = S.info;
  const phones = i.phones.filter(p => a.notify.includes(p.service)).map(p => p.label);
  const newRooms = a.rooms.filter(r => !i.areas.some(x => x.name.toLowerCase() === r.toLowerCase()));
  const yes = i.choices.filter(c => a[c.key]);
  const pre = h("pre", {}, "Loading...");
  const details = h("details", {}, h("summary", {}, "Show the files I'll write"), pre);
  details.addEventListener("toggle", async () => {
    if (!details.open) return;
    try {
      const files = await api("POST", "api/preview", a);
      pre.textContent = Object.entries(files).map(([name, text]) => `### ${name}\n${text}`).join("\n");
    } catch (e) { pre.textContent = e.message; }
  });
  const list = (items) => items.flatMap((x, n) => n === 0 ? [x] : [n === items.length - 1 ? " and " : ", ", x]);
  render([
    h("h1", {}, "Here's the plan"),
    h("p", { class: "sentence" },
      "This is ", v(a.home_name), " with ", list(a.rooms.map(v)), ". ",
      newRooms.length ? ["I'll create ", list(newRooms.map(v)), ". "] : null,
      "When everyone's been gone ", v(`${a.leave_delay_minutes} minutes`), ", the house switches off. Coming home after dark lights up ",
      v(a.arrival_room), ". Messages go to ", phones.length ? list(phones.map(v)) : v("the bell in Home Assistant"), "."),
    h("h2", {}, "Switched on"),
    h("div", { class: "pills" }, yes.length
      ? yes.map(c => pill({ ic: CHOICE_INFO[c.key][0], title: CHOICE_INFO[c.key][1], on: true }))
      : pill({ ic: "close", title: "Nothing extra", sub: "Only the routines and the dashboard." })),
    h("div", { class: "gap" }),
    i.config_status === "custom"
      ? card("warn", "Someone edited this Home Assistant by hand",
          "I'll replace configuration.yaml and keep a copy in the donkeyhome_backups folder. If someone else set up this Home Assistant, ask them first.")
      : null,
    pill({ ic: "shieldCheckOutline", title: "You're safe", sub: "I back up every file I change. If Home Assistant finds any problem, I put everything back." }),
    details,
  ], { back: () => go(5), next: run, label: "Set up my home", icon: "check" });
}

// ------------------------------------------------------------ doing it
async function run() {
  S.step = STEPS + 1;
  render([h("h1", {}, "Setting up your home"),
    h("div", { class: "pills" }, pill({ ic: "timerSandComplete", title: "Working on it", sub: "Rooms, backup, files, check. Up to a minute.",
      end: h("span", { class: "spinner" }) }))]);
  let result;
  try {
    result = await api("POST", "api/apply", S.a);
  } catch (e) {
    render([h("h1", {}, "That didn't work, but nothing changed"),
      card("bad", null, e.message),
      h("p", { class: "lead" }, "Try again in a minute. If it keeps failing, open the DonkeyHome app's Log tab and share it when you ask for help.")],
      { back: () => go(6), next: run, label: "Try again", icon: "arrowRight" });
    return;
  }
  const waiting = pill({ ic: "timerSandComplete", title: "Restarting Home Assistant", sub: "About a minute. Keep this page open.",
    end: h("span", { class: "spinner" }) });
  render([h("h1", {}, "Almost there"),
    h("div", { class: "pills" }, result.steps.map(s => pill({ ic: "check", icClass: "ok", title: s })), waiting)]);
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
  S.step = STEPS + 2;
  render([
    h("img", { class: "hero-img", src: "donkey.svg", alt: "" }),
    h("h1", {}, "Your home is ready"),
    h("p", { class: "sentence" }, "Your dashboard ", v(S.a.home_name), " is in the sidebar. Three things to do next:"),
    h("div", { class: "pills" },
      pill({ ic: "lightbulbOutline", title: "Add your devices", sub: "Settings > Devices and services. Always pick the room." }),
      pill({ ic: "power", title: "Try a routine", sub: "Tap Good Night or Everything Off on your dashboard." }),
      pill({ ic: "mapMarkerRadiusOutline", title: "Turn on Auto leave", sub: "Once every phone shows its person at home." })),
    h("div", { class: "gap" }),
    h("p", { class: "muted small" }, "Want to change something? Open DonkeyHome again. Your old files are in ", result.backup, "."),
  ], { hint: "All done", next: () => { window.top.location.href = "/my-home/home"; }, label: "Open dashboard", icon: "arrowRight" });
}

load();
