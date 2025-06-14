import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from scipy import stats

def plot_time_series(df: pd.DataFrame) -> plt.Figure:
    fig, ax = plt.subplots()
    df.plot(marker="o", ax=ax)
    ax.set_ylabel("Value")
    return fig

def plot_hist_with_normal(y) -> tuple[plt.Figure, float, float]:
    mu, sigma = y.mean(), y.std()
    fig, ax1 = plt.subplots()
    counts, bins, _ = ax1.hist(y, bins=20, alpha=0.7, color="skyblue", edgecolor="black")
    ax1.set(title="Histogram with Normal Fit", xlabel="Total Score", ylabel="Frequency")
    ax2 = ax1.twinx()
    ax2.plot(
        bins,
        stats.norm.pdf(bins, mu, sigma),
        'k--',
        label=f"N({mu:.1f}, {sigma:.2f}²)"
    )
    ax2.set_ylabel("Density")
    ax2.legend(loc="upper right")
    return fig, mu, sigma

def plot_kde(y) -> plt.Figure:
    fig, ax = plt.subplots()
    sns.kdeplot(y, fill=True, ax=ax)
    return fig

def plot_residuals(x, y, label: str, color: str) -> plt.Figure:
    coeffs = np.polyfit(x, y, 1)
    line = np.poly1d(coeffs)
    fig, ax = plt.subplots()
    ax.scatter(x, y, alpha=0.6, color=color)
    ax.plot(np.sort(x), line(np.sort(x)), 'k--')
    ax.set(title=f"Total vs {label}", xlabel=label, ylabel="Total")
    return fig