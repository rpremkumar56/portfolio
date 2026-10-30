"""Edge-case and smoothness checks for the Files archive. Run: python3 edge_tests.py"""
import os, json
from playwright.sync_api import sync_playwright
SP=os.path.dirname(os.path.abspath(__file__)); URL='file://'+os.path.abspath(os.path.join(SP,'..','index.html'))
results=[]
def check(name, ok, info=""):
    results.append((name,bool(ok),str(info))); print(("PASS " if ok else "FAIL ")+name+(("  — "+str(info)) if (info and not ok) else ""))
def page(b,w,h,**kw):
    ctx=b.new_context(viewport={'width':w,'height':h},**kw); ctx.route('**/fonts.googleapis.com/**', lambda r: r.abort())
    pg=ctx.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.on('console', lambda m: errs.append(m.text) if m.type=='error' and 'ERR_FAILED' not in m.text else None)
    return ctx,pg,errs
LAYOUT="""()=>{ const W=document.documentElement.clientWidth, sw=document.documentElement.scrollWidth;
  const tabs=[...document.querySelectorAll('.folder:not(.out) .tab')];
  const clipped=tabs.filter(t=>{const l=t.querySelector('.tl'); return l.scrollWidth>l.clientWidth+1}).map(t=>t.textContent);
  const out=tabs.filter(t=>{const r=t.getBoundingClientRect(); return r.left<-1||r.right>W+1}).map(t=>t.textContent);
  return {W,sw,clipped,out,n:tabs.length}; }"""
DOC="""()=>{ const W=document.documentElement.clientWidth; const fv=document.getElementById('fv');
  const wide=[...fv.querySelectorAll('.sheet,.exhibit,.figure,.card-note,.panel')].filter(e=>{const r=e.getBoundingClientRect(); return r.right>W+1||r.left<-1}).map(e=>e.className);
  const sw=fv.scrollWidth>fv.clientWidth+1;
  const pc=getComputedStyle(document.getElementById('panel')).backgroundColor;
  const top=document.elementFromPoint(innerWidth/2, innerHeight-70); const covered = top && top.closest('.drawer') ? 1 : 0;
  return {wide,sw,pc,covered}; }"""
