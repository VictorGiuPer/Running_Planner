from planner.training_plan import get_next_planned_run
from planner.past_runs import fetch_recent_runs
from planner.pace_estimator import get_estimated_performance
from planner.route_generator import generate_and_print_loops_plan, geocode_address
from planner.weather_checker import fetch_hourly_forecast, extract_day_forecast

from datetime import datetime, date


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
    get_estimated_performance(run["distance_km"], past_runs)

    # 5. Generate a route for the planned distance
    start_address = input("Start address: ").strip()
    start_latlng = geocode_address(start_address)

    generate_and_print_loops_plan(start_latlng, run["distance_km"])

    # 6. Fetch weather forecast
    weather_data = fetch_hourly_forecast(start_latlng[0], start_latlng[1])

    if isinstance(run["date"], date):
        run_date = run["date"]
    else:
        run_date = datetime.strptime(run["date"], "%Y-%m-%d").date()
    day_forecast = extract_day_forecast(weather_data, run_date)

    print(f"\n=== Weather Forecast | {run_date} ===")
    for slot in day_forecast:
        print(f"{slot['time']} - {slot['temp']}°C (feels {slot['feels_like']}°C), "
            f"Wind {slot['wind']} m/s, Rain {slot['rain_prob']:.0f}%")
    
    # 7. Get Google Calendar and Constraints

    # 8. Ask Gemini To Plan the best time for my run

    # 9. Create Google Calendar entry with buffer


if __name__ == "__main__":
    main()


"""
Yes — that’s exactly where this starts tipping into *agentic AI* territory.

Right now your planner is **reactive** — you give it the run distance and date, and it spits out loops + weather.
If you let an LLM **decide the best run start time** based on your weather forecast, your calendar, and maybe personal constraints (e.g., no running before coffee), you’ve turned it into an **autonomous decision-maker** for part of your plan.

Concretely, you could:

1. **Fetch hourly forecast** for the run day.
2. **Pull constraints** (e.g., "only between 6:00 and 20:00", “avoid >25°C”, “rain prob <30%”, "I prefer mornings").
3. **Feed all that into the LLM** with instructions like:

   > “Pick the best 1–2 hour window for my run that minimizes wind, temperature extremes, and rain probability.”
4. **Have it return** the start time, confidence, and a short reasoning (so you understand the trade-offs it made).
5. **Optionally**: automatically add the event to Google Calendar.

At that point your LLM isn’t just generating text — it’s interpreting data, weighing trade-offs, and making a choice, which is exactly what agentic AI is about.

If you want, I can help you design that **"weather → reasoning → time suggestion"** prompt and the code glue so your planner just… decides.
"""