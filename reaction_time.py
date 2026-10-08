import json
import random
import time
import tkinter as tk
from datetime import datetime, timezone
from pathlib import Path
from tkinter import messagebox


TRIAL_COUNT = 5
RESULTS_FILE = Path(__file__).with_name("reaction_times.json")


class ReactionTimeApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Coffee Reaction Time")
        self.root.resizable(False, False)
        self.root.configure(bg="#f4f1eb")

        self.state = "idle"
        self.trial = 0
        self.reaction_times: list[int] = []
        self.green_started_ns = 0
        self.pending_timer: str | None = None
        self.square_id: int | None = None
        self.message_id: int | None = None

        self.canvas = tk.Canvas(
            root, width=480, height=420, bg="#f4f1eb", highlightthickness=0
        )
        self.canvas.pack(padx=24, pady=(20, 8))
        self.root.bind("<Button-1>", self.start_test)
        self.root.bind("<space>", self.handle_space)

        self.draw_idle()
        self.root.focus_set()

    def draw_idle(self) -> None:
        self.canvas.delete("all")
        self.canvas.create_text(
            240, 100, text="REACTION TIME", fill="#292724",
            font=("Segoe UI", 22, "bold"),
        )
        self.canvas.create_text(
            240, 170, text="Left-click anywhere to start",
            fill="#514d47", font=("Segoe UI", 15),
        )
        self.canvas.create_text(
            240, 215, text="Wait for green, then press SPACE",
            fill="#77716a", font=("Segoe UI", 12),
        )
        self.canvas.create_text(
            240, 250, text="5 trials per test",
            fill="#77716a", font=("Segoe UI", 12),
        )

    def start_test(self, _event: tk.Event | None = None) -> None:
        if self.state not in ("idle", "complete"):
            return
        self.trial = 1
        self.reaction_times = []
        self.begin_trial()

    def begin_trial(self, message: str | None = None) -> None:
        self.state = "waiting"
        self.canvas.delete("all")
        self.canvas.create_text(
            240, 55, text=f"TRIAL {self.trial} / {TRIAL_COUNT}",
            fill="#514d47", font=("Segoe UI", 13, "bold"),
        )
        self.square_id = self.canvas.create_rectangle(
            150, 100, 330, 280, fill="#df4237", outline=""
        )
        self.message_id = self.canvas.create_text(
            240, 330, text=message or "Wait for green...",
            fill="#514d47", font=("Segoe UI", 13),
        )
        delay_ms = random.randint(1500, 4000)
        self.pending_timer = self.root.after(delay_ms, self.show_green)

    def show_green(self) -> None:
        self.pending_timer = None
        if self.state != "waiting":
            return
        self.state = "ready"
        self.canvas.itemconfigure(self.square_id, fill="#2d9d62")
        self.canvas.itemconfigure(self.message_id, text="PRESS SPACE NOW")
        self.root.update_idletasks()
        self.green_started_ms = time.perf_counter_ns()/1000

    def handle_space(self, _event: tk.Event | None = None) -> str:
        if self.state == "waiting":
            if self.pending_timer is not None:
                self.root.after_cancel(self.pending_timer)
                self.pending_timer = None
            self.begin_trial("Too soon! Wait for green...")
        elif self.state == "ready":
            self.reaction_times.append(time.perf_counter_ns()/1000 - self.green_started_ms)
            if len(self.reaction_times) < TRIAL_COUNT:
                self.trial += 1
                self.begin_trial("Good! Get ready for the next one...")
            else:
                self.finish_test()
        return "break"

    def finish_test(self) -> None:
        average_ns = sum(self.reaction_times) / TRIAL_COUNT
        average_ns = float(f"{average_ns:.6g}")
        performed = datetime.now(timezone.utc).astimezone().isoformat(
            timespec="microseconds"
        )
        try:
            history = self.load_history()
            history[performed] = average_ns
            self.save_history(history)
        except (OSError, json.JSONDecodeError, ValueError) as error:
            messagebox.showerror(
                "Could not save results",
                f"The test is complete, but its result could not be saved:\n{error}",
                parent=self.root,
            )
            self.state = "complete"
            self.show_result(average_ns, saved=False)
            return

        self.state = "complete"
        self.show_result(average_ns, saved=True)

    @staticmethod
    def load_history() -> dict[str, int | float]:
        if not RESULTS_FILE.exists():
            return {}
        with RESULTS_FILE.open("r", encoding="utf-8") as results_file:
            history = json.load(results_file)
        if not isinstance(history, dict) or any(
            not isinstance(key, str)
            or isinstance(value, bool)
            or not isinstance(value, (int, float))
            for key, value in history.items()
        ):
            raise ValueError("The results file must contain timestamp-to-number entries.")
        return history

    @staticmethod
    def save_history(history: dict[str, int | float]) -> None:
        with RESULTS_FILE.open("w", encoding="utf-8") as results_file:
            json.dump(history, results_file, indent=2)
            results_file.write("\n")

    def show_result(self, average_micros: float, saved: bool) -> None:
        self.canvas.delete("all")
        self.canvas.create_text(
            240, 95, text="TEST COMPLETE", fill="#292724",
            font=("Segoe UI", 22, "bold"),
        )
        self.canvas.create_text(
            240, 160, text=f"Average: {average_micros:.6g} microseconds",
            fill="#2d8052", font=("Segoe UI", 18, "bold"),
        )
        self.canvas.create_text(
            240, 205, text=f"{TRIAL_COUNT} trials",
            fill="#514d47", font=("Segoe UI", 13),
        )
        self.canvas.create_text(
            240, 250,
            text="Saved to reaction_times.json" if saved else "Result was not saved",
            fill="#77716a", font=("Segoe UI", 12),
        )
        self.canvas.create_text(
            240, 300, text="Left-click to run another test",
            fill="#514d47", font=("Segoe UI", 13),
        )


if __name__ == "__main__":
    window = tk.Tk()
    ReactionTimeApp(window)
    window.mainloop()
