import requests
import datetime
import pandas as pd

# חיפוש הדאטה-סט הרלוונטי (כדי לא לקבע resource_id)
pkg = requests.get("https://data.gov.il/api/3/action/package_search",
                   params={"q": "עסקאות נדל"}).json()

# מאתרים ריסורס עם פורמט CSV או שהועלה ל-DataStore (has views)
resources = []
for res in pkg["result"]["results"][0]["resources"]:
    if (res.get("datastore_active") or (res.get("format") or "").lower() == "csv"):
        resources.append(res)

# אם יש ריסורס שמחובר ל-DataStore נעדיף אותו (תמיכה ב-query)
res = next((r for r in resources if r.get("datastore_active")), resources[0])
resource_id = res["id"]

# טווח תאריכים לשנה אחורה
today = datetime.date.today()
start = (today.replace(year=today.year-1)).isoformat()

# שאילתה: עיר="תל אביב - יפו", סוג נכס דירה, תאריך עסקה מהשנה האחרונה
q = {
    "resource_id": resource_id,
    "limit": 1000,
    "filters": {
        "city_name": "תל אביב - יפו",
        "asset_type": "דירה"
    },
    "q": "",  # אפשר להשאיר ריק
}

data = requests.get("https://data.gov.il/api/3/action/datastore_search",
                    params=q).json()

records = data["result"]["records"]

# מיון/סינון נוסף בפנדס
df = pd.DataFrame(records)
cols = ["deal_date", "price", "street_name", "house_number", "neighborhood", "asset_rooms", "asset_area"]
df = df[cols].sort_values("deal_date", ascending=False)

print(df.head(20))
