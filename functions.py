import json
import pandas as pd
def format_open_hours(open_hours_str):
    if pd.isna(open_hours_str):
        return ""
    open_hours = json.loads(open_hours_str)
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    formatted_hours = []
    if open_hours:
        formatted_hours.append("Open hours:")
    for day in days:
        hours = open_hours.get(day, [])
        if hours:
            formatted_hours.append(f"  {day}: {hours[0][0]} - {hours[0][1]}")
        else:
            formatted_hours.append(f"  {day}: Closed")
    return " \n • ".join(formatted_hours)