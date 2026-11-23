from __future__ import annotations

import numpy as np
from matplotlib.figure import Figure

from models import BeamModel, CalculationResults, SupportType


PURPLE = "#7654a7"
PURPLE_DARK = "#503779"
INK = "#17151a"
GRID = "#eee6ef"
MUTED = "#68616d"


def create_figure() -> Figure:
    figure = Figure(figsize=(8, 8), dpi=100, facecolor="#fffafd")
    figure.subplots_adjust(left=0.08, right=0.98, top=0.96, bottom=0.06, hspace=0.65)
    figure.add_subplot(4, 1, 1)
    figure.add_subplot(4, 1, 2)
    figure.add_subplot(4, 1, 3)
    figure.add_subplot(4, 1, 4)
    return figure


def _style_axis(axis, title: str, ylabel: str) -> None:
    axis.set_facecolor("#fffafd")
    axis.set_title(title, loc="left", fontsize=10, fontweight="bold", color=INK)
    axis.set_ylabel(ylabel, color=MUTED, fontsize=8)
    axis.grid(True, color=GRID, linewidth=0.8)
    axis.tick_params(labelsize=8, colors=MUTED)
    for spine in axis.spines.values():
        spine.set_color("#dccfe1")


def render(figure: Figure, model: BeamModel, results: CalculationResults) -> None:
    axes = figure.axes
    for axis in axes:
        axis.clear()

    beam_axis, shear_axis, moment_axis, deflection_axis = axes
    for axis, title, ylabel in (
        (shear_axis, "Shear diagram", "kip"),
        (moment_axis, "Moment diagram", "kip-ft"),
        (deflection_axis, "Deflection diagram", "in"),
    ):
        _style_axis(axis, title, ylabel)

    beam_axis.set_facecolor("#fffafd")
    beam_axis.set_xlim(0, model.span)
    beam_axis.set_ylim(-1.5, 1.8)
    beam_axis.set_yticks([])
    beam_axis.set_xticks(np.linspace(0, model.span, 11))
    beam_axis.tick_params(axis="x", labelsize=8, colors=MUTED)
    beam_axis.set_title("Beam and loading", loc="left", fontsize=10, fontweight="bold", color=INK)
    for spine in beam_axis.spines.values():
        spine.set_visible(False)

    beam_axis.plot([0, model.span], [0, 0], color=INK, linewidth=4, solid_capstyle="butt")
    if model.support_type is SupportType.CANTILEVER:
        beam_axis.plot([0, 0], [-0.65, 0.65], color=INK, linewidth=8)
        for y in np.linspace(-0.65, 0.65, 7):
            beam_axis.plot([-0.15, 0], [y - 0.1, y + 0.1], color=INK, linewidth=1)
    else:
        beam_axis.plot(0, -0.3, marker="^", markersize=18, color=INK)
        beam_axis.plot(model.span, -0.3, marker="^", markersize=18, color=INK)
        beam_axis.plot([0, model.span], [-0.48, -0.48], color=INK, linewidth=2)

    for load in model.point_loads:
        if load.direction.value == "down":
            beam_axis.annotate(
                f"{load.magnitude:.1f} kip",
                xy=(load.position, 0.05),
                xytext=(load.position, 1.25),
                ha="center",
                color=PURPLE,
                arrowprops={"arrowstyle": "-|>", "color": PURPLE, "lw": 1.8},
            )
        else:
            beam_axis.annotate(
                f"{load.magnitude:.1f} kip",
                xy=(load.position, -0.05),
                xytext=(load.position, -1.05),
                ha="center",
                color=PURPLE,
                arrowprops={"arrowstyle": "-|>", "color": PURPLE, "lw": 1.8},
            )

    for load in model.uniform_loads:
        y = 0.8 if load.direction.value == "down" else -0.8
        beam_axis.plot([load.start, load.end], [y, y], color=PURPLE, linewidth=1.5)
        count = max(2, min(12, int(round((load.end - load.start) / max(model.span / 10, 0.001)))))
        for x in np.linspace(load.start, load.end, count):
            if load.direction.value == "down":
                beam_axis.annotate("", xy=(x, 0.08), xytext=(x, y), arrowprops={"arrowstyle": "-|>", "color": PURPLE})
            else:
                beam_axis.annotate("", xy=(x, -0.08), xytext=(x, y), arrowprops={"arrowstyle": "-|>", "color": PURPLE})
        beam_axis.text((load.start + load.end) / 2, y + (0.12 if y > 0 else -0.2), f"{load.magnitude:.1f} kip/ft", ha="center", color=PURPLE, fontsize=8)

    for index, cut in enumerate(results.cuts):
        beam_axis.axvline(cut.location, color=(PURPLE if index == 0 else PURPLE_DARK), linestyle="--", linewidth=1)

    x = np.asarray([point.x for point in results.points])
    shear = np.asarray([point.shear for point in results.points])
    moment = np.asarray([point.moment for point in results.points])
    deflection = np.asarray([point.deflection for point in results.points])
    for axis, values, color, fill in (
        (shear_axis, shear, PURPLE, "#dcd0f1"),
        (moment_axis, moment, PURPLE, "#dcd0f1"),
        (deflection_axis, deflection, PURPLE, "#dcd0f1"),
    ):
        axis.plot(x, values, color=color, linewidth=2)
        axis.fill_between(x, values, 0, color=fill, alpha=0.72)
        axis.axhline(0, color="#8d8290", linewidth=0.8)
        axis.set_xlim(0, model.span)
        axis.set_xticks(np.linspace(0, model.span, 3))
        axis.set_xlabel("Position (ft)", fontsize=8, color=MUTED)

    moment_axis.annotate(
        f"{abs(results.max_absolute_moment):.2f}",
        xy=(results.governing_moment_location, results.max_absolute_moment),
        xytext=(5, 5),
        textcoords="offset points",
        fontsize=8,
        color=PURPLE_DARK,
    )
    deflection_axis.annotate(
        f"{results.deflection_check.actual:.3f} in",
        xy=(results.deflection_check.location, float(np.interp(results.deflection_check.location, x, deflection))),
        xytext=(5, 5),
        textcoords="offset points",
        fontsize=8,
        color=PURPLE_DARK,
    )
