import re
import pandas as pd

def spare_transition_df(game_strings: list[str]) -> pd.DataFrame:
    """
    For each spare in each game, records:
      - first_throw: how many pins on the first ball
      - bonus:       pins scored on the next roll
    Returns a DataFrame one row per spare.
    """
    records = []
    for gs in game_strings:
        rolls = []
        # build rolls list again
        for ch in gs:
            if ch == 'X':
                rolls.append(10)
            elif ch == '/':
                rolls.append(10 - rolls[-1])
            elif ch in '-F':
                rolls.append(0)
            else:
                rolls.append(int(ch))
        # scan for spares in string
        for i, ch in enumerate(gs):
            if ch == '/':
                first = rolls[i-1]
                bonus = rolls[i+1] if i+1 < len(rolls) else None
                records.append({"first_throw": first, "bonus_throw": bonus})
    return pd.DataFrame(records)


def strike_transition_df(game_strings: list[str]) -> pd.DataFrame:
    """
    For each strike in each game, records:
      - bonus1: first bonus roll
      - bonus2: second bonus roll
    Returns a DataFrame one row per strike.
    """
    records = []
    for gs in game_strings:
        rolls = []
        for ch in gs:
            if ch == 'X':
                rolls.append(10)
            elif ch == '/':
                rolls.append(10 - rolls[-1])
            elif ch in '-F':
                rolls.append(0)
            else:
                rolls.append(int(ch))
        # scan for strikes
        idx = 0
        for i, ch in enumerate(gs):
            if ch == 'X':
                b1 = rolls[idx+1] if idx+1 < len(rolls) else None
                b2 = rolls[idx+2] if idx+2 < len(rolls) else None
                records.append({"bonus1": b1, "bonus2": b2})
                idx += 1
            else:
                idx += 1 if ch=='X' else 2  # skip two rolls for non-strike
    return pd.DataFrame(records)

import matplotlib.pyplot as plt
import numpy as np
from typing import List
def plot_spare_bonus_distribution(
    game_strings: List[str],
    max_pin: int = 10
) -> plt.Figure:
    """
    Histogram of pins knocked down on the roll immediately after each spare,
    with a dashed mean line.
    """
    # 1) extract numeric rolls
    bonuses = []
    for gs in game_strings:
        rolls = []
        for ch in gs:
            if ch == "X":
                rolls.append(10)
            elif ch == "/":
                rolls.append(10 - rolls[-1])
            elif ch in "-F":
                rolls.append(0)
            else:
                rolls.append(int(ch))
        # find each spare in the string
        for idx, ch in enumerate(gs):
            if ch == "/":
                # next roll lives at rolls[idx+1]
                if idx + 1 < len(rolls):
                    bonuses.append(rolls[idx + 1])

    # 2) build integer‐centered bins 0…max_pin
    edges = np.arange(-0.5, max_pin + 1.5, 1)
    fig, ax = plt.subplots()
    ax.hist(bonuses, bins=edges, edgecolor="black", rwidth=0.8)
    mean_b = np.mean(bonuses) if bonuses else 0
    ax.axvline(mean_b, linestyle="--", color="black", label=f"Mean = {mean_b:.2f}")
    ax.set_xticks(range(0, max_pin + 1))
    ax.set_title("Spare Bonus Distribution")
    ax.set_xlabel("Pins on Next Roll After Spare")
    ax.set_ylabel("Frequency")
    ax.legend()
    fig.tight_layout()
    return fig


def plot_strike_bonus_distributions(
    game_strings: List[str],
    max_pin: int = 10
) -> plt.Figure:
    """
    Three‐panel histogram for:
      1) bonus1: pins on next roll after a strike
      2) bonus2: pins on second‐next roll after a strike
      3) combined: bonus1 + bonus2
    """
    b1_list, b2_list = [], []

    # build flat rolls list & extract bonuses
    for gs in game_strings:
        rolls = []
        for ch in gs:
            if ch == "X":
                rolls.append(10)
            elif ch == "/":
                rolls.append(10 - rolls[-1])
            elif ch in "-F":
                rolls.append(0)
            else:
                rolls.append(int(ch))

        r = 0
        for ch in gs:
            if ch == "X":
                # next two rolls
                if r + 1 < len(rolls):
                    b1_list.append(rolls[r + 1])
                if r + 2 < len(rolls):
                    b2_list.append(rolls[r + 2])
                r += 1
            else:
                # non‐strike consumes two rolls
                r += 2

    combined = [x + y for x, y in zip(b1_list, b2_list)]

    # bins for single‐roll bonuses
    single_edges = np.arange(-0.5, max_pin + 1.5, 1)
    # bins for combined bonuses (max up to 20)
    max_comb = max(combined) if combined else 0
    combined_edges = np.arange(-0.5, max_comb + 1.5, 1)

    fig, axes = plt.subplots(1, 3, figsize=(15, 4), sharey=True)

    # Panel 1: next‐roll bonus
    axes[0].hist(b1_list, bins=single_edges, edgecolor="black", rwidth=0.8)
    m1 = np.mean(b1_list) if b1_list else 0
    axes[0].axvline(m1, linestyle="--", color="black", label=f"Mean={m1:.2f}")
    axes[0].set_title("Strike Bonus: Next Roll")
    axes[0].set_xticks(range(0, max_pin + 1))
    axes[0].set_xlabel("Pins")
    axes[0].legend()

    # Panel 2: second‐roll bonus
    axes[1].hist(b2_list, bins=single_edges, edgecolor="black", rwidth=0.8)
    m2 = np.mean(b2_list) if b2_list else 0
    axes[1].axvline(m2, linestyle="--", color="black", label=f"Mean={m2:.2f}")
    axes[1].set_title("Strike Bonus: 2nd Next Roll")
    axes[1].set_xticks(range(0, max_pin + 1))
    axes[1].set_xlabel("Pins")
    axes[1].legend()

    # Panel 3: combined two‐roll bonus
    axes[2].hist(combined, bins=combined_edges, edgecolor="black", rwidth=0.8)
    mc = np.mean(combined) if combined else 0
    axes[2].axvline(mc, linestyle="--", color="black", label=f"Mean={mc:.2f}")
    axes[2].set_title("Combined Bonus")
    axes[2].set_xticks(range(0, max_comb + 1))
    axes[2].set_xlabel("Pins")
    axes[2].legend()

    axes[0].set_ylabel("Frequency")
    fig.tight_layout()
    return fig
