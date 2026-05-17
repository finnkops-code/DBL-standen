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

def strip_tags(text):
    return re.sub(r'<[^>]+>', '', text).strip()

def clean_number(text):
    text = strip_tags(text).strip()
    return text if text else '-'

def parse_standings(html):
    result = {}

    parts = re.split(r'<h3[^>]*>(.*?)</h3>', html, flags=re.DOTALL)

    i = 1
    while i < len(parts):
        divisie_naam = strip_tags(parts[i]).strip()
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
            if len(tds_raw) < 4:
                continue

            # Kolom 0: positie
            positie = clean_number(tds_raw[0])
            if not re.match(r'^\d+$', positie):
                continue

            # Kolom 1: teamcel met <a title="Teamnaam"> en <img src="...">
            teamcel = tds_raw[1]

            naam_match = re.search(r'<a[^>]+title=["\']([^"\']+)["\']', teamcel)
            if naam_match:
                teamnaam = naam_match.group(1).strip()
                teamnaam = re.sub(r'\s*Logo\s*$', '', teamnaam, flags=re.IGNORECASE).strip()
            else:
                teamnaam = strip_tags(teamcel).strip()
                if not teamnaam:
                    continue

            logo_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', teamcel)
            logo_url = logo_match.group(1).strip() if logo_match else ''
            if logo_url and logo_url.startswith('/'):
                logo_url = 'https://www.baseball.de' + logo_url

            # Kolommen 2+: W, L, PCT, GB
            cijfers = [clean_number(td) for td in tds_raw[2:]]

            rij = {
                "positie":  positie,
                "team":     teamnaam,
                "logo_url": logo_url,
                "w":        cijfers[0] if len(cijfers) > 0 else '-',
                "l":        cijfers[1] if len(cijfers) > 1 else '-',
                "pct":      cijfers[2] if len(cijfers) > 2 else '-',
                "gb":       cijfers[3] if len(cijfers) > 3 else '-',
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

    for divisie, rijen in standen.items():
        print(f"\n{divisie}:")
        for r in rijen:
            print(f"  {r['positie']}. {r['team']} | W:{r['w']} L:{r['l']} PCT:{r['pct']} GB:{r['gb']}")

    output = {
        "bijgewerkt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "bron":       URL,
        "standen":    standen,
    }

    with open("dbl_standen.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("\n✅ dbl_standen.json opgeslagen")

if __name__ == "__main__":
    main()
