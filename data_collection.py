"""
Pharmaceutical Data Collector
- Branded: uses Playwright to visit 1mg product pages and extract visible product fields.
- Generic: uses Playwright to open PMBI's live Product/MRP list and trigger its CSV export.
- No Kaggle/pre-made dataset is used.
Run: python scripts/data_collection.py
"""
from pathlib import Path
import re, time, pandas as pd
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
EVIDENCE = ROOT / "evidence_screenshots"
DATA.mkdir(exist_ok=True); EVIDENCE.mkdir(exist_ok=True)

BRANDED_URLS = [
    "https://www.1mg.com/drugs/Metform-Tablet-564579",
    "https://www.1mg.com/drugs/500-mg-17942",
    "https://www.1mg.com/drugs/Atorvast-Tablet-906912",
    "https://www.1mg.com/drugs/Atorastin-Tablet-678105",
    "https://www.1mg.com/drugs/pantop-40mg-tablet-26028",
    "https://www.1mg.com/drugs/Paracet-Tablet-458722",
    "https://www.1mg.com/drugs/aztra-500mg-tablet-711314",
    "https://www.1mg.com/drugs/azim-500mg-tablet-570565",
    "https://www.1mg.com/drugs/aziyan-500mg-tablet-405375",
]

def text_after(body, label):
    m = re.search(label + r"\s*([^\n]+)", body, flags=re.I)
    return m.group(1).strip() if m else ""

def collect_branded(page):
    rows=[]
    for url in BRANDED_URLS:
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(2500)
        body = page.locator("body").inner_text()
        title = page.locator("h1").first.inner_text() if page.locator("h1").count() else ""
        # Visible page text patterns are intentionally used instead of hidden APIs.
        comp = ""
        m = re.search(r"(?:Contains|Composition)\s+(.+?)(?:Marketer|Storage|Product information)", body, re.S|re.I)
        if m: comp = re.sub(r"\s+", " ", m.group(1)).strip()
        marketer = ""
        m = re.search(r"Marketer\s+(.+?)(?:\n|Storage)", body, re.I)
        if m: marketer = m.group(1).strip()
        mrp = ""
        m = re.search(r"MRP\s*₹\s*([0-9,.]+)", body, re.I)
        if m: mrp = float(m.group(1).replace(",",""))
        side = ""
        m = re.search(r"Common side effects.*?\n((?:\s*\*\s*.*\n?)+)", body, re.I|re.S)
        if m: side = "; ".join(re.findall(r"\*\s*(.+)", m.group(1)))
        rows.append({
            "branded_name": title.strip(),
            "active_salt_composition": comp,
            "manufacturer": marketer,
            "packaging": "",
            "mrp_inr": mrp,
            "side_effects": side,
            "source_url": url,
            "source_date": time.strftime("%Y-%m-%d"),
            "source": "1mg"
        })
        page.screenshot(path=str(EVIDENCE / ("branded_" + re.sub(r"[^A-Za-z0-9]+","_",title)[:60] + ".png")), full_page=True)
    return pd.DataFrame(rows)

def collect_generic(page):
    url="https://janaushadhi.gov.in/product-portfolio/product-view-list"
    page.goto(url, wait_until="networkidle", timeout=90000)
    page.screenshot(path=str(EVIDENCE/"pmbi_product_list_before_export.png"), full_page=True)
    # The live site exposes a Download CSV control after JS loads.
    # We intentionally locate it by accessible text instead of hard-coding a private API.
    with page.expect_download(timeout=60000) as dlinfo:
        page.get_by_text(re.compile("Download CSV", re.I)).click()
    dl=dlinfo.value
    out=DATA/"generic_medicines_live.csv"
    dl.save_as(out)
    return out

def main():
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=False)
        page=browser.new_page(viewport={"width":1440,"height":1000})
        branded=collect_branded(page)
        branded.to_csv(DATA/"branded_medicines_live.csv", index=False)
        try:
            generic=collect_generic(page)
            print("Generic live export:", generic)
        except Exception as e:
            print("PMBI CSV export failed. Keep the screenshot and inspect the current download control manually:", e)
        browser.close()
    print("Branded rows:", len(branded))
    print("Files:", list(DATA.glob("*.csv")))

if __name__=="__main__":
    main()
