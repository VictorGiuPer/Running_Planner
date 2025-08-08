from planner.training_plan import get_next_planned_run
from planner.past_runs import fetch_recent_runs
from planner.pace_estimator import estimate_run_duration
from planner.route_generator import (geocode_address,
                                     build_two_calibrated_loops,
                                     get_two_loops_link_and_lengths)
from utils import round_up_minutes, format_pace

def main():
    # 1. Load environment variables & config

    # 2. Read next planned run from Google Sheets
    run = get_next_planned_run()

    if not run:
        print("No upcoming run found in Google Sheets.")
        return

    print("=== Next Planned Run ===")
    print(f"Date     : {run['date']}")
    print(f"Distance : {run['distance_km']} km")
    print(f"Week     : {run['week']}")


    # 3. Fetch past run data from Strava
    print("\n=== Recent Runs (Strava) ===")
    past_runs = fetch_recent_runs(10)
    for r in past_runs:
        print(f"{r['name']:<40} {r['distance_km']:>5.2f} km  "
              f"{r['average_speed_kmh']:>4.1f} km/h  {r['pace_str']}")        
        pass

    # 4. Estimate pace and run duration
    est_minutes = estimate_run_duration(run["distance_km"], past_runs)
    total_block = round_up_minutes(est_minutes + 30)  # +30 min buffer
    pace_min_per_km = est_minutes / run["distance_km"]

    print("\n=== Estimated Performance ===")
    print(f"Estimated pace       : {format_pace(pace_min_per_km)} min/km")
    print(f"Estimated run time   : {est_minutes:.0f} min")
    print(f"Calendar block (+30) : {total_block} min")

    # 5. Generate a route for the planned distance
    planned_km = run["distance_km"]      # e.g., 24
    target_loop_km = 6.2                 # ~6–7 km is your preference

    start_address = input("Start address: ").strip()
    bearing = float(input("Initial direction (deg, 0=N, 90=E, 180=S, 270=W): "))

    start_latlng = geocode_address(start_address)

    waypoints, loopA_km, loopB_km = build_two_calibrated_loops(
        start_lat=start_latlng[0],
        start_lng=start_latlng[1],
        target_loop_km=target_loop_km,
        initial_bearing_deg=bearing,
    )

    link, a_km, b_km, total_ab_km = get_two_loops_link_and_lengths(start=start_latlng, waypoints=waypoints)

    cycle_km = a_km + b_km
    full_cycles = int(planned_km // cycle_km)
    remainder = planned_km - full_cycles * cycle_km

    print("\n=== Loops (calibrated) ===")
    print(f"Loop A: {a_km:.2f} km")
    print(f"Loop B: {b_km:.2f} km")
    print(f"A+B   : {cycle_km:.2f} km")

    print("\n=== Suggested plan ===")
    if full_cycles > 0:
        print(f"Run {full_cycles}×: A → B")
    if remainder > 0.4:
        extra = 'A' if abs(remainder - a_km) < abs(remainder - b_km) else 'B'
        print(f"Then add one extra loop: {extra}")
    else:
        print("No extra loop needed; you’ll be very close to plan.")

    print("\nGoogle Maps route (A then B):")
    print(link)
    # 6. Fetch weather forecast

    # 7. Choose best time to run

    # 8. Create Google Calendar entry with buffer


if __name__ == "__main__":
    main()