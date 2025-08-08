from planner.training_plan import get_next_planned_run
from planner.past_runs import fetch_recent_runs
from planner.pace_estimator import estimate_run_duration
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

    # 6. Fetch weather forecast

    # 7. Choose best time to run

    # 8. Create Google Calendar entry with buffer


if __name__ == "__main__":
    main()