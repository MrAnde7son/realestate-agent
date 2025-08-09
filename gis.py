import os, json, re, requests
from urllib.parse import quote

BASE = "https://gisn.tel-aviv.gov.il/ArcGIS/rest/services/IView2/MapServer"
LAYER_ID = 433  # "רישיונות בביצוע" (אפשר לשנות ל-499 "אתרי בניה" וכו')

def layer_info(layer_id=LAYER_ID):
    url = f"{BASE}/{layer_id}?f=pjson"
    return requests.get(url).json()

def search_permits(query_text, layer_id=LAYER_ID, limit=200):
    # where מבוסס טקסט חופשי על שדה כתובת/תיאור (צריך להתאים לשמות השדות בפועל)
    # הטריק: נבנה where רחב על כמה שדות מוכרים אם קיימים
    info = layer_info(layer_id)
    fields = {f['name'] for f in info.get('fields', [])}
    candidates = [n for n in ['ADDRESS','Address','address','SITE_ADDRESS','FULL_ADDRESS','STREET','street','שם_רחוב','כתובת','DESCRIPTION','תיאור'] if n in fields]
    if not candidates:
        raise RuntimeError(f"לא נמצא שדה כתובת/תיאור בשכבה {layer_id}. שדות קיימים: {sorted(fields)}")
    like = quote(f"%{query_text}%")
    ors = [f"UPPER({c}) LIKE UPPER('{like}')" for c in candidates]
    where = " OR ".join(ors)

    params = {
        "where": where,
        "outFields": "*",
        "returnGeometry": "false",
        "f": "pjson",
        "resultRecordCount": limit
    }
    url = f"{BASE}/{layer_id}/query"
    r = requests.get(url, params=params)
    r.raise_for_status()
    data = r.json()
    return data.get("features", [])

def download_attachments(object_id, layer_id=LAYER_ID, out_dir="attachments"):
    os.makedirs(out_dir, exist_ok=True)
    url = f"{BASE}/{layer_id}/{object_id}/attachments?f=pjson"
    meta = requests.get(url).json()
    for att in meta.get("attachmentInfos", []):
        att_id = att["id"]
        name = re.sub(r"[^\w\-.א-ת ]", "_", att.get("name","file"))
        file_url = f"{BASE}/{layer_id}/{object_id}/attachments/{att_id}"
        data = requests.get(file_url).content
        path = os.path.join(out_dir, f"{object_id}_{name}")
        with open(path, "wb") as f:
            f.write(data)
        print("saved:", path)

# --- שימוש:
# דוגמה: חיפוש “רמת החייל” או רחוב ספציפי (“הל"ה”)
features = search_permits("רמת החייל")
for f in features[:5]:
    attrs = f["attributes"]
    oid = attrs.get("OBJECTID") or attrs.get("ObjectId") or attrs.get("OBJECTID_1")
    print({k: attrs.get(k) for k in list(attrs.keys())[:10]})  # הדפסה מהירה של כמה שדות ראשונים
    if oid:
        download_attachments(oid)
