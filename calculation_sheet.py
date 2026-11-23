from __future__ import annotations

from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from models import BeamModel, CalculationResults


class CalculationSheetError(ValueError):
    pass


PAGE_WIDTH = 8.5
PAGE_HEIGHT = 11.0
STANDARD_MARGIN = 0.75
LEFT = STANDARD_MARGIN / PAGE_WIDTH
RIGHT = 1.0 - STANDARD_MARGIN / PAGE_WIDTH
TOP = 1.0 - STANDARD_MARGIN / PAGE_HEIGHT
BOTTOM = STANDARD_MARGIN / PAGE_HEIGHT


def _direction(value) -> str:
    return "upward" if value.value == "up" else "downward"


def export_calculation_sheet(path: str | Path, model: BeamModel, results: CalculationResults) -> None:
    target = Path(path)
    try:
        member = model.member
        limit = model.deflection_limit if model.deflection_limit is not None else model.span * 12 / 360
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        input_lines = [
            f"Support type: {model.support_type.value}",
            f"Span: {model.span:.4f} ft",
            f"Member: {member.member_type.value} - {member.designation}",
            f"Grade/species: {member.grade}" + (f" - {member.species}" if member.species else ""),
            f"Elastic modulus E: {member.elastic_modulus:.2f} ksi",
            f"Moment of inertia I: {member.moment_inertia:.4f} in^4",
            f"Section modulus S: {member.section_modulus:.4f} in^3",
            f"Allowable bending stress: {member.allowable_bending_stress:.4f} ksi",
            f"Deflection limit: {limit:.4f} in",
            f"Self-weight: {'included (assumed ' + format(member.assumed_self_weight, '.4f') + ' kip/ft)' if model.include_self_weight else 'excluded'}",
        ]
        for load in model.point_loads:
            input_lines.append(
                f"Point load: {load.magnitude:.4f} kip at {load.position:.4f} ft, {_direction(load.direction)}"
            )
        for load in model.uniform_loads:
            input_lines.append(
                f"Uniform load: {load.magnitude:.4f} kip/ft from {load.start:.4f} ft to {load.end:.4f} ft, {_direction(load.direction)}"
            )
        for index, cut in enumerate(results.cuts, start=1):
            input_lines.append(f"Cut {index}: {cut.location:.4f} ft")

        with PdfPages(target) as pdf:
            page1 = plt.figure(figsize=(8.5, 11), facecolor="white")
            page1.text(LEFT, TOP - 0.02, "Beam Designer - Calculation Sheet", fontsize=17, fontweight="bold")
            page1.text(LEFT, TOP - 0.07, f"Generated: {timestamp}", fontsize=9, color="#68616d")
            page1.text(LEFT, TOP - 0.13, "Inputs", fontsize=13, fontweight="bold")
            page1.text(
                LEFT,
                TOP - 0.18,
                "\n".join(input_lines),
                fontsize=11,
                va="top",
                linespacing=1.75,
            )
            pdf.savefig(page1)
            plt.close(page1)

            page2 = plt.figure(figsize=(8.5, 11), facecolor="white")
            page2.text(LEFT, TOP - 0.02, "Beam Designer - Calculation Outputs", fontsize=17, fontweight="bold")
            page2.text(LEFT, TOP - 0.07, f"Generated: {timestamp}", fontsize=9, color="#68616d")

            beam_ax = page2.add_axes([LEFT, 0.70, RIGHT - LEFT, 0.16])
            beam_ax.set_facecolor("#fffafd")
            beam_ax.set_xlim(0, model.span)
            beam_ax.set_ylim(-1.5, 1.8)
            beam_ax.set_yticks([])
            beam_ax.plot([0, model.span], [0, 0], color="#17151a", linewidth=4)
            if model.support_type.value == "Cantilever":
                beam_ax.plot([0, 0], [-0.65, 0.65], color="#17151a", linewidth=8)
            else:
                beam_ax.plot(0, -0.30, marker="^", markersize=16, color="#17151a")
                beam_ax.plot(model.span, -0.30, marker="^", markersize=16, color="#17151a")
            for load in model.point_loads:
                y = 1.15 if load.direction.value == "down" else -1.05
                beam_ax.annotate(
                    f"{load.magnitude:.4f} kip",
                    xy=(load.position, 0),
                    xytext=(load.position, y),
                    ha="center",
                    arrowprops={"arrowstyle": "-|>", "color": "#7654a7"},
                    color="#7654a7",
                    fontsize=8,
                )
            for load in model.uniform_loads:
                y = 0.8 if load.direction.value == "down" else -0.8
                beam_ax.plot([load.start, load.end], [y, y], color="#7654a7", linewidth=1.5)
            beam_ax.set_title("Beam and loading", loc="left", fontsize=11, fontweight="bold")
            beam_ax.grid(True, axis="x", color="#eee6ef")

            shear_ax = page2.add_axes([LEFT, 0.54, RIGHT - LEFT, 0.12])
            moment_ax = page2.add_axes([LEFT, 0.38, RIGHT - LEFT, 0.12])
            deflection_ax = page2.add_axes([LEFT, 0.22, RIGHT - LEFT, 0.12])
            x = [point.x for point in results.points]
            for axis, values, title in (
                (shear_ax, [point.shear for point in results.points], "Shear diagram (kip)"),
                (moment_ax, [point.moment for point in results.points], "Moment diagram (kip-ft)"),
                (deflection_ax, [point.deflection for point in results.points], "Deflection diagram (in)"),
            ):
                axis.plot(x, values, color="#7654a7", linewidth=1.8)
                axis.fill_between(x, values, 0, color="#dcd0f1", alpha=0.72)
                axis.axhline(0, color="#8d8290", linewidth=0.8)
                axis.set_title(title, loc="left", fontsize=10, fontweight="bold")
                axis.set_xlim(0, model.span)
                axis.grid(True, color="#eee6ef")
                axis.tick_params(labelsize=8)

            bending_status = "PASS" if results.bending_check.passes else "FAIL"
            deflection_status = "PASS" if results.deflection_check.passes else "FAIL"
            summary_lines = [
                f"Left reaction: {results.reactions.left:.4f} kip",
                f"Right reaction: {results.reactions.right:.4f} kip",
                f"Fixed-end moment: {results.reactions.fixed_moment:.4f} kip-ft",
                f"Maximum positive/negative shear: {results.max_positive_shear:.4f} / {results.max_negative_shear:.4f} kip",
                f"Maximum absolute moment: {abs(results.max_absolute_moment):.4f} kip-ft at {results.governing_moment_location:.4f} ft",
                f"Maximum absolute deflection: {results.deflection_check.actual:.4f} in at {results.deflection_check.location:.4f} ft",
                f"Bending stress: {results.bending_check.actual:.4f} ksi / {results.bending_check.allowable:.4f} ksi allowable - {bending_status}",
                f"Deflection: {results.deflection_check.actual:.4f} in / {results.deflection_check.allowable:.4f} in allowable - {deflection_status}",
            ]
            page2.text(
                LEFT,
                0.16,
                "Calculations and checks\n" + "\n".join(summary_lines),
                fontsize=7.5,
                va="top",
                linespacing=1.25,
            )
            pdf.savefig(page2)
            plt.close(page2)
    except OSError as exc:
        raise CalculationSheetError(f"Could not export calculation sheet: {exc}") from exc
