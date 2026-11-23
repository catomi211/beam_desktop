from __future__ import annotations

from models import BeamModel, ValidationError


def validate_model(model: BeamModel) -> list[ValidationError]:
    errors: list[ValidationError] = []
    if model.span <= 0:
        errors.append(ValidationError("span", "Span must be greater than 0 ft."))

    for index, load in enumerate(model.point_loads):
        prefix = f"point_{index}"
        if load.magnitude <= 0:
            errors.append(ValidationError(f"{prefix}_magnitude", "Point-load magnitude must be greater than 0 kip."))
        if load.position < 0 or load.position > model.span:
            errors.append(ValidationError(f"{prefix}_position", "Point-load position must be within the beam span."))

    for index, load in enumerate(model.uniform_loads):
        prefix = f"uniform_{index}"
        if load.magnitude <= 0:
            errors.append(ValidationError(f"{prefix}_magnitude", "Uniform-load magnitude must be greater than 0 kip/ft."))
        if load.start < 0 or load.start >= model.span:
            errors.append(ValidationError(f"{prefix}_start", "Uniform-load start must be within the beam span."))
        if load.end <= 0 or load.end > model.span:
            errors.append(ValidationError(f"{prefix}_end", "Uniform-load end must be within the beam span."))
        if load.start >= load.end:
            errors.append(ValidationError(f"{prefix}_range", "Uniform-load start must be less than its end."))

    if model.member is None:
        errors.append(ValidationError("member", "A supported member selection is required."))
    return errors


def validate_cut(location: float, span: float, number: int) -> ValidationError | None:
    if location < 0 or location > span:
        return ValidationError(
            f"cut_{number}",
            f"Cut {number} must be between 0 ft and {span:.1f} ft.",
        )
    return None
