from __future__ import annotations

import csv
from pathlib import Path

from models import CalculationResults


class CSVExportError(ValueError):
    pass


def export_results(path: str | Path, results: CalculationResults) -> None:
    target = Path(path)
    try:
        with target.open("w", encoding="utf-8", newline="") as csv_file:
            writer = csv.writer(csv_file, delimiter=",", lineterminator="\r\n")
            writer.writerow(["X (ft)", "V (kip)", "M (kip-ft)", "Deflection (in)"])
            x_values = [float(point.x) for point in results.points]
            shear_values = [float(point.shear) for point in results.points]
            moment_values = [float(point.moment) for point in results.points]
            deflection_values = [float(point.deflection) for point in results.points]
            span = x_values[-1]
            locations = list(range(int(span) + 1))
            if not locations or abs(locations[-1] - span) > 1e-12:
                locations.append(span)

            for location in locations:
                writer.writerow(
                    [
                        str(int(location)) if isinstance(location, int) else f"{location:.4f}",
                        f"{_interpolate(location, x_values, shear_values):.4f}",
                        f"{_interpolate(location, x_values, moment_values):.4f}",
                        f"{_interpolate(location, x_values, deflection_values):.4f}",
                    ]
                )
    except OSError as exc:
        raise CSVExportError(f"Could not export beam results: {exc}") from exc


def _interpolate(location: float, x_values: list[float], values: list[float]) -> float:
    if location <= x_values[0]:
        return values[0]
    if location >= x_values[-1]:
        return values[-1]
    import bisect

    index = bisect.bisect_left(x_values, location)
    if x_values[index] == location:
        return values[index]
    left = index - 1
    fraction = (location - x_values[left]) / (x_values[index] - x_values[left])
    return values[left] + fraction * (values[index] - values[left])
