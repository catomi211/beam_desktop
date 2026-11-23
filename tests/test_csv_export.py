import csv
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from calculations import calculate
from csv_export import export_results
from member_data import get_member
from models import BeamModel, MemberType, PointLoad, SupportType, UniformLoad


def test_csv_exports_exact_headers_and_full_grid(tmp_path):
    model = BeamModel(
        20,
        SupportType.SIMPLY_SUPPORTED,
        [PointLoad(10, 10)],
        [],
        get_member(MemberType.STEEL, "W12 x 26"),
        False,
    )
    results = calculate(model)
    path = tmp_path / "beam_results.csv"
    export_results(path, results)

    with path.open("r", encoding="utf-8", newline="") as csv_file:
        rows = list(csv.reader(csv_file))

    assert rows[0] == ["X (ft)", "V (kip)", "M (kip-ft)", "Deflection (in)"]
    assert len(rows) == 22
    assert float(rows[1][0]) == 0
    assert math.isclose(float(rows[-1][0]), 20, abs_tol=1e-12)
    assert all(row[0].isdigit() for row in rows[1:])
    assert all(
        "." in row[column] and len(row[column].split(".")[1]) == 4
        for row in rows[1:]
        for column in (1, 2, 3)
    )


def test_csv_is_crlf_and_contains_numeric_values(tmp_path):
    model = BeamModel(
        10,
        SupportType.CANTILEVER,
        [PointLoad(10, 10)],
        [],
        get_member(MemberType.STEEL, "W12 x 26"),
        False,
    )
    path = tmp_path / "cantilever.csv"
    export_results(path, calculate(model))
    raw = path.read_bytes()

    assert b"\r\n" in raw
    assert b"\n" not in raw.replace(b"\r\n", b"")
    text = raw.decode("utf-8")
    assert text.startswith("X (ft),V (kip),M (kip-ft),Deflection (in)\r\n")
