import os
import datetime

# 1. Map typical team strings to ISO country codes to generate precise flags
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

def get_flag(country_name):
    """Converts country name to Unicode Regional Indicator flag emojis."""
    code = COUNTRY_MAP.get(country_name, "")
    if not code:
        return ""
    # Handle specific UK subdivisions if needed, default to standard flags
    if code == "GB-ENG": return "🏴󠁧󠁢󠁥󠁮󠁧󠁿"
    if code == "GB-SCT": return "🏴󠁧󠁢󠁳󠁣󠁴󠁿"
    
    # Mathematical magic: shift characters to the regional flag blocks
    return "".join(chr(127397 + ord(c)) for c in code.upper())

def get_short_code(country_name):
    """Returns standard abbreviation for space saving alongside flags."""
    full_code = COUNTRY_MAP.get(country_name, "UN")
    return full_code.split("-")[-1]

# 2. Live fixture dictionary mimicking API updates or official schedule pipelines
# Dates are structured natively in UTC format (YYYYMMDDTHHMMSSZ)
FIXTURES = [
    {
        "id": "match1",
        "home": "Mexico", "away": "South Africa",
        "start": "20260611T210000Z", "end": "20260611T230000Z",
        "venue": "Mexico City Stadium", "group": "Group A"
    },
    {
        "id": "match2",
        "home": "South Korea", "away": "Czech Republic",
        "start": "20260612T040000Z", "end": "20260612T060000Z",
        "venue": "Estadio Guadalajara", "group": "Group A"
    },
    {
        "id": "match3",
        "home": "Canada", "away": "Bosnia and Herzegovina",
        "start": "20260612T210000Z", "end": "20260612T230000Z",
        "venue": "Toronto Stadium", "group": "Group B"
    },
    {
        "id": "match4",
        "home": "United States", "away": "Paraguay",
        "start": "20260613T030000Z", "end": "20260613T050000Z",
        "venue": "Los Angeles Stadium", "group": "Group D"
    }
]

def generate_ics():
    now_utc = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//YourName//World Cup 2026 Flags Sync//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:🏆 World Cup 2026 Schedule",
        "X-WR-TIMEZONE:UTC",
        "X-WR-CALDESC:World cup fixtures with cross-platform country flag indicators."
    ]
    
    for f in FIXTURES:
        h_flag = get_flag(f["home"])
        a_flag = get_flag(f["away"])
        h_code = get_short_code(f["home"])
        a_code = get_short_code(f["away"])
        
        # Combined layout ensures accessibility for systems with broken emoji renders (Windows)
        summary = f"{h_flag} {h_code} vs {a_code} {a_flag} | {f['group']}"
        description = f"Tournament: FIFA World Cup 2026\\nMatchup: {f['home']} vs {f['away']}\\nStage: {f['group']}"
        
        lines.extend([
            "BEGIN:VEVENT",
            f"UID:wc2026-{f['id']}@yourdomain.com",
            f"DTSTAMP:{now_utc}",
            f"DTSTART:{f['start']}",
            f"DTEND:{f['end']}",
            f"SUMMARY:{summary}",
            f"DESCRIPTION:{description}",
            f"LOCATION:{f['venue']}",
            "END:VEVENT"
        ])
        
    lines.append("END:VCALENDAR")
    
    # Save file into the local repository layout
    with open("world-cup.ics", "w", encoding="utf-8") as file:
        file.write("\n".join(lines))

if __name__ == "__main__":
    generate_ics()
