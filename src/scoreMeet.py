# %%
import sys
from collections import defaultdict
from scipy.interpolate import interp1d
import numpy as np

# Add custom parser path and import
sys.path.insert(0, "../hytek-parser")
from hytek_parser import hy3_parser
from hytek_parser.hy3.enums import Course, Stroke, Gender

# File path and parsing
file_path = "../SampleMeetResults/Meet Results-PCS Spring Home Meet 2025-22Mar2025-002.hy3"
parsed_file = hy3_parser.parse_hy3(file_path)
events = parsed_file.meet.events
event_ids = list(events.keys())

# %%
def get_event_code(event):
    stroke_code = {
        Stroke.FREESTYLE: "1" if not event.relay else "6",
        Stroke.BACKSTROKE: "2",
        Stroke.BREASTSTROKE: "3",
        Stroke.BUTTERFLY: "4",
        Stroke.MEDLEY: "5" if not event.relay else "7"
    }.get(event.stroke, "")

    course_code = {
        Course.SCY: "Y",
        Course.LCM: "L",
        Course.SCM: "S"
    }.get(event.course, "")

    return f"{stroke_code}{event.distance}{course_code}" if stroke_code and course_code else None

# %%
def get_event_name(event):
    gender_str = {
        Gender.MALE: "Men's",
        Gender.FEMALE: "Women's",
        Gender.UNKNOWN: "Mixed"
    }.get(event.gender, "Unknown")

    stroke_str = {
        Stroke.FREESTYLE: "Freestyle",
        Stroke.BACKSTROKE: "Backstroke",
        Stroke.BREASTSTROKE: "Breaststroke",
        Stroke.BUTTERFLY: "Butterfly",
        Stroke.MEDLEY: "Medley"
    }.get(event.stroke, "Unknown")

    return f"{gender_str} {event.distance} {stroke_str} ({event.course.name})"

# %%
# Extract and organize event results
results = defaultdict(list)

for event_id in event_ids:
    event = events[event_id]
    event_name = get_event_name(event)

    for entry in event.entries:
        swimmer = entry.swimmers[0]
        swimmer_name = f"{swimmer.first_name} {swimmer.middle_initial + ' ' if swimmer.middle_initial else ''}{swimmer.last_name}"
        
        result_entry = {
            "swimmer": swimmer_name,
            "age": swimmer.age,
            "prelim_time": entry.prelim_time,
            "swimoff_time": entry.swimoff_time,
            "final_time": entry.finals_time
        }
        results[event_name].append(result_entry)

    # Sort by final time, ignoring missing or zero times
    results[event_name] = sorted(
        results[event_name],
        key=lambda x: float('inf') if not x['final_time'] or x['final_time'] == 0.0 else x['final_time']
    )

# %%
# Example points table
pointSystem15plus = {
    "Men's 100 Freestyle (SCY)": {
        41.23: 1000, 43.56: 950, 45.89: 900, 46.99: 850, 48.09: 800,
        49.19: 750, 50.29: 700, 51.34: 650, 52.49: 600, 53.56: 550,
        54.64: 500, 55.71: 450, 56.79: 400, 57.89: 350, 58.99: 300,
        60.09: 250, 61.19: 200, 62.19: 150, 63.19: 100
    },
    "Women's 100 Freestyle (SCY)": {
        46.09: 1000, 48.69: 950, 51.29: 900, 52.49: 850, 53.69: 800,
        54.89: 750, 56.09: 700, 57.34: 650, 58.59: 600, 59.81: 550,
        61.04: 500, 62.36: 450, 63.49: 400, 64.69: 350, 65.89: 300,
        67.09: 250, 68.29: 200, 69.29: 150, 70.29: 100
    }
}

# %%
def get_interpolated_score(event_name: str, gender: str, time_seconds: float, points_dict: dict) -> float:
    if time_seconds <= 0:
        return 0.0
    
    key = f"{gender}'s {event_name}"
    if key not in points_dict:
        raise ValueError(f"No data found for event '{key}'")
    
    time_points = sorted(points_dict[key].items())
    times = [t for t, _ in time_points]
    scores = [s for _, s in time_points]

    f = interp1d(times, scores, bounds_error=False, fill_value="extrapolate")
    score = float(f(time_seconds))
    return max(score, 0.0)

# %%
# Apply scoring for specific events
def print_scores(event_key: str, gender: str):
    for swimmer in results.get(event_key, []):
        swimmer_name = swimmer["swimmer"]
        swimmer_time = swimmer["final_time"]

        if swimmer_time and swimmer_time > 0.0:
            total_seconds = swimmer_time  # Assuming already in seconds
            score = get_interpolated_score("100 Freestyle (SCY)", gender, total_seconds, pointSystem15plus)
            print(f"Swimmer: {swimmer_name}, Time: {swimmer_time}, Score: {score}")

print_scores("Women's 100 Freestyle (SCY)", "Women")
print_scores("Men's 100 Freestyle (SCY)", "Men")
