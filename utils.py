def round_up_minutes(mins, base=15):
    # e.g., 66 -> 75
    return int(base * ((mins + base - 1) // base))

def format_pace(min_per_km):
    """Convert pace (in minutes/km as float) to mm:ss string."""
    minutes = int(min_per_km)
    seconds = int(round((min_per_km - minutes) * 60))
    return f"{minutes}:{seconds:02d} min/km"