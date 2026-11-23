from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from member_data import get_member
from models import (
    BeamModel,
    LoadDirection,
    MemberType,
    PointLoad,
    SupportType,
    UniformLoad,
)


FILE_VERSION = 1


class BeamFileError(ValueError):
    pass


def beam_to_dict(model: BeamModel) -> dict[str, Any]:
    if model.member is None:
        raise BeamFileError("A member is required before saving.")
    member = model.member
    return {
        "format": "beam-design",
        "version": FILE_VERSION,
        "support_type": model.support_type.value,
        "span_ft": model.span,
        "deflection_limit_in": model.deflection_limit,
        "include_self_weight": model.include_self_weight,
        "member": {
            "type": member.member_type.value,
            "designation": member.designation,
            "grade": member.grade,
            "species": member.species,
            "E_ksi": member.elastic_modulus,
            "I_in4": member.moment_inertia,
            "S_in3": member.section_modulus,
            "Fb_ksi": member.allowable_bending_stress,
            "assumed_self_weight_kip_ft": member.assumed_self_weight,
        },
        "point_loads": [
            {
                "magnitude_kip": load.magnitude,
                "position_ft": load.position,
                "direction": load.direction.value,
            }
            for load in model.point_loads
        ],
        "uniform_loads": [
            {
                "magnitude_kip_ft": load.magnitude,
                "start_ft": load.start,
                "end_ft": load.end,
                "direction": load.direction.value,
            }
            for load in model.uniform_loads
        ],
    }


def save_beam(path: str | Path, model: BeamModel) -> None:
    target = Path(path)
    try:
        target.write_text(json.dumps(beam_to_dict(model), indent=2), encoding="utf-8")
    except OSError as exc:
        raise BeamFileError(f"Could not save beam design: {exc}") from exc


def beam_from_dict(data: dict[str, Any]) -> BeamModel:
    if not isinstance(data, dict):
        raise BeamFileError("The beam file does not contain a JSON object.")
    if data.get("format") != "beam-design":
        raise BeamFileError("The file is not a Beam Designer design.")
    if data.get("version") != FILE_VERSION:
        raise BeamFileError("The beam file uses an unsupported version.")

    try:
        support = SupportType(data["support_type"])
        span = float(data["span_ft"])
        deflection_limit = data.get("deflection_limit_in")
        if deflection_limit is not None:
            deflection_limit = float(deflection_limit)
            if not math.isfinite(deflection_limit) or deflection_limit <= 0:
                raise BeamFileError("Deflection limit must be greater than 0 in.")
        include_self_weight = data["include_self_weight"]
        if not isinstance(include_self_weight, bool):
            raise BeamFileError("The self-weight setting is invalid.")
        member_data = data["member"]
        member_type = MemberType(member_data["type"])
        member = get_member(member_type, member_data["designation"])
    except (KeyError, TypeError, ValueError) as exc:
        raise BeamFileError(f"Beam file contains invalid or unsupported values: {exc}") from exc
    if member is None:
        raise BeamFileError("The saved member is not supported.")
    saved_properties = member_data
    for key, actual in (
        ("grade", member.grade),
        ("species", member.species),
        ("E_ksi", member.elastic_modulus),
        ("I_in4", member.moment_inertia),
        ("S_in3", member.section_modulus),
        ("Fb_ksi", member.allowable_bending_stress),
    ):
        if key not in saved_properties or saved_properties[key] != actual:
            raise BeamFileError("The saved member properties are incompatible with this app.")

    try:
        point_loads = tuple(
            PointLoad(
                float(load["magnitude_kip"]),
                float(load["position_ft"]),
                LoadDirection(load["direction"]),
            )
            for load in data["point_loads"]
        )
        uniform_loads = tuple(
            UniformLoad(
                float(load["magnitude_kip_ft"]),
                float(load["start_ft"]),
                float(load["end_ft"]),
                LoadDirection(load["direction"]),
            )
            for load in data["uniform_loads"]
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise BeamFileError(f"The beam file contains invalid loads: {exc}") from exc
    if not isinstance(include_self_weight, bool):
        raise BeamFileError("The self-weight setting is invalid.")
    if span <= 0:
        raise BeamFileError("Span must be greater than 0 ft.")

    return BeamModel(
        span=span,
        support_type=support,
        point_loads=list(point_loads),
        uniform_loads=list(uniform_loads),
        member=member,
        include_self_weight=include_self_weight,
        deflection_limit=deflection_limit,
    )


def load_beam(path: str | Path) -> BeamModel:
    source = Path(path)
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise BeamFileError(f"The beam file is not valid JSON: {exc}") from exc
    except OSError as exc:
        raise BeamFileError(f"Could not open beam design: {exc}") from exc
    return beam_from_dict(data)
