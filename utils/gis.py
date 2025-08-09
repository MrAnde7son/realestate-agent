# -*- coding: utf-8 -*-
import json, os, re, requests

BASE = "https://gisn.tel-aviv.gov.il/ArcGIS/rest/services/IView2/MapServer"
LAYER_NEIGH = 511   # שכונות
LAYER_PERMITS = 772 # בקשות והיתרי בניה

HDRS = {"User-Agent":"Mozilla/5.0","Accept":"application/json, text/plain, */*"}

def safe_json(resp):
    ctype = (resp.headers.get("Content-Type") or "").lower()
    if "json" in ctype:
        try: return resp.json()
        except Exception: pass
    return {"_error":"non_json","status":resp.status_code,"snippet":resp.text[:400]}

def get_neighborhood_polygon(name_he):
    """שולף גאומטריה לשכונה בשם מדויק; אם לא מוצא, מחזיר None"""
    url = f"{BASE}/{LAYER_NEIGH}/query"
    params = {
        "f":"pjson",
        "where": f"shem_shchuna = '{name_he}'",
        "outFields":"shem_shchuna",
        "returnGeometry":"true",
        "outSR":4326,
        "resultRecordCount": 1
    }
    res = safe_json(requests.get(url, params=params, headers=HDRS, timeout=30))
    feats = res.get("features") if isinstance(res, dict) else None
    if feats:
        return feats[0]["geometry"]
    return None

def search_permits_by_address(text, limit=2000):
    """חיפוש לפי כתובת חופשית בשדה addresses (יכול להחזיר גם תוצאות מחוץ לשכונה)"""
    url = f"{BASE}/{LAYER_PERMITS}/query"
    params = {
        "f":"pjson",
        "where": f"addresses LIKE '%{text}%'",
        "outFields":"request_num,permission_num,building_stage,url_hadmaya,addresses,permission_date",
        "returnGeometry":"false",
        "resultRecordCount": limit
    }
    return safe_json(requests.get(url, params=params, headers=HDRS, timeout=30))

def search_permits_in_polygon(geom, limit=2000):
    """חיפוש מרחבי: מוצא היתרים בתוך פוליגון נתון"""
    url = f"{BASE}/{LAYER_PERMITS}/query"
    params = {
        "f":"pjson",
        "where":"1=1",
        "geometry": json.dumps(geom, ensure_ascii=False),
        "geometryType":"esriGeometryPolygon",
        "inSR":4326,
        "spatialRel":"esriSpatialRelIntersects",
        "outFields":"request_num,permission_num,building_stage,url_hadmaya,addresses,permission_date",
        "returnGeometry":"false",
        "resultRecordCount": limit
    }
    return safe_json(requests.get(url, params=params, headers=HDRS, timeout=30))

def download_permit_docs(features, out_dir="permits_docs"):
    """מוריד את המסמכים מתוך url_hadmaya ושומר בתיקייה"""
    os.makedirs(out_dir, exist_ok=True)
    saved = []
    for f in features:
        a = f.get("attributes", {})
        url = (a.get("url_hadmaya") or "").strip()
        if not url:
            continue
        if url.startswith("/"):
            url = "https://gisn.tel-aviv.gov.il" + url
        try:
            r = requests.get(url, headers=HDRS, timeout=30)
            if r.status_code == 200 and r.content:
                ext = ".pdf" if "pdf" in (r.headers.get("Content-Type","").lower()) else ".bin"
                safe_stage = re.sub(r'[^\w\-.א-ת ]', '_', a.get('building_stage', '') or '')
                ident = a.get('permission_num') or a.get('request_num') or 'permit'
                base = f"{ident}_{safe_stage}"
                path = os.path.join(out_dir, base + ext)
                with open(path,"wb") as fh:
                    fh.write(r.content)
                saved.append(path)
        except Exception:
            continue
    return saved

if __name__ == "__main__":
    area = "רמת החייל"
    # 1) נסה למצוא היתרים לפי כתובת חופשית – יכול להחזיר 0 תוצאות
    res = search_permits_by_address(area)
    features = res.get("features", []) if "_error" not in res else []
    if not features:
        # 2) אם אין תוצאות, נביא את הפוליגון של השכונה ונהריץ שאילתת מרחב
        poly = get_neighborhood_polygon(area)
        if poly:
            res = search_permits_in_polygon(poly)
            features = res.get("features", []) if "_error" not in res else []
        else:
            print({"_error":"neighborhood_not_found", "layer": LAYER_NEIGH, "name": area})
            exit(0)
    print(f"נמצאו {len(features)} היתרים בשכונה '{area}'")
    # 3) הורדת הקבצים
    files = download_permit_docs(features)
    print(f"הורדו {len(files)} קבצים ל־{os.path.abspath('permits_docs')}")
