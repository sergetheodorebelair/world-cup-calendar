import os
import datetime
import requests

# Dictionary mapping official names to ISO two-letter codes for perfect flags
COUNTRY_MAP = {
    "Mexico": "MX", "South Africa": "ZA", "South Korea": "KR", "Czech Republic": "CZ",
    "Czechia": "CZ", "Canada": "CA", "Bosnia and Herzegovina": "BA", "United States": "US",
    "USA": "US", "Paraguay": "PY", "Haiti": "HT", "Scotland": "GB-SCT", "Morocco": "MA",
    "Australia": "AU", "Türkiye": "TR", "Turkey": "TR", "Brazil": "BR", "Qatar": "QA",
    "Switzerland": "CH", "Germany": "DE", "Curaçao": "CW", "Netherlands": "NL",
    "Japan": "JP", "Ivory Coast": "CI", "Ecuador": "EC", "Sweden": "SE", "Tunisia": "TN",
    "Saudi Arabia": "SA", "Uruguay": "UY", "Spain": "ES", "Cape Verde": "CV", "Iran": "IR",
    "New Zealand": "NZ", "Belgium": "BE", "Egypt": "EG", "France": "FR", "Senegal": "SN",
    "Iraq": "IQ", "Norway": "NO", "Argentina": "AR", "Algeria": "DZ", "Austria": "AT",
    "Jordan": "JO", "Portugal": "PT", "DR Congo": "CD", "England": "GB-ENG", "Croatia": "HR",
    "Ghana": "GH", "Panama": "PA", "Uzbekistan": "UZ", "Colombia": "CO"
}

def clean_team_name(name):
    if not name:
        return "TBD"
    # Normalizing potential string variation outputs from the live mirror
    name = str(name)
    for extra in [" national football team", " national soccer team", " men's national soccer team"]:
        name = name.replace(extra, "")
    return name.strip()

def get_flag(clean_name):
    code = COUNTRY_MAP.get(clean_name, "")
    if not code:
        return "🏳️" 
    if code == "GB-ENG": return "🏴%A0%BC%A7%A1%A0%BC%A7%A7%A0%BC%A7%A5%A0%BC%A7%A7%A0%BC%A7%A2%A0%BC%A7%A7" # Explicit unicode sub-properties for UK flags
    if code == "GB-SCT": return "🏴%A0%BC%A7%A1%A0%BC%A7%A7%A0%BC%A7%A3%A0%BC%A7%A7%A0%BC%A7%A4%A0%BC%A7%A7"
    return "".join(chr(127397 + ord(c)) for c in code.upper())

def get_short_code(clean_name):
    full_code = COUNTRY_MAP.get(clean_name, "??")
    return full_code.split("-")[-1]

def fetch_live_fixtures():
    url = "https://worldcup26.ir/get/games"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        # Ensure array structure format tracking variations
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("games", data.get("matches", data.get("data", [])))
        return []
    except Exception as e:
        print(f"API Request failed: {e}. Pulling backup live mock fallback layer...")
        fallback_url = "https://raw.githubusercontent.com/rezarahiminia/worldcup2026/main/data/mock.json"
        try:
            res = requests.get(fallback_url, timeout=15)
            data = res.json()
            return data if isinstance(data, list) else data.get("games", [])
        except Exception as err:
            print(f"Critical error: Fallback layer also failed: {err}")
            return []

def parse_iso_to_ics_time(iso_str):
    if not iso_str:
        return datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    cleaned = iso_str.replace("-", "").replace(":", "").split(".")[0].split("+")[0]
    if not cleaned.endswith("Z"):
        cleaned += "Z"
    return cleaned

def generate_calendar():
    matches = fetch_live_fixtures()
    if not matches:
        print("Empty dataset fetched. Skipping sync update rewrite.")
        return

    now_utc = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//YourName//World Cup Live Sync//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:🏆 World Cup 2026 Live Schedule",
        "X-WR-TIMEZONE:UTC",
        "X-WR-CALDESC:World Cup matches with auto-adjusting kickoff times and flag emojis."
    ]

    for idx, match in enumerate(matches):
        if not isinstance(match, dict):
            continue

        # Safe dictionary property extraction mapping variations used by the REST schema
        home_data = match.get("homeTeam", match.get("home", "TBD"))
        away_data = match.get("awayTeam", match.get("away", "TBD"))
        
        home = clean_team_name(home_data if isinstance(home_data, str) else home_data.get("name", home_data.get("title", "TBD")))
        away = clean_team_name(away_data if isinstance(away_data, str) else away_data.get("name", away_data.get("title", "TBD")))
        
        start_raw = match.get("startTimeUserTimezone", match.get("utcDate", match.get("date", match.get("start", ""))))
        if not start_raw:
            continue
            
        dtstart = parse_iso_to_ics_time(start_raw)
        
        try:
            start_obj = datetime.datetime.strptime(dtstart, "%Y%m%dT%H%M%SZ")
        except ValueError:
            # Fallback format protection parsing string patterns
            try:
                start_obj = datetime.datetime.strptime(dtstart, "%Y-%m-%d %H:%M:%S")
                dtstart = start_obj.strftime("%Y%m%dT%H%M%SZ")
            except:
                continue
                
        dtend = (start_obj + datetime.timedelta(hours=2)).strftime("%Y%m%dT%H%M%SZ")
        
        venue = match.get("venue", match.get("stadium", "TBD Venue"))
        group = match.get("groupName", match.get("group", "Tournament Match"))
        match_id = match.get("id", match.get("_id", f"gen-idx-{idx}"))

        h_flag = get_flag(home)
        a_flag = get_flag(away)
        h_code = get_short_code(home)
        a_code = get_short_code(away)

        summary = f"{h_flag} {h_code} vs {a_code} {a_flag} | {group}"
        description = f"Tournament: FIFA World Cup 2026\\nMatchup: {home} vs {away}\\nStage: {group}\\nVenue: {venue}"
        
        lines.extend([
            "BEGIN:VEVENT",
            f"UID:wc2026-{match_id}@yourdomain.com",
            f"DTSTAMP:{now_utc}",
            f"DTSTART:{dtstart}",
            f"DTEND:{dtend}",
            f"SUMMARY:{summary}",
            f"DESCRIPTION:{description}",
            f"LOCATION:{venue}",
            "END:VEVENT"
        ])

    lines.append("END:VCALENDAR")

    with open("world-cup.ics", "w", encoding="utf-8") as file:
        file.write("\n".join(lines))
    print(f"Success: world-cup.ics generated cleanly with {len(lines) // 10} fixture entries.")

if __name__ == "__main__":
    generate_calendar()
