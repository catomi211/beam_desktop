import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from member_data import get_member
from models import BeamModel, MemberType, PointLoad, SupportType, UniformLoad
from validation import validate_cut, validate_model


def valid_model():
    return BeamModel(
        20,
        SupportType.SIMPLY_SUPPORTED,
        [PointLoad(5, 5)],
        [UniformLoad(1, 0, 20)],
        get_member(MemberType.STEEL, "W12 x 26"),
    )


def test_invalid_span_and_loads_are_reported():
    model = BeamModel(
        0,
        SupportType.SIMPLY_SUPPORTED,
        [PointLoad(-1, 25)],
        [UniformLoad(1, 10, 5)],
        None,
    )
    fields = {error.field for error in validate_model(model)}
    assert {"span", "point_0_magnitude", "point_0_position", "uniform_0_start", "uniform_0_end", "uniform_0_range", "member"} <= fields


def test_valid_model_has_no_errors():
    assert validate_model(valid_model()) == []


def test_cut_must_be_inside_span():
    assert validate_cut(0, 20, 1) is None
    assert validate_cut(20, 20, 2) is None
    assert validate_cut(20.1, 20, 2) is not None
