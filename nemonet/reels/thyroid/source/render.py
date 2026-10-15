import sys, os, math
from playwright.sync_api import sync_playwright
FPS=30
mode=sys.argv[1]  # "test t1 t2 ..." or "frames start end"
os.makedirs("/home/claude/reelT/frames",exist_ok=True); os.makedirs("/home/claude/reelT/test",exist_ok=True)
with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome",args=["--allow-file-access-from-files"])
    pg=b.new_page(viewport={"width":1080,"height":1920})
    errs=[]; pg.on("pageerror",lambda e:errs.append(str(e))); pg.on("console",lambda m: errs.append(m.text) if m.type=="error" else None)
    pg.goto("file:///home/claude/reelT/anim.html"); pg.evaluate("document.fonts.ready"); pg.wait_for_function("window.ready===true",timeout=10000)
    if mode=="test":
        for t in sys.argv[2:]:
            pg.evaluate(f"seek({t})"); pg.screenshot(path=f"/home/claude/reelT/test/t_{float(t):05.2f}.png")
    else:
        a,z=int(sys.argv[2]),int(sys.argv[3])
        for f in range(a,z):
            pg.evaluate(f"seek({f/FPS})"); pg.screenshot(path=f"/home/claude/reelT/frames/f{f:04d}.jpg",type="jpeg",quality=94)
            if f%60==0: print(f,flush=True)
    if errs: print("ERRORS:",errs[:5])
    b.close()
