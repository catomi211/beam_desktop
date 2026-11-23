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
            writer.writerow(["x", "V", "M", "deflection"])
            for point in results.points:
                writer.writerow(
                    [
                        format(point.x, ".17g"),
                        format(point.shear, ".17g"),
                        format(point.moment, ".17g"),
                        format(point.deflection, ".17g"),
                    ]
                )
    except OSError as exc:
        raise CSVExportError(f"Could not export beam results: {exc}") from exc
