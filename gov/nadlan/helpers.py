import time, uuid, json, jwt, requests

SECRET = "90c3e620192348f1bd46fcd9138c3c68"
ALG = "HS256"
DOMAIN = "www.nadlan.gov.il"
GF = 120  # seconds


def _rev(s: str) -> str:
    return s[::-1]


def make_sk(ttl=GF) -> str:
    return jwt.encode(
        {"domain": DOMAIN, "exp": int(time.time()) + ttl}, SECRET, algorithm=ALG
    )


def sign_outer(clear: dict, ttl=GF) -> dict:
    body = {**clear, "domain": DOMAIN, "exp": int(time.time()) + ttl}
    compact = jwt.encode(body, SECRET, algorithm=ALG, headers={"alg": ALG})
    return {"##": _rev(compact)}


def unwrap_any(resp_obj):
    if (
        isinstance(resp_obj, dict)
        and "__" in resp_obj
        and isinstance(resp_obj["__"], str)
    ):
        compact = _rev(resp_obj["__"])
        return jwt.decode(
            compact,
            SECRET,
            algorithms=[ALG],
            options={"verify_aud": False, "verify_iss": False},
        )
    if isinstance(resp_obj, dict) and "body" in resp_obj:
        try:
            inner = json.loads(resp_obj["body"])
            return unwrap_any(inner) or inner
        except Exception:
            return resp_obj
    return resp_obj


def post_deals_neighborhood(neigh_id: str, session=None, max_retries=3):
    s = session or requests.Session()
    url = "https://x4006fhmy5.execute-api.il-central-1.amazonaws.com/api/deal"

    def one_attempt():
        clear = {
            "base_id": neigh_id,
            "base_name": "neighborhoodId",
            "fetch_number": 1,
            "type_order": "dealDate_down",
            "sk": make_sk(),
            "token": str(uuid.uuid4()),
        }
        env = sign_outer(clear)
        r = s.post(
            url,
            headers={
                "accept": "*/*",
                "content-type": "text/plain",
                "origin": "https://www.nadlan.gov.il",
                "referer": "https://www.nadlan.gov.il/",
            },
            data=json.dumps(env),
            timeout=30,
        )
        # attempt to parse various wrapper shapes
        try:
            j = r.json()
        except Exception:
            j = {"body": r.text}
        return r.status_code, j

    backoff = 0.75
    for attempt in range(max_retries):
        status, j = one_attempt()
        if status == 200 and j.get("statusCode") == 200:
            return unwrap_any(j)
        if status == 405 or j.get("statusCode") == 405:
            time.sleep(backoff)
            backoff *= 1.6
            continue
        # 400 base_name invalid => key typo; but you’ve set neighborhoodId, so raise
        raise RuntimeError(
            f"HTTP {status} / JSON {j.get('statusCode')}: {str(j)[:300]}"
        )

    raise RuntimeError("Gave up after 405 retries")


if __name__ == "__main__":
    print(post_deals_neighborhood("65210036"))
