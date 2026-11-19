/* The look around the work: the PADD layout, the station header (stardate, readouts, link) and interface sounds.
   Settings > Appearance keeps the choices; the server hands them to every page as window.UTP_LOOK. */
const LOOK = Object.assign({layout: "auto", year: 2371, sounds: false, palette: "amber-blue", shape: "cut"}, window.UTP_LOOK || {});
const PALETTES = {"amber-blue": "Amber and blue on black", amber: "Amber on black", blue: "Blue on black"};
const SHAPES = {cut: "Cut corners", square: "Square", rounded: "Rounded"};
function applyStyle() {
  const d = document.documentElement;
  d.dataset.palette = LOOK.palette; d.dataset.shape = LOOK.shape;
  document.querySelectorAll("iframe").forEach(f => { try {
    const fd = f.contentDocument.documentElement; fd.dataset.palette = LOOK.palette; fd.dataset.shape = LOOK.shape; } catch (e) { } });
}

/* ---------- PADD layout ---------- */
const narrow = window.matchMedia("(max-width: 900px)");
function applyLayout() {
  const padd = LOOK.layout === "padd" || (LOOK.layout === "auto" && narrow.matches);
  document.documentElement.dataset.layout = padd ? "padd" : "desktop";
  if (!padd) document.documentElement.classList.remove("side-open");
}
narrow.addEventListener("change", applyLayout);
$("#menu-btn").onclick = () => document.documentElement.classList.toggle("side-open");
$("#scrim").onclick = () => document.documentElement.classList.remove("side-open");
document.addEventListener("click", e => {          // on a PADD, choosing something in the drawer closes it
  if (document.documentElement.dataset.layout === "padd" && e.target.closest(".side a, .side .item:not([data-dir=true])"))
    document.documentElement.classList.remove("side-open");
});

/* ---------- stardate: the TNG-era convention, 1000 units a year from 2323, for the in-universe year you set ---------- */
function stardate(now = new Date(), year = LOOK.year) {
  const start = new Date(now.getFullYear(), 0, 1), end = new Date(now.getFullYear() + 1, 0, 1);
  const frac = (now - start) / (end - start);
  return (1000 * (Number(year) - 2323) + 1000 * frac).toFixed(1);
}
function station() {
  $("#st-date").textContent = `Stardate ${stardate()}`;
  const l = S.langs.find(x => x.id === S.lang);
  $("#st-readout").textContent = l ? `${l.language} · ${(l.entries || 0).toLocaleString()} entries · ${l.branches.length} branches`
    : `${S.langs.filter(x => !x.fixture).length} languages on file`;
  const dot = $("#model-dot");
  $("#st-dot").className = dot ? dot.className : "dot";
  $("#st-link").textContent = dot && dot.classList.contains("ok") ? "Link: " + $("#model-label").textContent
    : dot && dot.classList.contains("bad") ? "Link: no answer" : "Link";
}
setInterval(station, 15000);
new MutationObserver(station).observe($("#model-dot"), {attributes: true});
document.addEventListener("click", () => setTimeout(station, 50));

/* ---------- interface sounds: short tones made on the spot, nothing recorded ---------- */
let audio = null;
function tone(kind) {
  if (!LOOK.sounds) return;
  try {
    audio = audio || new (window.AudioContext || window.webkitAudioContext)();
    const o = audio.createOscillator(), g = audio.createGain(), t = audio.currentTime;
    const [a, b, len] = {press: [880, 1320, .07], done: [660, 990, .14], fail: [440, 300, .18]}[kind] || [880, 1320, .07];
    o.type = "sine"; o.frequency.setValueAtTime(a, t); o.frequency.exponentialRampToValueAtTime(b, t + len);
    g.gain.setValueAtTime(.0001, t); g.gain.exponentialRampToValueAtTime(.06, t + .01); g.gain.exponentialRampToValueAtTime(.0001, t + len);
    o.connect(g).connect(audio.destination); o.start(t); o.stop(t + len + .02);
  } catch (e) { }
}
document.addEventListener("click", e => { if (e.target.closest("button, .ws-steps button, .lang a, .tab")) tone("press"); });

function setLook(patch, save = true) {
  Object.assign(LOOK, patch); window.UTP_LOOK = LOOK;
  applyLayout(); applyStyle(); station();
  if (save) api("/api/settings", {app: patch}).catch(() => { });
}
/* ---------- page changes: a quick scan-in on the view that opens ---------- */
function scanIn(el) {
  if (!el || document.documentElement.dataset.theme !== "terminal") return;
  el.classList.remove("scan-in"); void el.offsetWidth; el.classList.add("scan-in");
}
const _activate = activate;
activate = function (id) {
  _activate(id);
  scanIn(document.querySelector(".view:not([hidden])"));
};
new MutationObserver(() => scanIn($("#ws-pane"))).observe($("#workshop-view"), {childList: true});

applyLayout(); applyStyle();
setTimeout(station, 600);
