import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from calculation_sheet import export_calculation_sheet
from calculations import calculate
from member_data import get_member
from models import BeamModel, MemberType, PointLoad, SupportType, UniformLoad


def test_calculation_sheet_creates_pdf(tmp_path):
    model = BeamModel(
        20,
        SupportType.SIMPLY_SUPPORTED,
        [PointLoad(10, 10)],
        [UniformLoad(1, 0, 20)],
        get_member(MemberType.STEEL, "W12 x 26"),
        True,
        0.8,
    )
    path = tmp_path / "calculation-sheet.pdf"
    export_calculation_sheet(path, model, calculate(model))

    data = path.read_bytes()
    assert data.startswith(b"%PDF-")
    assert len(data) > 1000
    assert data.count(b"/Type /Page ") == 2
    assert data.count(b"/MediaBox [ 0 0 612 792 ]") == 2
    source = Path(__file__).parents[1].joinpath("calculation_sheet.py").read_text(encoding="utf-8")
    assert "Page 1 of" not in source
    assert "Page 2 of" not in source
    assert "preliminary calculation" not in source
    assert "code-compliant" not in source


def test_cantilever_calculation_sheet_creates_pdf(tmp_path):
    model = BeamModel(
        10,
        SupportType.CANTILEVER,
        [PointLoad(10, 10)],
        [],
        get_member(MemberType.STEEL, "W12 x 26"),
        False,
        0.5,
    )
    path = tmp_path / "cantilever-calculation-sheet.pdf"
    export_calculation_sheet(path, model, calculate(model))

    assert path.read_bytes().startswith(b"%PDF-")
