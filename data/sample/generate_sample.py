"""Generate a realistic 4-week flight schedule for model training."""
import pandas as pd
import numpy as np
from pathlib import Path

np.random.seed(42)

airlines = ["AA", "UA", "DL", "LH", "BA", "AF", "TK", "EK", "QR", "FR"]

# typical departure schedule template (hour, base_pax)
schedule_template = [
    (5, 120), (5, 140),
    (6, 200), (6, 220), (6, 180),
    (7, 240), (7, 280), (7, 260), (7, 300),
    (8, 320), (8, 290), (8, 180),
    (9, 160), (9, 150),
    (10, 130), (10, 120),
    (11, 140), (11, 135),
    (12, 160), (12, 155),
    (13, 150), (13, 145),
    (14, 170), (14, 165),
    (15, 180), (15, 175),
    (16, 210), (16, 200),
    (17, 290), (17, 270), (17, 310),
    (18, 330), (18, 300), (18, 280),
    (19, 250), (19, 220),
    (20, 190), (20, 170),
    (21, 150), (21, 130),
    (22, 120),
]

# day-of-week multipliers (Mon=0 ... Sun=6)
dow_multiplier = {0: 1.1, 1: 0.95, 2: 0.9, 3: 1.0, 4: 1.2, 5: 1.3, 6: 1.15}

rows = []
flight_counter = 1
base_date = pd.Timestamp("2026-05-01")

for day_offset in range(35):  # 5 weeks
    date = base_date + pd.Timedelta(days=day_offset)
    dow = date.dayofweek
    mult = dow_multiplier[dow]

    for hour, base_pax in schedule_template:
        minute = np.random.choice([0, 15, 30, 45])
        scheduled_time = date.replace(hour=hour, minute=minute, second=0)

        pax = int(base_pax * mult * np.random.uniform(0.85, 1.15))
        delay = int(np.random.choice([0, 0, 0, 5, 10, 15, 20, 30, 45],
                                      p=[0.5, 0.1, 0.1, 0.1, 0.07, 0.05, 0.04, 0.02, 0.02]))
        airline = np.random.choice(airlines)
        flight_num = f"{airline}{flight_counter:03d}"
        desks = max(2, pax // 80)

        rows.append({
            "flight_id": flight_num,
            "scheduled_time": scheduled_time,
            "pax_count": pax,
            "delay_min": delay,
            "checkin_desks": desks,
        })
        flight_counter += 1

df = pd.DataFrame(rows)
out = Path(__file__).parent / "training_flights.csv"
df.to_csv(out, index=False)
print(f"Generated {len(df)} flights across {day_offset+1} days → {out}")
print(df.describe())
