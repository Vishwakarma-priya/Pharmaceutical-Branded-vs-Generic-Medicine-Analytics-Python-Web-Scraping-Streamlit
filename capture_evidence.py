"""
Run this after data_collection.py if you need a separate evidence pass.
It captures the PMBI live product page and selected 1mg pages as full-page PNGs.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"evidence_screenshots"; OUT.mkdir(exist_ok=True)
URLS=[
("PMBI_live","https://janaushadhi.gov.in/product-portfolio/product-view-list"),
("1mg_metform","https://www.1mg.com/drugs/Metform-Tablet-564579"),
("1mg_atorvast","https://www.1mg.com/drugs/Atorvast-Tablet-906912"),
("1mg_pantop","https://www.1mg.com/drugs/pantop-40mg-tablet-26028"),
("1mg_paracet","https://www.1mg.com/drugs/Paracet-Tablet-458722"),
("1mg_aztra","https://www.1mg.com/drugs/aztra-500mg-tablet-711314"),
]
with sync_playwright() as p:
    browser=p.chromium.launch(headless=False)
    page=browser.new_page(viewport={"width":1440,"height":1000})
    for name,url in URLS:
        page.goto(url,wait_until="domcontentloaded",timeout=60000)
        page.wait_for_timeout(3000)
        page.screenshot(path=str(OUT+f"/{name}.png"),full_page=True)
    browser.close()
print("Evidence screenshots saved to",OUT)
