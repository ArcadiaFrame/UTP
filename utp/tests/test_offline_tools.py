"""Model, speech and tutor integration, against mock servers that answer like Ollama and Kokoro-FastAPI.

  python3 utp/tests/test_offline_tools.py

Uses only localhost. Proves the request shapes and the safety checks; it cannot prove
how a particular model or voice sounds.
"""
import csv
import http.server
import json
import os
import pathlib
import shutil
import sys
import tempfile
import threading

UTP = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(UTP.parent))
CALLS = []


class Mock(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        CALLS.append(("GET", self.path, None))
        self._send({"data": [{"id": "mock"}]} if self.path.endswith("/models") else {"voices": ["am_michael"]})

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        CALLS.append(("POST", self.path, body))
        if self.path.endswith("/chat/completions"):
            system = body["messages"][0]["content"]
            if "propose how to build" in system:
                content = json.dumps({"proposals": [
                    {"key": ASK["ok"], "parts": "{water}-{house}", "basis": "water house"},
                    {"key": ASK["ok2"], "parts": "{nonexistent}-{water}", "basis": "bad"},
                    {"key": ASK["ok3"], "parts": "{" + ASK["ok3"] + "}-{water}", "basis": "circular"},
                    {"key": "not-asked", "parts": "{water}-{fire}", "basis": "x"}]})
            elif "Some come out absurd" in system:
                content = json.dumps({"drop": [{"key": ASK["tpl"], "why": "absurd"}]})
            else:
                content = "<think>plan</think>TARGET: Ushal.\nGLOSS: water\nENGLISH: Water.\nNOTE: a first word"
            self._send({"choices": [{"message": {"content": content}}]})
        else:
            self._send(b"RIFF\x00\x00\x00\x00WAVEfake", "audio/wav")


ASK = {}


def main():
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Mock)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_port}"
    os.environ.update(UTP_LLM_URL=base + "/v1", UTP_LLM_MODEL="mock", UTP_KOKORO_URL=base)
    tmp = pathlib.Path(tempfile.mkdtemp())
    os.environ["HOME"] = str(tmp)
    from utp.core import Pack
    from utp.core import llm as L
    from utp.core.builder import Builder
    from utp.core.speech import Kokoro, phonemes
    import utp.tutor as T
    T.HOME = tmp / ".utp"
    report, fails = [], 0

    def check(ok, text):
        nonlocal fails
        fails += not ok
        report.append(f"[{'PASS' if ok else 'FAIL'}] {text}")

    # a private copy of the sample pack
    work = tmp / "packs" / "sample"
    shutil.copytree(UTP / "packs" / "sample", work, ignore=shutil.ignore_patterns("build", "meanings.csv", "exclude.txt"))
    shutil.copytree(UTP / "concepts", tmp / "concepts")
    pack = Pack(work)
    Builder(pack).build()
    rows = pack.rows()
    late = [r for r in rows if r["kind"] == "root" and r["status"] == "generated" and r["era"] in ("Middle", "Modern")
            and r["field"] != "grammar"]
    ASK.update(ok=late[0]["key"], ok2=late[1]["key"], ok3=late[2]["key"],
               tpl=next(r["key"] for r in rows if r["source"].startswith("template")))

    m = L.LLM()
    check(m.available() and m.chat([{"role": "user", "content": "hi"}]).startswith("TARGET"),
          "model client: available(), chat(), reasoning text stripped")
    ok, bad = L.propose(pack, rows, m, limit=3, batch=3, out=tmp / "proposals.csv")
    why = {b["key"]: b["why"] for b in bad}
    check([a["key"] for a in ok] == [ASK["ok"]] and why.get(ASK["ok2"], "").startswith("unknown meaning")
          and why.get(ASK["ok3"]) == "names itself" and why.get("not-asked") == "not asked",
          f"propose(): 1 valid kept, 3 invalid rejected with reasons {why}")
    flags = L.curate(pack, rows, m, limit=10, batch=10, out=tmp / "curation.csv")
    check([f["key"] for f in flags] == [ASK["tpl"]], "curate(): flags only keys it was asked about")

    # apply an approved proposal and an approved drop, then rebuild
    import utp.utp as U
    prop = list(csv.DictReader(open(tmp / "proposals.csv")))
    for p in prop:
        p["approve"] = "yes" if p["key"] == ASK["ok"] else "no"
    with open(tmp / "proposals.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(prop[0]))
        w.writeheader()
        w.writerows(prop)
    cur = list(csv.DictReader(open(tmp / "curation.csv")))
    cur[0]["approve"] = "yes"
    with open(tmp / "curation.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(cur[0]))
        w.writeheader()
        w.writerows(cur)
    U.main(["apply", str(work), str(tmp / "proposals.csv")])
    U.main(["apply", str(work), str(tmp / "curation.csv")])
    rows2, errors, _ = Builder(Pack(work)).build()
    by2 = {r["key"]: r for r in rows2}
    check(not errors and by2[ASK["ok"]]["parts"] == "{water}-{house}" and ASK["tpl"] not in by2,
          f"apply: approved derivation built, approved drop removed, {len(errors)} errors")

    # speech
    vul = Pack("vulcan")
    k = Kokoro()
    wav, ph, dropped = k.say_word(vul, "Sik tok nash-ve kon")
    sent = [c for c in CALLS if c[1] == "/dev/generate_from_phonemes"][-1][2]
    check(wav.startswith(b"RIFF") and sent == {"phonemes": phonemes(vul, "Sik tok nash-ve kon")[0], "voice": "bm_george"}
          and not dropped, f"Kokoro phoneme request for Vulcan: {sent}")
    k.say_text("Hola, ¿cómo estás?", "ef_dora")
    sent = [c for c in CALLS if c[1] == "/v1/audio/speech"][-1][2]
    check(sent["voice"] == "ef_dora" and sent["input"].startswith("Hola"), "Kokoro text request for a human language")

    # tutor: drill twice (second time nothing new is due), then a conversation
    class A:
        reverse = False; speak = True; n = 4; era = None; field = None  # noqa: E702
    std_rows = [r for r in pack.rows()]
    answers = iter([r for r in []])  # noqa
    by = {r["key"]: r for r in std_rows}
    out = []
    first4 = []

    def inp_factory():
        def inp(prompt):
            return "x"
        return inp
    right = T.drill(Pack(work), A, inp=inp_factory(), out=out.append)
    deck = json.loads((tmp / ".utp" / "progress" / "sample.json").read_text())
    check(right == 0 and len(deck) == 4 and all(c["box"] == 0 for c in deck.values()),
          "drill: 4 cards graded wrong go back to box 0, progress saved")
    keys = list(deck)
    answers = iter([by[k]["east"] for k in keys] + ["/quit"])
    right = T.drill(Pack(work), A, inp=lambda p: next(answers), out=out.append)
    check(right >= 2 and (tmp / ".utp" / "audio" / "last.wav").exists(), f"drill: correct answers advance ({right} right), audio played/saved")

    class B:
        pack = "vulcan"; language = None; level = "beginner"; speak = True  # noqa: E702
    said = iter(["Ushal?", "/quit"])
    out = []
    T.talk(B, inp=lambda p: next(said), out=out.append, llm=m)
    tutor_calls = [c for c in CALLS if c[1] == "/v1/chat/completions" and "patient, exacting tutor" in c[2]["messages"][0]["content"]]
    check(tutor_calls and any("Dictionary entries" in x["content"] for x in tutor_calls[-1][2]["messages"])
          and any("target: Ushal." in line for line in out),
          "talk: tutor prompt + dictionary context sent each turn, TARGET line parsed and spoken")
    srv.shutdown()
    shutil.rmtree(tmp)
    print("\n".join(report))
    print("ALL PASS" if not fails else f"{fails} FAILURES")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
