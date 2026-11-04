"""What Pulsus shows: one Metric per card and detail page, with how its
daily value is made and how it is drawn (docs/visualisation.md). No GTK."""
from dataclasses import dataclass

from pulsus import text

# Kept in the order of the Today page.


@dataclass(frozen=True)
class Metric:
    id: str
    title: str
    icon: str
    unit: str
    # The table that must exist for the metric to be shown.
    table: str
    # Store method name: daily values as {date: number}.
    daily: str
    # "bars" for amounts that add up (steps, sleep), "dots" for levels
    # (heart rate, stress) with a 7-day average line.
    style: str
    # For the trend sentence: "steps", "resting heart rate".
    what: str
    # How the daily value is made, shown under the chart.
    explanation: str
    digits: int = 0
    # Band of the user's normal range (levels only).
    baseline: bool = False
    # A readings table for the day view: hrv, spo2, stress, temperature.
    readings: str = ""
    readings_where: str = ""

    def format(self, value):
        if hasattr(value, "total_seconds"):
            return text.duration(value)
        if self.id == "sleep":
            return text.duration_hours(value)
        return text.number(value, self.digits)

    def value(self, raw):
        """A daily value as a plain number for charts and statistics."""
        if hasattr(raw, "total_seconds"):
            return text.hours(raw)
        if isinstance(raw, tuple):          # PAI: (today, last 7 days)
            return raw[1]
        return float(raw)


METRICS = (
    Metric("steps", "Steps", "pulsus-steps-symbolic", "steps",
           "mi_band_activity", "daily_steps", "bars", "steps",
           "All steps of the day, counted by the watch minute by minute."),
    Metric("heart-rate", "Resting Heart Rate", "pulsus-heart-symbolic", "bpm",
           "mi_band_activity", "daily_resting_heart_rate", "dots",
           "resting heart rate",
           "Estimated from the watch's readings: the average of the day's "
           "30 lowest one-minute values. The watch's own resting heart rate "
           "is not stored by Amazfish.", baseline=True),
    Metric("sleep", "Sleep", "pulsus-sleep-symbolic", "h",
           "mi_band_activity", "daily_sleep", "bars", "sleep",
           "Time asleep in the night's main sleep, from the minutes the watch "
           "marked as asleep. Amazfish does not store sleep stages for this "
           "watch, so Pulsus shows asleep and awake only.", digits=1),
    Metric("stress", "Stress", "pulsus-stress-symbolic", "",
           "stress", "daily_stress", "dots", "stress",
           "Average of the watch's automatic stress readings (0–100).",
           baseline=True, readings="stress", readings_where="AND stress_type = 1"),
    Metric("hrv", "Heart Rate Variability", "pulsus-hrv-symbolic", "ms",
           "hrv", "daily_hrv", "dots", "HRV",
           "Average of the watch's HRV readings, usually taken at night. "
           "Compare it only with your own values.",
           baseline=True, readings="hrv"),
    Metric("spo2", "Blood Oxygen", "pulsus-oxygen-symbolic", "%",
           "spo2", "daily_spo2", "dots", "blood oxygen",
           "Average of the watch's SpO₂ readings. A wrist watch is not a "
           "medical device.", readings="spo2"),
    Metric("temperature", "Skin Temperature", "pulsus-temperature-symbolic", "°C",
           "temperature", "daily_temperature", "dots", "skin temperature",
           "Average of the watch's skin temperature readings.", digits=1,
           baseline=True, readings="temperature"),
    Metric("pai", "PAI", "pulsus-pai-symbolic", "",
           "pai", "daily_pai", "bars", "PAI",
           "Personal Activity Intelligence as the watch computes it: the "
           "points of the last 7 days. The watch suggests keeping it at 100 "
           "or above."),
)

BY_ID = {m.id: m for m in METRICS}
