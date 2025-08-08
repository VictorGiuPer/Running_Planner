import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

def get_next_planned_run():
    # 1. Authenticate using service account
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)

    # 2. Open the spreadsheet and worksheet
    spreadsheet = client.open("FITNESS")
    sheet = spreadsheet.worksheet("Long Runs")

    # 3. Define expected column headers
    headers = ["Week #", "Date (Saturday)", "Distance (Planned)"]  # <-- Adjust based on print output

    # 4. Read all rows as dictionaries
    data = sheet.get_all_records(expected_headers=headers, head=1)

    # 5. Get today's date to find the next future run
    today = datetime.today().date()

    for row in data:
        try:
            # Parse the run date using German format: DD.MM.YYYY
            run_date_str = str(row["Date (Saturday)"])
            run_date = datetime.strptime(run_date_str, "%d.%m.%Y").date()
        except ValueError:
            # If parsing fails (e.g., blank or malformed date), skip this row
            print(f"⚠️ Could not parse date: {row['Date (Saturday)']}")
            continue
        
        # If the run is today or later, return it as the next planned run
        if run_date >= today:
            distance_km = parse_german_float(row["Distance (Planned)"])
            return {
                "date": run_date,
                "distance_km": distance_km,
                "week": row.get("Week #")
            }
        
    # If no upcoming runs were found, return None
    return None


def parse_german_float(value):
    if isinstance(value, (int, float)) and value > 100:
        return value / 100
    return float(str(value).replace(",", "."))
