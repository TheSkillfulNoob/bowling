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
    game_strings: List[str], max_pin: int = 10
) -> plt.Figure:
    # 1) get a DataFrame with one row per spare
    df = spare_transition_df(game_strings)
    bonuses = df["bonus_throw"].fillna(0).astype(int)

    # 2) bins 0…10 centered
    edges = np.arange(-0.5, max_pin + 1.5, 1)
    fig, ax = plt.subplots()
    ax.hist(bonuses, bins=edges, edgecolor="black", rwidth=0.8, align="left")
    mean_b = bonuses.mean() if not bonuses.empty else 0
    ax.axvline(mean_b, linestyle="--", color="black", label=f"Mean={mean_b:.2f}")
    ax.set_xticks(range(0, max_pin + 1))
    ax.set_title("Spare Bonus Distribution")
    ax.set_xlabel("Pins on Next Roll After Spare")
    ax.set_ylabel("Frequency")
    ax.legend()
    fig.tight_layout()
    return fig


def plot_strike_bonus_distributions(
    game_strings: List[str], max_pin: int = 10
) -> plt.Figure:
    # 1) get a DataFrame with one row per strike
    df = strike_transition_df(game_strings)
    b1 = df["bonus1"].fillna(0).astype(int)
    b2 = df["bonus2"].fillna(0).astype(int)
    combined = b1 + b2

    # 2) build bins
    single_edges   = np.arange(-0.5, max_pin + 1.5, 1)
    max_comb       = combined.max() if not combined.empty else 0
    combined_edges = np.arange(-0.5, max_comb + 1.5, 1)

    fig, axes = plt.subplots(1, 3, figsize=(15, 4), sharey=True)

    for ax, data, title, edges in zip(
        axes,
        [b1, b2, combined],
        ["Strike Bonus: Next Roll",
         "Strike Bonus: 2nd Next Roll",
         "Combined Bonus"],
        [single_edges, single_edges, combined_edges],
    ):
        ax.hist(data, bins=edges, edgecolor="black", rwidth=0.8, align="left")
        m = data.mean() if len(data)>0 else 0
        ax.axvline(m, linestyle="--", color="black", label=f"Mean={m:.2f}")
        ax.set_title(title)
        ax.set_xticks(range(0, int(edges.max())))
        ax.set_xlabel("Pins")
        ax.legend()

    axes[0].set_ylabel("Frequency")
    fig.tight_layout()
    return fig
