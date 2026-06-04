import os
import datetime
import requests

# Maps official FIFA data team names to ISO codes for the flag generator
COUNTRY_MAP = {
    "Mexico": "MX", "South Africa": "ZA", "South Korea": "KR", "Czech Republic": "CZ",
    "Canada": "CA", "Bosnia and Herzegovina": "BA", "United States": "US", "USA": "US",
    "Paraguay": "PY", "Haiti": "HT", "Scotland": "GB-SCT", "Morocco": "MA",
    "Australia": "AU", "Turkey": "TR", "Brazil": "BR", "Qatar": "QA",
    "Switzerland": "CH", "Germany": "DE", "Curaçao": "CW", "Netherlands": "NL",
    "Japan": "JP", "Ivory Coast": "CI", "Ecuador": "EC", "Sweden": "SE", "Tunisia": "TN",
    "Saudi Arabia": "SA", "Uruguay": "UY", "Spain": "ES", "Cape Verde": "CV", "Iran": "IR",
    "New Zealand": "NZ", "Belgium": "BE", "Egypt": "EG", "France": "FR", "Senegal": "SN",
    "Iraq": "IQ", "Norway": "NO", "Argentina": "AR", "Algeria": "DZ", "Austria": "AT",
    "Jordan": "JO", "Portugal": "PT", "DR Congo": "CD", "England": "GB-ENG", "Croatia": "HR",
    "Ghana": "GH", "Panama": "PA", "Uzbekistan": "UZ", "Colombia": "CO"
}

def get_flag(team_name):
    if not team_name:
        return "🏳️"
    code = COUNTRY_MAP.get(team_name, "")
    if not code:
        return "🏳️"  # Standard placeholder for undecided knockout lines (e.g. "Winner Group A")
    if code == "GB-ENG": return "🏴󠁧󠁢󠁥󠁮󠁧󠁿"
    if code == "GB-SCT": return "🏴󠁧󠁢󠁳󠁣󠁴󠁿"
    return "".join(chr(127397 + ord(c)) for c in code.upper())

def get_short_code(team_name):
    if not team_name:
        return "TBD"
    return COUNTRY_MAP.get(team_name, "??").split("-")[-1].upper()

def fetch_official_fixtures():
    # Official FIFA World Cup competition code is 'WC'
    url = "https://api.football-data.org/v4/competitions/WC/matches"
    
    # Safely extract the secret token from the secure environment injection
    api_token = os.environ.get("FOOTBALL_API_KEY")
    if not api_token:
        print("Error: Missing secure FOOTBALL_API_KEY environment configuration.")
        return None
        
    headers = {"X-Auth-Token": api_token}
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Critical error pulling official API payload: {e}")
        return None

def parse_iso_to_ics(iso_str):
    # Converts standard '2026-06-11T21:00:00Z' into calendar format '20260611T210000Z'
    return iso_str.replace("-", "").replace(":", "")

def generate_calendar():
    data = fetch_official_fixtures()
    if not data or "matches" not in data:
        print("Invalid data layout returned from endpoint. Retaining previous file state.")
        return

    now_utc = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//YourName//World Cup Official Sync//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:🏆 FIFA World Cup 2026 Schedule",
        "X-WR-TIMEZONE:UTC",
        "X-WR-CALDESC:Official World Cup fixtures synced straight from live tournament data."
    ]

    for match in data["matches"]:
        # Extract parsing items cleanly following official documentation guidelines
        home_team = match.get("homeTeam", {}) or {}
        away_team = match.get("awayTeam", {}) or {}
        
        home = home_team.get("name", "TBD")
        away = away_team.get("name", "TBD")
        
        # Pull standard kickoff parameters
        utc_date = match.get("utcDate")
        if not utc_date:
            continue
            
        dtstart = parse_iso_to_ics(utc_date)
        
        # Add 2-hour window duration block
        start_obj = datetime.datetime.strptime(dtstart, "%Y%m%dT%H%M%SZ")
        dtend = (start_obj + datetime.timedelta(hours=2)).strftime("%Y%m%dT%H%M%SZ")
        
        stage = match.get("stage", "Tournament Match").replace("_", " ").title()
        group_info = match.get("group", "")
        group_label = f" ({group_info.replace('_', ' ')})" if group_info else ""
        
        h_flag = get_flag(home)
        a_flag = get_flag(away)
        h_code = get_short_code(home)
        a_code = get_short_code(away)

        summary = f"{h_flag} {h_code} vs {a_code} {a_flag} | {stage}{group_label}"
        description = f"Matchup: {home} vs {away}\\nStage: {stage}{group_label}\\nMatch Day: {match.get('matchday', 'N/A')}"
        
        lines.extend([
            "BEGIN:VEVENT",
            f"UID:wc2026-{match['id']}@football-data.org",
            f"DTSTAMP:{now_utc}",
            f"DTSTART:{dtstart}",
            f"DTEND:{dtend}",
            f"SUMMARY:{summary}",
            f"DESCRIPTION:{description}",
            "END:VEVENT"
        ])

    lines.append("END:VCALENDAR")

    with open("world-cup.ics", "w", encoding="utf-8") as file:
        file.write("\n".join(lines))
    print(f"Success! Official .ics calendar generated with {len(data['matches'])} active matches.")

if __name__ == "__main__":
    generate_calendar()
