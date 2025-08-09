# pip install playwright bs4 pandas
# playwright install
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time, random, csv

START_URL = "https://www.madlan.co.il/for-sale/שכונה-רמת-החייל-תל-אביב-יפו-ישראל?filters=_0-11500000____villa%2Ccottage%2CdualCottage%2Cland______0-100000_______search-filter-top-bar&marketplace=residential"

def human_pause(a=0.8,b=1.8):
    time.sleep(random.uniform(a,b))

def extract_card_info(card):
    # Flexible selectors; Madlan changes classnames often
    def sel(one):
        return card.select_one(one)
    price = (sel('[data-auto="property-price"]') or sel('[class*="price"]'))
    address = (sel('[data-auto="property-address"]') or sel('h2, h3'))
    rooms = (sel('[data-auto="property-rooms"]') or sel('[class*="room"]'))
    floor = (sel('[data-auto="property-floor"]') or sel('[class*="floor"]'))
    area  = (sel('[data-auto="property-size"]') or sel('[class*="size"]') or sel('[class*="area"]'))
    link = (card.select_one('[data-auto="listed-bulletin-clickable"]') or card.select_one('a[href]'))
    href = link['href'] if link and link.has_attr('href') else None
    if href and href.startswith('/'):
        href = "https://www.madlan.co.il" + href
    return {
        "price": price.get_text(strip=True) if price else "",
        "address": address.get_text(strip=True) if address else "",
        "rooms": rooms.get_text(strip=True) if rooms else "",
        "floor": floor.get_text(strip=True) if floor else "",
        "area_sqm": area.get_text(strip=True) if area else "",
        "url": href or ""
    }

def extract_listing_details(html):
    soup = BeautifulSoup(html, "html.parser")
    # description
    desc = (soup.select_one('[data-testid="description"], .description, [class*="description"]') or soup.select_one('p'))
    description = desc.get_text(strip=True) if desc else ""
    # features
    feats = []
    for li in soup.select('[data-testid="feature"], .feature, [class*="feature"], ul li'):
        t = li.get_text(strip=True)
        if t and len(t) < 80: feats.append(t)
    # key/value details (dt/dd pairs or generic label/value)
    details = {}
    labels = soup.select('dt, [class*="label"], [class*="key"]')
    vals   = soup.select('dd, [class*="value"]')
    for lab, val in zip(labels, vals):
        k = lab.get_text(strip=True); v = val.get_text(strip=True)
        if k and v: details[k] = v
    return description, feats, details

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(
        locale="he-IL",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
    page = ctx.new_page()
    page.goto(START_URL, wait_until="domcontentloaded", timeout=90000)

    # scroll to load more results (tweak loops if you need more)
    for _ in range(8):
        page.mouse.wheel(0, 4000)
        human_pause(1.0, 2.0)

    html = page.content()
    soup = BeautifulSoup(html, "html.parser")

    # try multiple selectors for cards
    cards = (soup.select('[data-auto="listed-bulletin"]') or
             soup.select('[data-testid="listing-card"]') or
             soup.select('[class*="listed-bulletin"]') or
             soup.select('article'))

    out = []
    for c in cards:
        base = extract_card_info(c)
        if not base["url"]:
            continue
        # open listing page for details
        human_pause(1.2, 2.2)
        page.goto(base["url"], wait_until="domcontentloaded", timeout=90000)
        # let dynamic sections settle
        human_pause(0.8, 1.4)
        d_html = page.content()
        description, features, details = extract_listing_details(d_html)
        base.update({
            "description": description,
            "features": "; ".join(sorted(set(features))),
        })
        # flatten a few common details if present
        for k in ["מחיר", "שכונה", "כתובת", "מ\"ר בנוי", "חניות", "מחסן", "מרפסת"]:
            if k in details and k not in base:
                base[k] = details[k]
        out.append(base)

    # save CSV
    import csv
    if out:
        cols = sorted({k for row in out for k in row.keys()})
        with open("madlan_listings.csv", "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader(); w.writerows(out)
    browser.close()
print("Done.")
