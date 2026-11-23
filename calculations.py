from __future__ import annotations

import numpy as np

from models import (
    BeamModel,
    CalculationResults,
    CheckResult,
    CutResult,
    LoadDirection,
    Reactions,
    SeriesPoint,
    SupportType,
    UniformLoad,
)


def _signed(magnitude: float, direction: LoadDirection) -> float:
    return magnitude if direction is LoadDirection.DOWN else -magnitude


def _effective_uniform_loads(model: BeamModel):
    loads = list(model.uniform_loads)
    if model.include_self_weight and model.member is not None:
        loads.append(
            UniformLoad(model.member.assumed_self_weight, 0.0, model.span, LoadDirection.DOWN)
        )
    return loads


def calculate_reactions(model: BeamModel) -> Reactions:
    total = 0.0
    moment_left = 0.0
    for load in model.point_loads:
        signed = _signed(load.magnitude, load.direction)
        total += signed
        moment_left += signed * load.position
    for load in _effective_uniform_loads(model):
        signed_total = _signed(load.magnitude * (load.end - load.start), load.direction)
        total += signed_total
        moment_left += signed_total * (load.start + load.end) / 2

    if model.support_type is SupportType.CANTILEVER:
        return Reactions(total, 0.0, -moment_left)
    right = moment_left / model.span
    return Reactions(total - right, right, 0.0)


def _shear_moment_at(model: BeamModel, x: float, reactions: Reactions) -> tuple[float, float]:
    if model.support_type is SupportType.CANTILEVER:
        shear = reactions.left
        moment = 0.0
        for load in model.point_loads:
            signed = _signed(load.magnitude, load.direction)
            if load.position > x:
                moment -= signed * (load.position - x)
            else:
                shear -= signed
        for load in _effective_uniform_loads(model):
            signed = _signed(load.magnitude, load.direction)
            if x < load.end:
                start = max(x, load.start)
                length = load.end - start
                if length > 0:
                    moment -= signed * length * (start + load.end) / 2 - signed * length * x
            if x > load.start:
                shear -= signed * (min(x, load.end) - load.start)
        return shear, moment

    shear = reactions.left
    moment = reactions.left * x
    for load in model.point_loads:
        signed = _signed(load.magnitude, load.direction)
        if load.position <= x:
            shear -= signed
            moment -= signed * (x - load.position)
    for load in _effective_uniform_loads(model):
        signed = _signed(load.magnitude, load.direction)
        if x > load.start:
            end = min(x, load.end)
            if end > load.start:
                length = end - load.start
                shear -= signed * length
                moment -= signed * length * (x - (load.start + end) / 2)
    return shear, moment


def _grid(model: BeamModel, steps: int = 800) -> np.ndarray:
    critical = [0.0, model.span]
    critical.extend(load.position for load in model.point_loads)
    critical.extend(value for load in model.uniform_loads for value in (load.start, load.end))
    critical = sorted(set(value for value in critical if 0 <= value <= model.span))
    base = np.linspace(0.0, model.span, steps + 1)
    return np.unique(np.concatenate((base, np.asarray(critical, dtype=float))))


def _integrate_deflection(x_ft: np.ndarray, moment: np.ndarray, model: BeamModel) -> tuple[np.ndarray, np.ndarray]:
    x_in = x_ft * 12
    curvature = -(moment * 12) / (model.member.elastic_modulus * model.member.moment_inertia)
    rotation = np.zeros_like(x_in)
    rotation[1:] = np.cumsum((curvature[:-1] + curvature[1:]) * np.diff(x_in) / 2)
    deflection = np.zeros_like(x_in)
    deflection[1:] = np.cumsum((rotation[:-1] + rotation[1:]) * np.diff(x_in) / 2)
    if model.support_type is SupportType.SIMPLY_SUPPORTED and x_in[-1] > 0:
        deflection -= deflection[-1] * x_in / x_in[-1]
    slope = np.gradient(deflection, x_in, edge_order=1)
    if model.support_type is SupportType.CANTILEVER:
        slope[0] = 0.0
    return deflection, slope


def calculate(model: BeamModel, cuts: tuple[float, float] = (5.0, 15.0)) -> CalculationResults:
    reactions = calculate_reactions(model)
    x = _grid(model)
    shear = np.empty_like(x)
    moment = np.empty_like(x)
    for index, position in enumerate(x):
        shear[index], moment[index] = _shear_moment_at(model, float(position), reactions)
    deflection, slope = _integrate_deflection(x, moment, model)

    points = tuple(
        SeriesPoint(float(position), float(v_shear), float(v_moment), float(v_deflection), float(v_slope))
        for position, v_shear, v_moment, v_deflection, v_slope in zip(x, shear, moment, deflection, slope)
    )
    max_moment_index = int(np.argmax(np.abs(moment)))
    max_deflection_index = int(np.argmax(np.abs(deflection)))
    maximum_moment = float(moment[max_moment_index])
    stress = abs(maximum_moment * 12) / model.member.section_modulus
    allowable_deflection = model.span * 12 / 360
    bending = CheckResult(
        stress,
        model.member.allowable_bending_stress,
        stress <= model.member.allowable_bending_stress,
        float(x[max_moment_index]),
    )
    deflection_check = CheckResult(
        abs(float(deflection[max_deflection_index])),
        allowable_deflection,
        abs(float(deflection[max_deflection_index])) <= allowable_deflection,
        float(x[max_deflection_index]),
    )

    cuts_result: list[CutResult] = []
    for location in cuts:
        cut_shear = float(np.interp(location, x, shear))
        cut_moment = float(np.interp(location, x, moment))
        cut_slope = float(np.interp(location, x, slope))
        cuts_result.append(CutResult(location, cut_shear, cut_moment, abs(cut_moment * 12) / model.member.section_modulus, cut_slope))

    return CalculationResults(
        reactions,
        points,
        float(np.max(shear)),
        float(np.min(shear)),
        float(np.max(moment)),
        float(np.min(moment)),
        maximum_moment,
        float(x[max_moment_index]),
        deflection_check,
        bending,
        (cuts_result[0], cuts_result[1]),
    )
