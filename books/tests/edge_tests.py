import os, json, time
from playwright.sync_api import sync_playwright
SP=os.path.dirname(os.path.abspath(__file__)); URL='file://'+os.path.abspath(os.path.join(SP,'..','index.html'))
results=[]
def check(name, ok, info=""):
    results.append((name, bool(ok), info)); print(("PASS " if ok else "FAIL ")+name+("  — "+str(info) if info else ""))
def page(b, w, h, **kw):
    ctx=b.new_context(viewport={'width':w,'height':h}, **kw)
    ctx.route('**/fonts.googleapis.com/**', lambda r: r.abort())
    pg=ctx.new_page(); errs=[]
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.on('console', lambda m: errs.append(m.text) if m.type=='error' and 'ERR_FAILED' not in m.text else None)
    return ctx, pg, errs
JS_LAYOUT = """() => {
  const W=document.documentElement.clientWidth, sw=document.documentElement.scrollWidth;
  const bad=[]; document.querySelectorAll('.bay').forEach(bay=>{ const br=bay.getBoundingClientRect();
    bay.querySelectorAll('.spine').forEach(s=>{ const r=s.getBoundingClientRect(); if(r.right>br.right+1||r.left<br.left-1) bad.push(s.textContent.trim()); }); });
  const clipped=[...document.querySelectorAll('.spine .st')].filter(t=>t.scrollHeight>t.clientHeight+2||t.scrollWidth>t.clientWidth+2).map(t=>t.textContent);
  return {W, sw, outside:bad, clipped, spines:document.querySelectorAll('.spine').length};
}"""
JS_PAGES = """() => [...document.querySelectorAll('#book:not(.single) .leaf:not([aria-hidden=true]) .pg, #book:not(.single) .base-left .pg')].filter(e=>e.scrollHeight>e.clientHeight+2).map(e=>(e.querySelector('h1,h2')||{}).textContent)"""
with sync_playwright() as p:
    b=p.chromium.launch()
    # 1. layouts at many sizes
    for (w,h) in [(1440,900),(1280,720),(1024,768),(820,1180),(390,844),(360,740),(844,390)]:
        ctx,pg,errs=page(b,w,h); pg.goto(URL); pg.wait_for_timeout(600)
        L=pg.evaluate(JS_LAYOUT)
        check(f"[{w}x{h}] no sideways scroll", L['sw']<=L['W'], L)
        check(f"[{w}x{h}] all 15 spines fit their shelf", L['spines']==15 and not L['outside'], L['outside'])
        check(f"[{w}x{h}] spine titles not clipped", not L['clipped'], L['clipped'])
        if w in (1440,390): pg.screenshot(path=f"{SP}/shelf-{w}.png", full_page=True)
        # open every chapter of every book, check overflow on desktop spreads
        over=[]
        for i in range(15):
            pg.locator('.spine').nth(i).click(); pg.wait_for_timeout(700)
            over+=pg.evaluate(JS_PAGES)
            pg.keyboard.press('Escape'); pg.wait_for_timeout(800)
        check(f"[{w}x{h}] no clipped text on any open spread", not over, over)
        check(f"[{w}x{h}] no script errors", not errs, errs[:3]); ctx.close()

    # 2. reader basics, keyboard, focus return, rapid input
    ctx,pg,errs=page(b,1440,900); pg.goto(URL); pg.wait_for_timeout(400)
    pg.locator('.spine').nth(4).click(); pg.wait_for_timeout(800)
    check("spine 05 opens At Work at Ramp-down Radar", "Ramp-down Radar" in pg.inner_text('#book .leaf[aria-hidden=false]'.replace('[aria-hidden=false]','')) and 'pages' in pg.inner_text('#pageNo'), pg.inner_text('#pageNo'))
    pg.screenshot(path=f"{SP}/open-1440.png")
    for _ in range(25): pg.keyboard.press('ArrowRight')
    pg.wait_for_timeout(900)
    st=pg.evaluate("()=>({no:document.querySelector('#pageNo').textContent, next:document.querySelector('#nextBtn').disabled})")
    check("25 fast ArrowRight presses stop at the last page", st['next'], st)
    pg.keyboard.press('Escape'); pg.wait_for_timeout(800)
    check("Esc closes and focus goes back to a spine", pg.evaluate("()=>document.getElementById('reader').hidden && document.activeElement.classList.contains('spine')"))
    # rapid clicks on three spines
    pg.locator('.spine').nth(0).click(); pg.locator('.spine').nth(7).click(no_wait_after=True, force=True) if False else None
    pg.evaluate("()=>{const s=document.querySelectorAll('.spine'); s[1].click(); s[8].click(); s[12].click();}")
    pg.wait_for_timeout(1500)
    check("rapid clicks open only one book", pg.evaluate("()=>document.querySelectorAll('#reader:not([hidden])').length===1 && document.querySelectorAll('.flyer').length===0"))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(800)
    # wheel burst = one gesture with momentum
    pg.locator('.spine').nth(0).click(); pg.wait_for_timeout(800)
    before=pg.inner_text('#pageNo')
    pg.mouse.move(700,450)
    pg.evaluate("()=>new Promise(res=>{ let i=0; const el=document.getElementById('reader'); const t=setInterval(()=>{ el.dispatchEvent(new WheelEvent('wheel',{deltaY: Math.max(2, 60-i*2), bubbles:true, cancelable:true})); if(++i>=40){ clearInterval(t); res(); } },16); })")
    pg.wait_for_timeout(1000); after=pg.inner_text('#pageNo')
    check("one trackpad swipe turns exactly one spread", before!=after and pg.evaluate("()=>document.querySelectorAll('#book .leaf.flipped').length")==2, (before,after))
    check("no script errors (reader)", not errs, errs[:3]); ctx.close()

    # 3. highlight, persist, survive reload; stale marks ignored
    ctx,pg,errs=page(b,1440,900); pg.goto(URL+'#work-p2'); pg.wait_for_timeout(900)
    pg.click('[data-tool=hl]')
    pg.evaluate("""()=>{ const p=document.querySelector('.leaf[aria-hidden=false] .front .cols p'); const t=p.firstChild; const r=document.createRange(); r.setStart(t,2); r.setEnd(t,20); const s=getSelection(); s.removeAllRanges(); s.addRange(r); }""")
    pg.dispatch_event('#book','mouseup'); pg.evaluate("()=>document.dispatchEvent(new MouseEvent('mouseup'))"); pg.wait_for_timeout(200)
    n1=pg.evaluate("()=>document.querySelectorAll('#book .mark.hl').length")
    check("highlighter marks selected text", n1>=1, n1)
    pg.reload(); pg.wait_for_timeout(900)
    n2=pg.evaluate("()=>document.querySelectorAll('#book .mark.hl').length")
    check("marks survive a reload", n2>=1, n2)
    # simulate a content change: write a mark under an outdated key
    pg.evaluate("""()=>{ const f=document.querySelector('.face[data-key^="work:2:"]'); const k=f.dataset.key.split(':'); localStorage.setItem('prbooks.v2.mark.work:2:oldhash','<article class=pg>OLD TEXT</article>'); }""")
    pg.reload(); pg.wait_for_timeout(900)
    check("marks saved against old page text are ignored", 'OLD TEXT' not in pg.content())
    pg.click('[data-tool=hl]')
    # cross-page selection gives a message, not silence
    pg.evaluate("""()=>{ const a=document.querySelector('.leaf.flipped[aria-hidden=false] .back .cols p'); const z=document.querySelector('.leaf[aria-hidden=false]:not(.flipped) .front .cols p'); if(!a||!z) return; const r=document.createRange(); r.setStart(a.firstChild,1); r.setEnd(z.firstChild,Math.min(5,z.firstChild.length)); const s=getSelection(); s.removeAllRanges(); s.addRange(r); document.dispatchEvent(new MouseEvent('mouseup')); }""")
    pg.wait_for_timeout(200)
    check("a selection across two pages explains itself", "one page" in pg.inner_text('#tip'), pg.inner_text('#tip'))
    check("no script errors (marks)", not errs, errs[:3]); ctx.close()

    # 4. phone: rotate keeps the page; deep link
    ctx,pg,errs=page(b,390,844, has_touch=True, is_mobile=True); pg.goto(URL+'#home-p4'); pg.wait_for_timeout(1000)
    check("deep link #home-p4 opens At Home on page 4", "page 4 of" in pg.inner_text('#pageNo'), pg.inner_text('#pageNo'))
    pg.screenshot(path=f"{SP}/open-390.png")
    pg.set_viewport_size({'width':844,'height':390}); pg.wait_for_timeout(700)
    no=pg.inner_text('#pageNo')
    check("rotating the phone keeps page 4 in view", ("4" in no.split('of')[0]), no)
    check("no script errors (phone)", not errs, errs[:3]); ctx.close()

    # 5. storage blocked (private mode)
    ctx=b.new_context(viewport={'width':1280,'height':800}); ctx.add_init_script("Object.defineProperty(window,'localStorage',{get(){throw new Error('blocked')}})")
    pg=ctx.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(URL); pg.wait_for_timeout(400); pg.locator('.spine').nth(2).click(); pg.wait_for_timeout(800); pg.click('#nextBtn'); pg.wait_for_timeout(500)
    check("works with browser storage blocked", not errs and not pg.evaluate("()=>document.getElementById('reader').hidden"), errs[:2]); ctx.close()

    # 6. JavaScript off
    ctx=b.new_context(java_script_enabled=False, viewport={'width':1280,'height':800}); pg=ctx.new_page(); pg.goto(URL)
    txt=pg.inner_text('body')
    check("content readable with JavaScript off", "Ramp-down Radar" in txt and "Résumé" in txt); ctx.close()

    # 7. reduced motion
    ctx,pg,errs=page(b,1280,800, reduced_motion='reduce'); pg.goto(URL); pg.wait_for_timeout(400)
    pg.locator('.spine').nth(5).click(); pg.wait_for_timeout(300)
    check("reduced motion: book opens instantly", not pg.evaluate("()=>document.getElementById('reader').hidden") and not errs); ctx.close()

    # 8. Idli never leaves her rack, and petting works
    for (w,h) in [(1440,900),(390,844)]:
        ctx,pg,errs=page(b,w,h); pg.goto(URL)
        pg.evaluate("()=>{}"); out=[]
        pg.wait_for_timeout(200); pg.click('#idli'); pg.wait_for_timeout(500)
        hearts=pg.evaluate("()=>document.querySelectorAll('#rack .heart').length")
        for i in range(40):
            pg.wait_for_timeout(250)
            r=pg.evaluate("()=>{const a=document.getElementById('rack').getBoundingClientRect(), d=document.getElementById('idli').getBoundingClientRect(); return [d.left-a.left, a.right-d.right]}")
            if r[0]<12 or r[1]<12: out.append(r)
        check(f"[{w}] Idli stays inside the rack walls for 10 s", not out, out[:3])
        check(f"[{w}] tapping Idli makes hearts", hearts>0, hearts)
        if w==1440: pg.screenshot(path=f"{SP}/rack.png", clip={'x':600,'y':0,'width':840,'height':260})
        ctx.close()
    b.close()
fails=[r for r in results if not r[1]]
print(f"\n{len(results)-len(fails)} passed, {len(fails)} failed")
json.dump(results, open(SP+'/edge_results.json','w'))
