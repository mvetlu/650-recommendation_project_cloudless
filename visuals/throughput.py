import matplotlib.pyplot as plt

# -----------------------------
# Data
# -----------------------------

# Cloud version (from your table)
users_cloud = [5, 10, 15, 25]
throughput_cloud = [36, 62, 100, 170]  # req/s

# No-cloud version: fixed ~100 req/s then crashes
users_nocloud = [5, 10, 15, 25]
throughput_nocloud = [100, 100, 100, 0]   # flat then crash

# -----------------------------
# Figure
# -----------------------------
plt.figure(figsize=(9, 4.5), dpi=150)
ax = plt.gca()

# --- backgrounds ---
ax.set_facecolor("black")
ax.figure.set_facecolor("black")

# Throughput lines (colors per your theme)
ax.plot(
    users_cloud,
    throughput_cloud,
    marker="o",
    linewidth=2,
    color="#F4C542",               # golden yellow
    label="Cloud (scales with users)",
)
ax.plot(
    users_nocloud,
    throughput_nocloud,
    marker="s",
    linestyle="--",
    linewidth=2,
    color="red",                   # true red
    label="Non-cloud (fixed, then crash)",
)

# Axes, title
ax.set_xlabel("Concurrent Users", fontsize=12, color="white")
ax.set_ylabel("Throughput (req / sec)", fontsize=12, color="white")
ax.set_title("Scalability: Cloud vs Non-cloud", fontsize=14, color="white")
ax.set_ylim(bottom=0)

# Grid + ticks + spines in white-ish
ax.grid(axis="y", alpha=0.3, color="white")
ax.tick_params(colors="white")
for spine in ax.spines.values():
    spine.set_color("white")

# Legend styling
legend = ax.legend(loc="upper left", facecolor="black", edgecolor="white")
for text in legend.get_texts():
    text.set_color("white")
"""
# Optional caption under the plot
ax.text(
    0.5, -0.25,
    "Key insight: Cloud limit is a config setting, not a hardware constraint.",
    transform=ax.transAxes,
    ha="center",
    va="top",
    fontsize=10,
    color="white",
)
"""
plt.tight_layout()
plt.savefig("scalability_comparison_clean.png", facecolor="black")
plt.close()

print("Saved figure as scalability_comparison_clean.png")