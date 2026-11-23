import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

import pytest

from design_files import BeamFileError, beam_to_dict, load_beam, save_beam
from member_data import get_member
from models import BeamModel, LoadDirection, MemberType, PointLoad, SupportType, UniformLoad
from validation import validate_model


def sample_model():
    return BeamModel(
        20,
        SupportType.CANTILEVER,
        [PointLoad(5, 20, LoadDirection.DOWN)],
        [UniformLoad(1, 0, 20, LoadDirection.UP)],
        get_member(MemberType.STEEL, "W12 x 26"),
        True,
        0.75,
    )


def test_save_and_load_round_trip(tmp_path):
    path = tmp_path / "saved.beam.json"
    save_beam(path, sample_model())
    restored = load_beam(path)
    assert restored == sample_model()
    assert validate_model(restored) == []


def test_invalid_json_is_rejected(tmp_path):
    path = tmp_path / "invalid.beam.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(BeamFileError):
        load_beam(path)


def test_invalid_deflection_limit_is_rejected(tmp_path):
    path = tmp_path / "invalid-limit.beam.json"
    model = sample_model()
    model.deflection_limit = 0
    path.write_text(__import__("json").dumps(beam_to_dict(model)), encoding="utf-8")
    with pytest.raises(BeamFileError):
        load_beam(path)
