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
    """Trims down extended names like 'national football team' from raw inputs."""
    if not name:
        return "TBD"
    for extra in [" national football team", " national soccer team", " men's national soccer team", " cricket team"]:
        name = name.replace(extra, "")
    return name.strip()

def get_flag(clean_name):
    """Converts team name to Unicode Regional Indicator flag emojis."""
    code = COUNTRY_MAP.get(clean_name, "")
    if not code:
        return "🏳️" # Fallback flag for unconfirmed knockout lines (e.g. Winner Group A)
    if code == "GB-ENG": return "🏴󠁧󠁢󠁥󠁮󠁧󠁿"
    if code == "GB-SCT": return "🏴󠁧󠁢󠁳󠁣󠁴󠁿"
    return "".join(chr(127397 + ord(c)) for c in code.upper())

def get_short_code(clean_name):
    """Returns standard uppercase abbreviation alongside flags."""
    full_code = COUNTRY_MAP.get(clean_name, "??")
    return full_code.split("-")[-1]

def fetch_live_fixtures():
    """Pulls global schedules directly via open tournament JSON APIs."""
    url = "https://worldcup26.ir/get/games"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Primary API mirror unavailable: {e}. Trying fallback open source data layer...")
        # Fallback mirroring directly to a live raw data repository backup
        fallback_url = "https://raw.githubusercontent.com/rezarahiminia/worldcup2026/main/data/mock.json"
        try:
            res = requests.get(fallback_url, timeout=15)
            return res.json()
        except Exception as err:
            print(f"Critical Error: Both live data engines failed: {err}")
            return None

def parse_iso_to_ics_time(iso_str):
    """Normalizes ISO string patterns into explicit standard calendar UTC blocks."""
    # Removes standard separating punctuation characters commonly returned by APIs
    cleaned = iso_str.replace("-", "").replace(":", "").split(".")[0]
    if not cleaned.endswith("Z"):
        cleaned += "Z"
    return cleaned

def generate_calendar():
    raw_data = fetch_live_fixtures()
    if not raw_data:
        print("Halting compilation to prevent corrupting existing calendar file.")
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
        "X-WR-CALDESC:World Cup matches with automatically adjusting kickoff times and flags."
    ]

    # Checking for array wrapper variations across multi-source endpoints
    matches = raw_data if isinstance(raw_data, list) else raw_data.get("games", raw_data.get("matches", []))

    for idx, match in enumerate(matches):
        # Graceful normalization checking for key mapping variants
        home_raw = match.get("homeTeam", match.get("home", "TBD"))
        away_raw = match.get("awayTeam", match.get("away", "TBD"))
        
        # Handle embedded objects versus raw strings
        home = clean_team_name(home_raw if isinstance(home_raw, str) else home_raw.get("name", "TBD"))
        away = clean_team_name(away_raw if isinstance(away_raw, str) else away_raw.get("name", "TBD"))
        
        # Pull timestamps
        start_raw = match.get("startTimeUserTimezone", match.get("utcDate", match.get("start", "")))
        if not start_raw:
            continue
            
        dtstart = parse_iso_to_ics_time(start_raw)
        
        # Calculate artificial end window (roughly 2 hours after kickoff)
        start_obj = datetime.datetime.strptime(dtstart, "%Y%m%dT%H%M%SZ")
        dtend = (start_obj + datetime.timedelta(hours=2)).strftime("%Y%m%dT%H%M%SZ")
        
        venue = match.get("venue", "TBD Venue")
        group = match.get("groupName", match.get("group", "Tournament Match"))
        match_id = match.get("id", f"gen-idx-{idx}")

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

    # Outputs the structural file back to the repository root directory
    with open("world-cup.ics", "w", encoding="utf-8") as file:
        file.write("\n".join(lines))
    print("Success: world-cup.ics compiled cleanly via live network pipeline.")

if __name__ == "__main__":
    generate_calendar()