with sync_playwright() as p:
    b=p.chromium.launch()
    for (w,h) in [(1440,900),(1280,720),(1024,768),(820,1180),(390,844),(360,740),(844,390)]:
        ctx,pg,errs=page(b,w,h); pg.goto(URL); pg.wait_for_timeout(500)
        L=pg.evaluate(LAYOUT)
        check(f"[{w}x{h}] no sideways scroll", L['sw']<=L['W'], L)
        check(f"[{w}x{h}] all 20 folder tabs inside the screen", L['n']==20 and not L['out'], L['out'])
        check(f"[{w}x{h}] no clipped tab labels", not L['clipped'], L['clipped'])
        if w in (1440,390): pg.screenshot(path=f"{SP}/drawer-{w}.png", full_page=True)
        bad=[]; colour=[]
        for i in range(20):
            fid=f"f-{i+1:02d}"
            pg.evaluate(f"()=>document.querySelector('.folder[data-id=\"{fid}\"] .tab').click()"); pg.wait_for_timeout(950)
            d=pg.evaluate(DOC); fc=pg.evaluate(f"()=>getComputedStyle(document.querySelector('.folder[data-id=\"{fid}\"] .fb')).backgroundColor")
            if d['wide'] or d['sw']: bad.append((fid,d['wide']))
            if d['pc']!=fc: colour.append((fid,fc,d['pc']))
            if d['covered']: bad.append((fid,'drawer shows through the file'))
            if (w,i) in [(1440,4),(390,4),(1440,18)]: pg.screenshot(path=f"{SP}/file-{w}-{fid}.png", full_page=False)
            pg.keyboard.press('Escape'); pg.wait_for_timeout(700)
        check(f"[{w}x{h}] every file fits the screen", not bad, bad[:3])
        check(f"[{w}x{h}] every open file has its folder's colour", not colour, colour[:3])
        check(f"[{w}x{h}] no script errors", not errs, errs[:3]); ctx.close()

    ctx,pg,errs=page(b,1440,900); pg.goto(URL); pg.wait_for_timeout(400)
    pg.click('.chip[data-col=home]'); pg.wait_for_timeout(500)
    check("filter shows only At home (5 files)", pg.evaluate("()=>document.querySelectorAll('.folder:not(.out)').length")==5)
    pg.click('.folder[data-id="f-11"] .tab'); pg.wait_for_timeout(950)
    check("side tabs list the 5 files of the drawer", pg.evaluate("()=>document.querySelectorAll('#sidetabs .stab').length")==5)
    for _ in range(12): pg.keyboard.press('ArrowRight')
    pg.wait_for_timeout(1200)
    check("fast ArrowRight presses stop at the last file of the drawer", pg.inner_text('#fvTitle')=="On the workbench", pg.inner_text('#fvTitle'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(800)
    check("Esc closes and focus returns to that folder's tab", pg.evaluate("()=>document.getElementById('fv').hidden && document.activeElement.closest('.folder')?.dataset.id==='f-14'"))
    pg.evaluate("()=>{const t=document.querySelectorAll('.folder:not(.out) .tab'); t[0].click(); t[1].click(); t[2].click();}"); pg.wait_for_timeout(1300)
    check("rapid clicks open only one file", pg.evaluate("()=>!document.getElementById('fv').hidden && document.querySelectorAll('.flyer').length===0"))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(800)
    check("no script errors (navigation)", not errs, errs[:3]); ctx.close()

    ctx,pg,errs=page(b,1440,900); pg.goto(URL+'#f-05'); pg.wait_for_timeout(1100)
    check("deep link #f-05 opens Ramp-down Radar", pg.inner_text('#fvTitle')=="Ramp-down Radar")
    pg.click('[data-tool=hl]')
    pg.evaluate("""()=>{ const p=document.querySelector('#doc .sheet p.mk:not(.lede)'); const t=p.firstChild; const r=document.createRange(); r.setStart(t,0); r.setEnd(t,Math.min(30,t.length)); const s=getSelection(); s.removeAllRanges(); s.addRange(r); document.dispatchEvent(new MouseEvent('mouseup')); }""")
    pg.wait_for_timeout(200)
    check("highlighter marks selected text", pg.evaluate("()=>document.querySelectorAll('#doc .mark.hl').length")>=1)
    pg.reload(); pg.wait_for_timeout(1100)
    check("marks survive a reload", pg.evaluate("()=>document.querySelectorAll('#doc .mark.hl').length")>=1)
    pg.evaluate("()=>localStorage.setItem('prfiles.v1.mark.f-05:oldhash','<p>OLD TEXT</p>')"); pg.reload(); pg.wait_for_timeout(1100)
    check("marks saved against old file text are ignored", 'OLD TEXT' not in pg.content())
    check("no script errors (marks)", not errs, errs[:3]); ctx.close()

    ctx,pg,errs=page(b,390,844,has_touch=True,is_mobile=True); pg.goto(URL+'#f-10'); pg.wait_for_timeout(1100)
    check("phone deep link opens the clinic file", pg.inner_text('#fvTitle')=="The paper register")
    pg.set_viewport_size({'width':844,'height':390}); pg.wait_for_timeout(500)
    check("rotating the phone keeps the same file open", pg.inner_text('#fvTitle')=="The paper register" and not errs, errs[:2]); ctx.close()

    ctx=b.new_context(viewport={'width':1280,'height':800}); ctx.add_init_script("Object.defineProperty(window,'localStorage',{get(){throw new Error('blocked')}})")
    pg=ctx.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e))); pg.goto(URL); pg.wait_for_timeout(400)
    pg.click('.folder[data-id="f-02"] .tab'); pg.wait_for_timeout(950); pg.click('#nextBtn'); pg.wait_for_timeout(500)
    check("works with browser storage blocked", not errs and pg.inner_text('#fvTitle')=="Finance Ops AI-Assist", errs[:2]); ctx.close()

    ctx=b.new_context(java_script_enabled=False); pg=ctx.new_page(); pg.goto(URL)
    check("content readable with JavaScript off", "Ramp-down Radar" in pg.inner_text('body')); ctx.close()

    ctx,pg,errs=page(b,1280,800,reduced_motion='reduce'); pg.goto(URL); pg.wait_for_timeout(300)
    pg.click('.folder[data-id="f-07"] .tab'); pg.wait_for_timeout(200)
    check("reduced motion: file opens at once", not pg.evaluate("()=>document.getElementById('fv').hidden") and not errs); ctx.close()

    for (w,h) in [(1440,900),(390,844)]:
        ctx,pg,errs=page(b,w,h); pg.goto(URL); pg.wait_for_timeout(200); pg.click('#idli'); pg.wait_for_timeout(500)
        hearts=pg.evaluate("()=>document.querySelectorAll('#rack .heart').length"); out=[]
        for i in range(40):
            pg.wait_for_timeout(250)
            r=pg.evaluate("()=>{const a=document.getElementById('rack').getBoundingClientRect(), d=document.getElementById('idli').getBoundingClientRect(); return [d.left-a.left, a.right-d.right]}")
            if r[0]<12 or r[1]<12: out.append(r)
        check(f"[{w}] Idli stays inside her rack for 10 s", not out, out[:3]); check(f"[{w}] tapping Idli makes hearts", hearts>0)
        ctx.close()


    # back navigation and big numbers
    ctx,pg,errs=page(b,1440,900); pg.goto(URL); pg.wait_for_timeout(400)
    pg.click('.folder[data-id="f-09"] .tab'); pg.wait_for_timeout(950)
    sizes=pg.evaluate("()=>[...document.querySelectorAll('.ex-num')].map(e=>parseFloat(getComputedStyle(e).fontSize))")
    check(f"exhibit numbers are large on desktop ({sizes})", sizes and min(sizes)>=44, sizes)
    pg.evaluate("()=>{const f=document.getElementById('fv'); f.scrollTop=f.scrollHeight}"); pg.wait_for_timeout(300)
    vis=pg.evaluate("()=>{const r=document.getElementById('closeBtn').getBoundingClientRect(); return r.top>=0 && r.bottom<=innerHeight}")
    check("the back button stays in view after scrolling to the end", vis)
    pg.go_back(); pg.wait_for_timeout(900)
    check("the browser Back button closes the file", pg.evaluate("()=>document.getElementById('fv').hidden"))
    pg.go_forward(); pg.wait_for_timeout(1100)
    check("the browser Forward button reopens it", pg.evaluate("()=>!document.getElementById('fv').hidden") and pg.inner_text('#fvTitle')=="Enterprise transformation", pg.inner_text('#fvTitle'))
    pg.click('#closeBtn2'); pg.wait_for_timeout(900)
    check("the bottom back button closes the file", pg.evaluate("()=>document.getElementById('fv').hidden"))
    check("no script errors (back navigation)", not errs, errs[:3]); ctx.close()
    ctx,pg,errs=page(b,390,844,has_touch=True,is_mobile=True); pg.goto(URL); pg.wait_for_timeout(400)
    pg.click('.folder[data-id="f-01"] .tab'); pg.wait_for_timeout(950)
    sizes=pg.evaluate("()=>[...document.querySelectorAll('.ex-num')].map(e=>parseFloat(getComputedStyle(e).fontSize))")
    check(f"exhibit numbers are large on a phone ({sizes})", sizes and min(sizes)>=40, sizes)
    pg.screenshot(path=f"{SP}/exhibits-390.png", full_page=False)
    pg.evaluate("()=>{const f=document.getElementById('fv'); f.scrollTop=700}"); pg.wait_for_timeout(300); pg.screenshot(path=f"{SP}/exhibits-390b.png")
    ctx.close()

    # smoothness of the open flight
    ctx,pg,errs=page(b,1440,900); pg.goto(URL); pg.wait_for_timeout(500); gaps=[]; block=[]
    for fid in ["f-01","f-05","f-10","f-15"]:
        r=pg.evaluate("""(fid)=>new Promise(res=>{ const fr=[]; const t0=performance.now(); const loop=t=>{ fr.push(t); if(t-t0<1200) requestAnimationFrame(loop); else res({fr,t0,click}); };
          requestAnimationFrame(loop); document.querySelector('.folder[data-id="'+fid+'"] .tab').click(); var click=performance.now()-t0; })""", fid)
        fr=r['fr']; gaps+= [b2-a for a,b2 in zip(fr,fr[1:])]; block.append(r['click'])
        pg.keyboard.press('Escape'); pg.wait_for_timeout(800)
    slow=[g for g in gaps if g>34]
    check(f"click blocks the page for under 50 ms (worst {max(block):.0f} ms)", max(block)<50)
    check(f"open flight: under 5 slow frames ({len(slow)} slow, worst {max(gaps):.0f} ms)", len(slow)<5)
    ctx.close(); b.close()
fails=[r for r in results if not r[1]]
print(f"\n{len(results)-len(fails)} passed, {len(fails)} failed")
