# planner/pace_estimator.py
from statistics import median

def _min_per_km(distance_km, moving_time_min):
    """
    Helper: Calculate pace in minutes per km.
    Returns None if distance is zero or negative.
    """
    if distance_km <= 0:
        return None
    return moving_time_min / distance_km

def _clean(values):
    """
    Helper: Filter pace values to a 'sane' range (3–10 min/km).
    This removes bad GPS data or walking activities.
    """
    vals = [v for v in values if v is not None and 3.0 <= v <= 10.0]  # 3–10 min/km sane band
    return vals

def estimate_run_duration(distance_km, past_runs, window_ratio=0.3):
    """
    Estimate minutes for a planned distance using recent runs.
    Strategy:
      1) Find runs with distance within ±30% of target (configurable).
      2) Use the median pace (min/km) of those; else fallback to median of all.
    Returns: estimated minutes (float)
    """
    target = distance_km
    lo, hi = target * (1 - window_ratio), target * (1 + window_ratio)

    similar_paces = [] # Paces from runs close in distance to the target
    all_paces = [] # Paces from all past runs

    for r in past_runs:
        d = float(r.get("distance_km", 0))
        tmin = float(r.get("moving_time_min", 0))
        pace = _min_per_km(d, tmin)
        if pace is None: 
            continue
        all_paces.append(pace)
        if lo <= d <= hi: # If run distance is within the similarity window
            similar_paces.append(pace)

    # Choose pace pool: prefer similar distances, else use all runs
    pool = _clean(similar_paces) or _clean(all_paces)
    if not pool:
        # super fallback: 6:00 / km
        est_pace = 6.0
    else:
        est_pace = median(pool)

    return est_pace * distance_km  # minutes
