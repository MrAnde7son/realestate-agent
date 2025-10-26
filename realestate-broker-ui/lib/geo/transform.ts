// lib/geo/transform.ts
// No deps. Handles ITM (EPSG:2039), WebMercator (EPSG:3857), and WGS84.
// Returns { lon, lat, source } so you can see which path was used.

// --- WebMercator (EPSG:3857) -> WGS84 ---
function fromEPSG3857to4326(x: number, y: number) {
  const R = 6378137;
  const lon = (x / R) * (180 / Math.PI);
  const lat = (2 * Math.atan(Math.exp(y / R)) - Math.PI / 2) * (180 / Math.PI);
  return { lon, lat };
}

// --- ITM (EPSG:2039) -> WGS84 ---
function itm2039ToWgs84_(x: number, y: number) {
  // GRS80 ellipsoid
  const a = 6378137.0;
  const f = 1 / 298.257222101;
  const b = a * (1 - f);
  const e2 = 1 - (b * b) / (a * a);

  const lon0 = 35.20451694444445 * (Math.PI / 180);
  const k0 = 1.0000067;
  const falseE = 219529.584;
  const falseN = 626907.39;

  const dx = x - falseE;
  const dy = y - falseN;

  const n = (a - b) / (a + b);
  const A0 = 1 + (n ** 2) / 4 + (n ** 4) / 64;
  const A2 = (3 / 2) * (n - (n ** 3) / 8);
  const A4 = (15 / 16) * (n ** 2 - (n ** 4) / 4);
  const A6 = (35 / 48) * (n ** 3);
  const A8 = (315 / 512) * (n ** 4);

  const M = dy / k0;
  const sigma = (M / (a * (1 - e2 / 4 - (3 * e2 ** 2) / 64 - (5 * e2 ** 3) / 256)));

  const fp =
    sigma +
    A2 * Math.sin(2 * sigma) +
    A4 * Math.sin(4 * sigma) +
    A6 * Math.sin(6 * sigma) +
    A8 * Math.sin(8 * sigma);

  const sinfp = Math.sin(fp);
  const cosfp = Math.cos(fp);
  const tanfp = Math.tan(fp);

  const N1 = a / Math.sqrt(1 - e2 * sinfp * sinfp);
  const R1 = (a * (1 - e2)) / Math.pow(1 - e2 * sinfp * sinfp, 1.5);
  const D = dx / (N1 * k0);

  const lat =
    fp -
    ((N1 * tanfp) / R1) *
      ( (D ** 2) / 2 -
        ( (5 + 3 * tanfp * tanfp + 10 * (e2 / (1 - e2)) - 4 * ((e2 / (1 - e2)) ** 2) - 9 * e2) * (D ** 4) ) / 24 +
        ( (61 + 90 * tanfp * tanfp + 45 * (tanfp ** 4)) * (D ** 6) ) / 720 );

  const lon =
    lon0 +
    ( D -
      ((1 + 2 * tanfp * tanfp + (e2 / (1 - e2))) * (D ** 3)) / 6 +
      ((5 + 28 * tanfp * tanfp + 24 * (tanfp ** 4)) * (D ** 5)) / 120
    ) / cosfp;

  return { lon: (lon * 180) / Math.PI, lat: (lat * 180) / Math.PI };
}

export function normalizeToLonLat(p: any): { lon: number; lat: number; source: 'wgs84' | 'wgs84_swapped' | '3857' | 'itm2039' } | null {
  const num = (v: any) => (v == null || v === '' ? NaN : Number(v));

  // Try all likely field names we’ve seen
  const lonRaw = p.lon ?? p.longitude ?? p.lon_wgs84 ?? p.lng ?? p.x_wgs84;
  const latRaw = p.lat ?? p.latitude ?? p.lat_wgs84 ?? p.latitute ?? p.y_wgs84;

  // govmap blobs often come as { coordinates: { x,y } } but can also have lon_wgs84/lat_wgs84
  const gov = p.govmap_data?.coordinates ?? p.govmap_data ?? {};
  const govLon = gov.lon_wgs84 ?? gov.longitude ?? gov.lng ?? gov.lon;
  const govLat = gov.lat_wgs84 ?? gov.latitude ?? gov.lat;

  // ITM (meters) candidates
  const itmX = p.x ?? p.itm_x ?? p.X ?? p.itm?.x ?? p.gisCoordinates?.x ?? gov.x_itm ?? gov.x2039 ?? gov.xitm ?? gov.x;
  const itmY = p.y ?? p.itm_y ?? p.Y ?? p.itm?.y ?? p.gisCoordinates?.y ?? gov.y_itm ?? gov.y2039 ?? gov.yitm ?? gov.y;

  // WebMercator candidates (meters)
  const wmX = p.x_itm ?? p.web_mercator_x ?? gov.web_mercator_x ?? gov.x_3857 ?? gov.merc_x;
  const wmY = p.y_itm ?? p.web_mercator_y ?? gov.web_mercator_y ?? gov.y_3857 ?? gov.merc_y;

  const lon = num(lonRaw ?? govLon);
  const lat = num(latRaw ?? govLat);
  const x = num(itmX);
  const y = num(itmY);
  const xm = num(wmX);
  const ym = num(wmY);

  // A) Already WGS84 in Israel
  if (Number.isFinite(lon) && Number.isFinite(lat) && lat >= 29 && lat <= 34.8 && lon >= 33 && lon <= 36.5) {
    return { lon, lat, source: 'wgs84' };
  }
  // A2) Very common: swapped lon/lat
  if (Number.isFinite(lon) && Number.isFinite(lat) && lon >= 29 && lon <= 34.8 && lat >= 33 && lat <= 36.5) {
    return { lon: lat, lat: lon, source: 'wgs84_swapped' };
  }

  // B) WebMercator (EPSG:3857) — magnitudes in millions
  if (Number.isFinite(xm) && Number.isFinite(ym) && Math.abs(xm) > 1_000_000 && Math.abs(ym) > 1_000_000) {
    const pt = fromEPSG3857to4326(xm, ym);
    return { ...pt, source: '3857' };
  }

  // C) ITM (EPSG:2039): x≈120k–300k, y≈600k–900k
  if (Number.isFinite(x) && Number.isFinite(y) && x > 100_000 && x < 400_000 && y > 500_000 && y < 1_000_000) {
    const pt = itm2039ToWgs84_(x, y);
    return { ...pt, source: 'itm2039' };
  }

  return null;
}
