"""Build the Sindh health-facility dataset the danger gate points women to.

Why this is a script and not a hand-written file: the escalation path must
never name a facility that does not exist. Asking an LLM for "the nearest
clinic to Tando Allahyar" produces confident, plausible, sometimes invented
names -- on the one path where a woman may be haemorrhaging, that costs the
minutes that matter. So every row here comes from OpenStreetMap and is
regenerable, auditable, and traceable to an OSM element id.

Output: data/facilities/sindh_health_facilities.json
    {"generated": "...", "source": "...", "count": N, "facilities": [
       {"id","name","kind","lat","lon","district","phone","emergency"} ]}

Coordinates are rounded to 5 decimal places (~1m) -- more precision than that
is false confidence for OSM-sourced points, and it keeps the bundle small
enough to ship to a phone on a weak rural connection.

Re-run with:  python scripts/fetch_health_facilities.py
"""

import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

# Sindh bounding box (south, west, north, east).
BBOX = (23.6, 66.6, 28.6, 71.2)

MIRRORS = [
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

OUT_PATH = os.path.join("data", "facilities", "sindh_health_facilities.json")
# The frontend fetches this on demand -- only once an escalation actually
# happens -- so it stays out of the initial bundle a rural phone has to load.
WEB_PATH = os.path.join("frontend", "public", "sindh_health_facilities.json")

QUERY = (
    "[out:json][timeout:180];"
    '(node["amenity"~"^(hospital|clinic|doctors)$"]({0},{1},{2},{3});'
    ' way["amenity"~"^(hospital|clinic|doctors)$"]({0},{1},{2},{3}););'
    "out center;"
).format(*BBOX)

# OSM `amenity` is coarse. Pakistan's public system is tiered, and the tier is
# what tells a woman whether the place can actually admit her: BHU (Basic
# Health Unit) and RHC (Rural Health Centre) are outpatient, THQ (Tehsil HQ)
# and DHQ (District HQ) hospitals have inpatient and usually emergency
# obstetric care. The name almost always carries the tier, so read it there.
TIERS = [
    ("dhq", ("dhq", "district headquarter", "district head quarter", "civil hospital")),
    ("thq", ("thq", "tehsil headquarter", "taluka headquarter", "taluka hospital")),
    ("rhc", ("rhc", "rural health centre", "rural health center")),
    ("bhu", ("bhu", "basic health unit")),
    ("mch", ("mch", "maternity", "maternal", "gynae", "children")),
]


# OSM's `amenity=hospital` is applied loosely: diagnostic labs, dental
# surgeries, pharmacies and physiotherapy rooms all carry it. None of them can
# take a woman who is bleeding, and offering one as "your nearest hospital"
# during an escalation actively sends her the wrong way. Drop them by name.
EXCLUDE = (
    "laborator", " lab", "lab ", "diagnostic", "pathology", "x-ray", "xray",
    "radiolog", "ultrasound", "dental", "dentist", "orthodont", "pharmac",
    "medical store", "chemist", "optical", "optician", "eye care",
    "physiotherap", "homeopath", "hakeem", "veterinar", "blood bank",
)


def is_usable(name: str) -> bool:
    low = (name or "").lower()
    return not any(bad in low for bad in EXCLUDE)


def classify(name: str, amenity: str) -> str:
    low = (name or "").lower()
    for tier, needles in TIERS:
        if any(n in low for n in needles):
            return tier
    return {"hospital": "hospital", "clinic": "clinic", "doctors": "clinic"}.get(amenity, "clinic")


def fetch() -> dict:
    body = urllib.parse.urlencode({"data": QUERY}).encode()
    last = None
    for mirror in MIRRORS:
        try:
            print(f"  querying {mirror} ...", flush=True)
            req = urllib.request.Request(
                mirror, data=body,
                headers={"User-Agent": "naari-ai-fyp/1.0 (SZABIST academic project)"})
            with urllib.request.urlopen(req, timeout=200) as resp:
                return json.load(resp)
        except Exception as exc:  # mirrors rate-limit and time out routinely
            last = f"{type(exc).__name__}: {exc}"
            print(f"    failed -- {last}", flush=True)
            time.sleep(2)
    raise SystemExit(f"every Overpass mirror failed; last error was {last}")


def main() -> None:
    raw = fetch()
    facilities = []
    for el in raw.get("elements", []):
        tags = el.get("tags", {})
        name = (tags.get("name") or "").strip()
        if not name:
            continue  # an unnamed point cannot be given to a woman as a destination
        if not is_usable(name):
            continue  # a lab or dental surgery is not somewhere to send an emergency
        lat = el.get("lat") or el.get("center", {}).get("lat")
        lon = el.get("lon") or el.get("center", {}).get("lon")
        if lat is None or lon is None:
            continue
        facilities.append({
            "id": f"{el['type']}/{el['id']}",
            "name": name,
            "kind": classify(name, tags.get("amenity", "")),
            "lat": round(float(lat), 5),
            "lon": round(float(lon), 5),
            "district": (tags.get("addr:district") or tags.get("addr:city") or "").strip(),
            "phone": (tags.get("phone") or tags.get("contact:phone") or "").strip(),
            "emergency": tags.get("emergency") == "yes",
        })

    facilities.sort(key=lambda f: (f["kind"], f["name"]))
    payload = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "OpenStreetMap via Overpass API, ODbL",
        "bbox": list(BBOX),
        "count": len(facilities),
        "facilities": facilities,
    }

    for path in (OUT_PATH, WEB_PATH):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, separators=(",", ":"))

    by_kind = {}
    for f in facilities:
        by_kind[f["kind"]] = by_kind.get(f["kind"], 0) + 1
    print(f"\nwrote {OUT_PATH}  ({len(facilities)} facilities, "
          f"{os.path.getsize(OUT_PATH)/1024:.0f} KB)")
    for kind, n in sorted(by_kind.items(), key=lambda kv: -kv[1]):
        print(f"  {kind:9} {n}")
    print(f"  with phone   {sum(1 for f in facilities if f['phone'])}")


if __name__ == "__main__":
    sys.exit(main())
