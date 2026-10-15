import sys
from playwright.sync_api import sync_playwright
names=sys.argv[1:] or ["hook","tries","twist","symptoms","solution","overtake","cta"]
with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome",args=["--allow-file-access-from-files"])
    pg=b.new_page(viewport={"width":1080,"height":1920}); pg.on("pageerror",lambda e:print("ERR",e))
    pg.goto("file:///home/claude/reelT/index.html"); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(300)
    for n in names:
        pg.evaluate(f"showStill('{n}')"); pg.wait_for_timeout(100); pg.screenshot(path=f"/home/claude/reelT/out/still_{n}.png")
    b.close()
