import os
import requests
import random
from math import radians, degrees, sin, cos, asin, atan2
from dotenv import load_dotenv

# Load API keys from .env file
load_dotenv()
GOOGLE_DIRECTIONS_KEY = os.getenv("GOOGLE_DIRECTIONS_KEY")
GOOGLE_GEOCODING_KEY = os.getenv("GOOGLE_GEOCODING_KEY")

# ---------- GEOCODING: Convert address to GPS coordinates ----------
def geocode_address(address: str) -> tuple[float, float]:
    """Address → (lat, lng) via Google Geocoding API."""
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": address, "key": GOOGLE_GEOCODING_KEY}
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()

    # If no results, fail early
    if not data.get("results"):
        raise ValueError(f"Address not found: {address}")
    
    # Extract first result's coordinates
    loc = data["results"][0]["geometry"]["location"]
    return (loc["lat"], loc["lng"])

# ---------- BEARING & COORDINATE HELPERS ----------
def _norm_bearing(b: float) -> float:
    """Normalize degrees into [0, 360)."""
    b = b % 360.0
    return b if b >= 0 else b + 360.0

def destination_point(lat: float, lng: float, bearing_deg: float, distance_m: float) -> tuple[float, float]:
    """Given a starting lat/lng, a bearing (degrees), and a distance (meters),
    compute the resulting lat/lng using spherical trigonometry."""
    R = 6371000 # Earth radius in meters
    b = radians(bearing_deg) # convert bearing to radians
    lat1 = radians(lat)
    lng1 = radians(lng)

    # Calculate the destination latitude
    lat2 = asin(sin(lat1) * cos(distance_m / R) + cos(lat1) * sin(distance_m / R) * cos(b))

    # Calculate the destination longitude
    lng2 = lng1 + atan2(sin(b) * sin(distance_m / R) * cos(lat1),
                        cos(distance_m / R) - sin(lat1) * sin(lat2))
    
    return (degrees(lat2), degrees(lng2)) # convert back to degrees

# ---------- DIRECTIONS API — Distance Calculation Helpers ----------
def _directions_distance_km(origin_str: str, waypoints_str: str) -> float:
    """Call Directions API for origin -> waypoints -> origin (walking) and return total km."""
    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": origin_str,
        "destination": origin_str,      # loop closes at start
        "waypoints": waypoints_str,     # e.g. "lat1,lng1|lat2,lng2"
        "mode": "walking",
        "key": GOOGLE_DIRECTIONS_KEY,
    }
    r = requests.get(url, params=params, timeout=25)
    r.raise_for_status()
    data = r.json()

    if data.get("status") != "OK":
        raise RuntimeError(f"Directions API error: {data.get('status')} - {data.get('error_message')}")
    
    # Sum up the distance of all legs in meters
    total_m = 0
    for leg in data["routes"][0]["legs"]:
        total_m += leg["distance"]["value"]
    return total_m / 1000.0

def _build_loop_waypoints_str(start_lat: float, start_lng: float, hop_km: float, bearing_deg: float) -> str:
    """Return 'lat,lng|lat,lng' for WP1 and WP2 (START is destination)."""
    hop_m = hop_km * 1000.0 # convert km to meters
    b1 = _norm_bearing(bearing_deg)
    b2 = _norm_bearing(bearing_deg + 60.0)  # 60° turn towards returning

    # Return only WP1 and WP2 - start is implied
    wp1 = destination_point(start_lat, start_lng, b1, hop_m)
    wp2 = destination_point(wp1[0], wp1[1], b2, hop_m)
    return f"{wp1[0]},{wp1[1]}|{wp2[0]},{wp2[1]}"

