import json
import re
import urllib.request
from datetime import datetime, timezone

URL = "https://www.baseball.de/saison/tabellen"

def fetch_html(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
        "Accept-Language": "de-DE,de;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")

def clean(text):
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def parse_standings(html):
    result = {}

    # Zoek alle h3-koppen (Noord / Zuid) en de tabel die erop volgt
    parts = re.split(r'<h3[^>]*>(.*?)</h3>', html, flags=re.DOTALL)

    i = 1
    while i < len(parts):
        divisie_naam = clean(parts[i])
        rest = parts[i + 1] if i + 1 < len(parts) else ''

        table_match = re.search(r'<table[^>]*>(.*?)</table>', rest, re.DOTALL)
        if not table_match:
            i += 2
            continue

        table_html = table_match.group(1)
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL)

        divisie_rijen = []
        for row in rows:
            tds_raw = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
            tds = [clean(td) for td in tds_raw]
            tds = [t for t in tds if t != '']

            if len(tds) < 4:
                continue

            # Eerste cel = positie (getal)
            positie = tds[0] if re.match(r'^\d+$', tds[0]) else '-'

            # Tweede cel = teamnaam
            team = tds[1] if len(tds) > 1 else ''
            if not team:
                continue

            # Resterende cellen = W, L, PCT, GB
            cijfers = tds[2:]

            rij = {
                "positie": positie,
                "team":    team,
                "w":       cijfers[0] if len(cijfers) > 0 else '-',
                "l":       cijfers[1] if len(cijfers) > 1 else '-',
                "pct":     cijfers[2] if len(cijfers) > 2 else '-',
                "gb":      cijfers[3] if len(cijfers) > 3 else '-',
            }
            divisie_rijen.append(rij)

        if divisie_rijen:
            result[divisie_naam] = divisie_rijen

        i += 2

    return result

def main():
    print(f"Ophalen van {URL}...")
    html = fetch_html(URL)
    print(f"Ontvangen: {len(html)} bytes")

    standen = parse_standings(html)
    print(f"Gevonden divisies: {list(standen.keys())}")

    output = {
        "bijgewerkt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "bron":       URL,
        "standen":    standen,
    }

    with open("dbl_standen.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("✅ dbl_standen.json opgeslagen")

if __name__ == "__main__":
    main()
