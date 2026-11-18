"""Repeatable post-deploy checks using Orca's embedded browser.

Usage: python docs/qa/browser_audit.py --base-url URL --output report.json
Requires an active Orca desktop. Only changes this test tab's local storage.
Network failures and latency are simulated in this tab for recovery checks.
"""
import argparse
import atexit
import base64
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen


def cli(*args):
    result = subprocess.run(["orca", *args, "--json"], capture_output=True,
                            text=True, encoding="utf-8", timeout=55)
    data = json.loads(result.stdout)
    if not data.get("ok"):
        raise RuntimeError(data.get("error"))
    return data["result"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    page = cli("tab", "create", "--url", base + "/wizard")["browserPageId"]
    results = []

    def ev(code):
        encoded = base64.b64encode(code.encode()).decode()
        raw = cli("eval", "--page", page, "--expression", f"eval(atob('{encoded}'))")["result"]
        return json.loads(raw) if isinstance(raw, str) else raw

    helpers = """
      const pause=ms=>new Promise(r=>setTimeout(r,ms));
      const buttons=()=>[...document.querySelectorAll('button')];
      const click=text=>{const b=buttons().find(b=>b.textContent.trim()===text); if(!b) throw Error('Missing button '+text); b.click();};
      const main=()=>document.querySelector('main');
    """

    def run(code):
        return ev("(async()=>{" + helpers + code + "})()")

    original_dock = ev("JSON.stringify(localStorage.getItem('comparebuy_dock'))")

    def restore_dock():
        if original_dock is None:
            ev("localStorage.removeItem('comparebuy_dock'); JSON.stringify(true)")
        else:
            ev("localStorage.setItem('comparebuy_dock'," + json.dumps(original_dock) + "); JSON.stringify(true)")

    atexit.register(restore_dock)

    def go(path):
        # Full navigation resets request interception and React state.
        cli("goto", "--page", page, "--url", base + path)
        for _ in range(30):
            if ev("JSON.stringify(!!document.querySelector('main') || document.body.innerText.includes('Reload to try again'))"):
                break
            time.sleep(0.2)
        time.sleep(0.5)

    def record(key, evidence, passed):
        results.append(dict(key=key, passed=passed, evidence=evidence))
        print(key, "PASS" if passed else "FAIL", json.dumps(evidence, ensure_ascii=True), flush=True)

    go("/wizard")
    data = run("""
      const cards=[...main().querySelectorAll('h3')].map(h=>{
        const e=h.closest('button')||h.closest('.cursor-pointer');
        return {name:h.textContent,tag:e?.tagName,tabIndex:e?.tabIndex,pressed:e?.getAttribute('aria-pressed')};
      }); return JSON.stringify(cards);
    """)
    record("category-keyboard", data, len(data) == 5 and all(c['tag'] == 'BUTTON' and c['tabIndex'] == 0 for c in data))
    cli("viewport", "--page", page, "--width", "390", "--height", "844", "--mobile")
    data = run("""
      const toggle=buttons().find(b=>b.getAttribute('aria-label')==='Toggle Menu');
      const before=toggle.getAttribute('aria-expanded'); toggle.click(); await pause(100);
      const after=toggle.getAttribute('aria-expanded');
      const controls=toggle.getAttribute('aria-controls');
      const exists=!!document.getElementById(controls); toggle.click(); await pause(100);
      return JSON.stringify({before,after,controls,exists});
    """)
    record("menu-expanded", data, data['before'] == 'false' and data['after'] == 'true' and data['exists'])
    cli("viewport", "--page", page, "--width", "1280", "--height", "900")
    data = run("""
      const heading=[...main().querySelectorAll('h3')].find(h=>h.textContent==='TWS / Audio');
      (heading.closest('button')||heading.closest('.cursor-pointer')).click(); await pause(100);
      click('Lanjutkan'); await pause(100);
      const presets=buttons().filter(b=>/Entry ANC|Mid-Range Harian/.test(b.textContent)).map(b=>b.innerText);
      buttons().find(b=>b.textContent.includes('Entry ANC')).click(); await pause(100);
      const sliders=[...main().querySelectorAll('input[type=range]')].map(e=>({name:e.getAttribute('aria-label'),value:e.value,step:e.step}));
      return JSON.stringify({presets,sliders,text:main().innerText});
    """)
    record("budget-labels", data['presets'], '300.000' in data['presets'][0] and '1.000.000' in data['presets'][0] and '2.500.000' in data['presets'][1])
    record("budget-slider-step", data['sliders'], float(data['sliders'][0]['value']) == 300000 and 300000 % float(data['sliders'][0]['step']) == 0)
    data = run("""
      click('Lanjutkan'); await pause(100);
      const selected=buttons().filter(b=>b.getAttribute('aria-pressed')==='true').map(b=>b.innerText);
      click('Lanjutkan'); await pause(100);
      const blocked=main().innerText.includes('Bagaimana Skenario');
      const message=main().querySelector('[role=alert]')?.textContent;
      if(!blocked){click('Kembali');await pause(100);}
      buttons().find(b=>b.textContent.includes('Olahraga & Gym')).click();await pause(100);
      click('Lanjutkan');await pause(100);
      const sliders=[...main().querySelectorAll('input[type=range]')].map(e=>({name:e.getAttribute('aria-label'),labels:[...(e.labels||[])].map(l=>l.textContent)}));
      return JSON.stringify({selected,blocked,message,sliders});
    """)
    record("scenario-required", {k: data.get(k) for k in ['selected', 'blocked', 'message']}, data['blocked'] and bool(data.get('message')))
    record("priority-labels", data['sliders'], len(data['sliders']) == 6 and all(s['name'] or s['labels'] for s in data['sliders']))

    go("/catalog")
    data = run("""
      for(let i=0;i<100&&!main().querySelector('input[type=text]');i++)await pause(100);
      for(let i=0;i<100&&main().innerText.includes('Memuat');i++)await pause(100);
      const input=main().querySelector('input[type=text]');
      const set=value=>{Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(input,value);input.dispatchEvent(new Event('input',{bubbles:true}));};
      set('Samsung'); await pause(450);
      const plain=[...main().querySelectorAll('h3')].map(h=>h.textContent).filter(s=>s.includes('Samsung'));
      set(' Samsung '); await pause(450);
      const padded=[...main().querySelectorAll('h3')].map(h=>h.textContent).filter(s=>s.includes('Samsung'));
      return JSON.stringify({plain,padded});
    """)
    record("search-trim", data, len(data['plain']) > 0 and data['plain'] == data['padded'])

    # Seed real catalog records, not fabricated data, for the comparison checks.
    with urlopen('https://comparebuy-api.onrender.com/api/products?per_page=100', timeout=45) as response:
        products = json.load(response)['products']
    pair = [next(p for p in products if p['id'] == pid) for pid in ['sm-002', 'sm-001']]

    def seed_pair():
        ev("localStorage.setItem('comparebuy_dock',JSON.stringify(" + json.dumps(pair) + ")); JSON.stringify(true)")
        go("/catalog")

    seed_pair()
    data = run("""
      window.__realFetch=window.fetch;
      window.fetch=(url,opts)=>String(url).includes('/api/compare')?Promise.reject(new Error('QA simulated outage')):window.__realFetch(url,opts);
      [...document.querySelectorAll('a')].find(a=>a.getAttribute('href')==='/compare').click();
      for(let i=0;i<80&&!document.querySelector('thead h4');i++)await pause(100);
      return JSON.stringify({expected:JSON.parse(localStorage.getItem('comparebuy_dock')).map(p=>p.name),actual:[...document.querySelectorAll('thead h4')].map(e=>e.textContent)});
    """)
    record("comparison-fallback-order", data, data['actual'] == data['expected'])

    seed_pair()
    data = run("""
      window.__realFetch=window.fetch; window.__pendingCompare=null;
      const pair=JSON.parse(localStorage.getItem('comparebuy_dock'));
      window.fetch=(url,opts)=>String(url).includes('/api/compare')?new Promise(resolve=>{window.__pendingCompare=()=>resolve(new Response(JSON.stringify({products:pair,highlights:[],is_same_category:true})));}):window.__realFetch(url,opts);
      [...document.querySelectorAll('a')].find(a=>a.getAttribute('href')==='/compare').click();
      for(let i=0;i<80&&!window.__pendingCompare;i++)await pause(100);
      if(!window.__pendingCompare)throw Error('Comparison did not start');
      click('Kosongkan Matriks'); await pause(150); window.__pendingCompare(); await pause(350);
      return JSON.stringify({saved:JSON.parse(localStorage.getItem('comparebuy_dock')),columns:[...document.querySelectorAll('thead h4')].map(e=>e.textContent),empty:main().innerText.includes('Belum Ada Produk')});
    """)
    record("comparison-stale-response", data, data['saved'] == [] and data['columns'] == [] and data['empty'])

    # Valid JSON with a wrong shape must not crash the whole application.
    ev("localStorage.setItem('comparebuy_dock','{}'); JSON.stringify(true)")
    go("/catalog")
    data = run("await pause(600); return JSON.stringify({hasMain:!!main(),text:document.body.innerText.slice(0,400)});")
    record("dock-storage-validation", data, data['hasMain'] and 'Application error' not in data['text'])
    ev("localStorage.removeItem('comparebuy_dock'); JSON.stringify(true)")
    go("/catalog")
    report = dict(tested_at=datetime.now(timezone.utc).isoformat(), base_url=base,
                  browser="Orca embedded Chromium", page=page,
                  note="Outage/latency checks simulate fetch failures in this tab only.", results=results)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{sum(r['passed'] for r in results)}/{len(results)} passed; report: {output}", flush=True)


if __name__ == '__main__':
    main()
