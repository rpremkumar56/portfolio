"""Longest single drawing task per file open, with a 4x CPU slowdown. Run: python3 paint_trace.py ../index.html"""
import sys, json, statistics
from playwright.sync_api import sync_playwright
NAMES={"Paint","RasterTask","Layout","UpdateLayerTree","PrePaint","Layerize"}
def run(f):
    with sync_playwright() as p:
        b=p.chromium.launch(); c=b.new_context(viewport={'width':1440,'height':900}); c.route('**/fonts.googleapis.com/**',lambda r:r.abort()); pg=c.new_page()
        cdp=c.new_cdp_session(pg); cdp.send('Emulation.setCPUThrottlingRate',{'rate':4})
        pg.goto('file://'+f); pg.wait_for_timeout(1500)
        worst=[]; over16=[]
        for fid in ["f-01","f-05","f-10","f-14","f-03","f-11"]*2:
            b.start_tracing(page=pg, categories=["devtools.timeline","disabled-by-default-devtools.timeline"])
            pg.click(f'.folder[data-id="{fid}"] .tab'); pg.wait_for_timeout(1100)
            ev=[e for e in json.loads(b.stop_tracing())["traceEvents"] if e.get("name") in NAMES and e.get("ph")=="X"]
            d=[e.get("dur",0)/1000 for e in ev]; worst.append(max(d) if d else 0); over16.append(len([x for x in d if x>16]))
            pg.keyboard.press('Escape'); pg.wait_for_timeout(1400)
        b.close()
    return round(statistics.median(worst),1), round(max(worst),1), round(statistics.mean(over16),2)
for f in sys.argv[1:]:
    m,mx,o=run(f); print(f"{f.split('/')[-1]:18s} median longest task {m} ms · worst {mx} ms · tasks over one frame per open {o}")
