import sys

sys.path.append(".")
from src.services.consistency.validator import ConsistencyValidator

cv = ConsistencyValidator()

# Debug the timestamp comparison
timestamp1 = "day_1_morning"
timestamp2 = "day_1_afternoon"

print(f"Comparing: {timestamp1} vs {timestamp2}")

if "_" in timestamp1 and "_" in timestamp2:
    day1, time1 = timestamp1.split("_", 1)
    day2, time2 = timestamp2.split("_", 1)
    print(f"Day1: {day1}, Time1: {time1}")
    print(f"Day2: {day2}, Time2: {time2}")

    import re

    day1_num = int(re.search(r"\d+", day1).group()) if re.search(r"\d+", day1) else 0
    day2_num = int(re.search(r"\d+", day2).group()) if re.search(r"\d+", day2) else 0
    print(f"Day1_num: {day1_num}, Day2_num: {day2_num}")

    time_order = {"morning": 1, "afternoon": 2, "evening": 3, "night": 4}
    time1_val = time_order.get(time1.lower(), 2)
    time2_val = time_order.get(time2.lower(), 2)
    print(f"Time1_val: {time1_val}, Time2_val: {time2_val}")

    result = -1 if time1_val < time2_val else (1 if time1_val > time2_val else 0)
    print(f"Result: {result}")

# Test the actual function
actual_result = cv._compare_timestamps(timestamp1, timestamp2)
print(f"Actual function result: {actual_result}")
