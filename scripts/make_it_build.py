"""Make the IT review copy of the tool: same page, no mail connection, dummy data only.
Usage: python3 scripts/make_it_build.py  ->  app/DP_World_Platform_IT.html
The page sees <meta name="dpw-build" content="it"> and turns off Gmail (inbox uses the offline dummy copy,
no Pull from Gmail, draft links open a normal compose window)."""
import pathlib, sys
src = pathlib.Path("app/DP_World_Platform_DEMO.html"); out = pathlib.Path("app/DP_World_Platform_IT.html")
s = src.read_text(encoding="utf-8")
def rep(a, b):
    global s
    if s.count(a) != 1: sys.exit(f"marker not found once: {a[:60]}")
    s = s.replace(a, b)
rep("<title>DP World Egypt Platform</title>", '<title>DP World Egypt Platform (IT review)</title>\n<meta name="dpw-build" content="it">')
rep('<div class="demoBar" role="note">DEMO · ', '<div class="demoBar" role="note">IT REVIEW COPY · no mail connection · ')
out.write_text(s, encoding="utf-8"); print("written", out, len(s), "bytes")