# ---------- CALIBRATE LOOP SIZE ----------
def calibrate_loop_hop(
    start_lat: float,
    start_lng: float,
    target_loop_km: float,
    bearing_deg: float,
    max_iters: int = 6,
    tol_km: float = 0.2,
) -> tuple[list[tuple[float, float]], float, float]:
    """
    Iteratively adjust hop_km so loop (Start->WP1->WP2->Start) ≈ target_loop_km.
    Returns: (waypoints_list [WP1, WP2, START], measured_loop_km, hop_km_used)
    """
    origin = f"{start_lat},{start_lng}"
    hop_km = max(0.8, target_loop_km / 3.0)  # initial guess: loop ~ 3 hops

    last_wps_str = None
    for _ in range(max_iters):
        # Build candidate loop
        wps_str = _build_loop_waypoints_str(start_lat, start_lng, hop_km, bearing_deg)

        # Measure loop distance
        loop_km = _directions_distance_km(origin, wps_str)
        err = target_loop_km - loop_km

        # Stop if close enough to target
        if abs(err) <= tol_km:
            last_wps_str = wps_str
            break

        # Adjust hop length proportionally to distance error
        scale = max(0.6, min(1.4, target_loop_km / max(loop_km, 0.3)))
        hop_km *= scale # new hop length for next iteration
        last_wps_str = wps_str

    # Extract final coordinates for waypoints
    wp_parts = (last_wps_str or _build_loop_waypoints_str(start_lat, start_lng, hop_km, bearing_deg)).split("|")
    wp1_lat, wp1_lng = map(float, wp_parts[0].split(","))
    wp2_lat, wp2_lng = map(float, wp_parts[1].split(","))
    waypoints = [(wp1_lat, wp1_lng), (wp2_lat, wp2_lng), (start_lat, start_lng)]

    # Get the measured loop length for reporting
    measured_km = _directions_distance_km(origin, f"{wp1_lat},{wp1_lng}|{wp2_lat},{wp2_lng}")
    return waypoints, measured_km, hop_km

# ---------- BUILD TWO CALIBRATED LOOPS (A & B) ----------
def build_two_calibrated_loops(
    start_lat: float,
    start_lng: float,
    target_loop_km: float,
    initial_bearing_deg: float,
) -> tuple[list[tuple[float, float]], float, float]:
    """
    Calibrate hop separately for Loop A (initial) and Loop B (opposite).
    Returns: (combined_waypoints [A_wp1, A_wp2, START, B_wp1, B_wp2, START], loopA_km, loopB_km)
    """
    b0 = _norm_bearing(initial_bearing_deg)
    b_opposite = _norm_bearing(b0 + 180.0) # reverse direction

    # Calibrate both loops separately
    loopA_wps, loopA_km, _ = calibrate_loop_hop(start_lat, start_lng, target_loop_km, b0)
    loopB_wps, loopB_km, _ = calibrate_loop_hop(start_lat, start_lng, target_loop_km, b_opposite)

    # Return combined waypoint list and loop lengths
    return loopA_wps + loopB_wps, loopA_km, loopB_km

# ---------- GENERATE FINAL GOOGLE MAPS LINK ----------
def _sum_legs_km(directions_json: dict, leg_indices: list[int]) -> float:
    """Sum specific legs (by index) from the first route and return km."""
    legs = directions_json.get("routes", [{}])[0].get("legs", [])
    total_m = 0
    for i in leg_indices:
        if i < len(legs):
            total_m += legs[i].get("distance", {}).get("value", 0)
    return total_m / 1000.0

def get_two_loops_link_and_lengths(
    start: tuple[float, float],
    waypoints: list[tuple[float, float]]
) -> tuple[str, float, float, float]:
    """
    Calls Directions API for combined A+B loops and returns:
      (google_maps_url, loopA_km, loopB_km, total_km)
    Waypoints order:
      origin ->
        A_wp1 (leg0) -> A_wp2 (leg1) -> START (leg2) ->
        B_wp1 (leg3) -> B_wp2 (leg4) -> START (leg5 = destination)
    """
    wp_str = "|".join(f"{lat},{lng}" for lat, lng in waypoints)
    origin = f"{start[0]},{start[1]}"
    destination = origin
    
    # Call Directions API with both loops in one request
    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": origin,
        "destination": destination,
        "waypoints": wp_str,
        "mode": "walking",
        "key": GOOGLE_DIRECTIONS_KEY,
    }
    r = requests.get(url, params=params, timeout=25)
    r.raise_for_status()
    data = r.json()
    if data.get("status") != "OK":
        raise RuntimeError(f"Directions API error: {data.get('status')} - {data.get('error_message')}")

    # Legs 0-2 are loop A, 3-5 are loop B
    loopA_km = _sum_legs_km(data, [0, 1, 2])
    loopB_km = _sum_legs_km(data, [3, 4, 5])
    total_km = loopA_km + loopB_km

    # Construct a shareable Google Maps link
    maps_url = (
        "https://www.google.com/maps/dir/?api=1"
        f"&origin={origin}"
        f"&destination={destination}"
        f"&travelmode=walking"
        f"&waypoints={wp_str}"
    )
    return maps_url, loopA_km, loopB_km, total_km


# NOTE: If the remainder after full A+B cycles is less than a full loop
# but still > ~1 km, you might want to manually add a small extension
# (e.g., an extra 500m–1 km out-and-back) to hit the planned distance exactly