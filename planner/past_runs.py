import os
import requests
from dotenv import load_dotenv
from utils import format_pace

# Load Variables
load_dotenv()

# Strava API endpoints
STRAVA_AUTH_URL = "https://www.strava.com/oauth/token"
STRAVA_ACTIVITIES_URL = "https://www.strava.com/api/v3/athlete/activities"
STRAVA_ATHLETE_URL = "https://www.strava.com/api/v3/athlete"

# Exchange stored refresh token for a short-lived access token.
def get_strava_access_token():
    payload = {
        "client_id": os.getenv("STRAVA_CLIENT_ID"), # App's client ID
        "client_secret": os.getenv("STRAVA_CLIENT_SECRET"), # App's client secret
        "refresh_token": os.getenv("STRAVA_REFRESH_TOKEN"), # Long-lived refresh token
        "grant_type": "refresh_token", # Tell Strava we're refreshing the token
    }

    # Request a new access token from Strava
    r = requests.post(STRAVA_AUTH_URL, data=payload)
    if r.status_code != 200:
        raise RuntimeError(f"Token refresh failed {r.status_code}: {r.text}")

    # Return the short-lived access token from Strava's response
    return r.json()["access_token"]

def fetch_recent_runs(limit=5):
    # Get a valid short-lived access token
    token = get_strava_access_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Optional sanity check
    r0 = requests.get(STRAVA_ATHLETE_URL, headers=headers)
    if r0.status_code != 200:
        raise RuntimeError(f"/athlete failed {r0.status_code}: {r0.text}")

    # Fetch recent activities
    r = requests.get(STRAVA_ACTIVITIES_URL, headers=headers, params={"per_page": limit, "page": 1})
    if r.status_code != 200:
        raise RuntimeError(f"/athlete/activities failed {r.status_code}: {r.text}")

    runs = []
    for a in r.json():
        if a.get("type") == "Run": # Only keep runs, ignore rides/swims/etc.
            runs.append({
                "name": a.get("name"), # Run title from Strava
                "distance_km": (a.get("distance") or 0) / 1000.0, # Convert meters → kilometers
                "moving_time_min": (a.get("moving_time") or 0) / 60.0, # Convert seconds → minutes
                "average_speed_kmh": (a.get("average_speed") or 0) * 3.6, # Convert m/s → km/h
                "pace_str": format_pace((a['moving_time'] / 60) / (a['distance'] / 1000)) # Calculate pace
            })
    return runs
