import json
import math
from datetime import datetime
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt


RESULTS_FILE = Path(__file__).with_name("reaction_times.json")


def load_results() -> list[tuple[datetime, float]]:
    with RESULTS_FILE.open("r", encoding="utf-8") as results_file:
        data = json.load(results_file)

    if not isinstance(data, dict):
        raise ValueError("Expected a JSON object of timestamp-to-reaction-time entries.")

    results = []
    for timestamp, reaction_time in data.items():
        if not isinstance(timestamp, str):
            raise ValueError("Each test timestamp must be a string.")
        if (
            isinstance(reaction_time, bool)
            or not isinstance(reaction_time, (int, float))
            or not math.isfinite(reaction_time)
        ):
            raise ValueError(f"Reaction time for {timestamp!r} must be a finite number.")
        try:
            performed = datetime.fromisoformat(timestamp)
        except ValueError as error:
            raise ValueError(f"Invalid test timestamp: {timestamp!r}.") from error
        results.append((performed, float(reaction_time)))

    return sorted(results, key=lambda result: result[0].astimezone().timestamp())


def make_figures(results: list[tuple[datetime, float]]) -> tuple[plt.Figure, plt.Figure]:
    times = [performed for performed, _ in results]
    reaction_times = [value for _, value in results]

    reaction_figure, reaction_axis = plt.subplots(figsize=(10, 5.5))
    reaction_axis.plot(
        times, reaction_times, marker="o", linewidth=2, color="#2d8052"
    )
    reaction_axis.set_title("Reaction Time History")
    reaction_axis.set_xlabel("Time of test")
    reaction_axis.set_ylabel("Reaction time (microseconds)")
    reaction_axis.grid(True, color="#ddd8cf", alpha=0.8)
    reaction_axis.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H:%M"))
    reaction_figure.autofmt_xdate()
    reaction_figure.tight_layout()

    change_figure, change_axis = plt.subplots(figsize=(10, 5.5))
    change_axis.set_title("Reaction Time Change from First Test")
    change_axis.set_xlabel("Time of test")
    change_axis.set_ylabel("Change from first test (%)")
    change_axis.axhline(0, color="#77716a", linewidth=1)
    change_axis.grid(True, color="#ddd8cf", alpha=0.8)
    change_axis.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H:%M"))

    baseline = reaction_times[0]
    if baseline == 0:
        change_axis.text(
            0.5, 0.5,
            "Percent change is undefined because the first reaction time is zero.",
            ha="center", va="center", transform=change_axis.transAxes,
        )
    else:
        percent_changes = [
            (value - baseline) / baseline * 100 for value in reaction_times
        ]
        change_axis.plot(
            times, percent_changes, marker="o", linewidth=2, color="#a05a38"
        )

    change_figure.autofmt_xdate()
    change_figure.tight_layout()
    return reaction_figure, change_figure


if __name__ == "__main__":
    try:
        results = load_results()
        if not results:
            raise ValueError("No reaction-time results have been recorded yet.")
    except (OSError, json.JSONDecodeError, ValueError) as error:
        raise SystemExit(f"Unable to display results: {error}") from error

    make_figures(results)
    plt.show()
