import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from calculations import calculate
from member_data import get_member
from models import BeamModel, LoadDirection, MemberType, PointLoad, SupportType, UniformLoad


def steel_model(span, support, point_loads=(), uniform_loads=()):
    return BeamModel(
        span,
        support,
        list(point_loads),
        list(uniform_loads),
        get_member(MemberType.STEEL, "W12 x 26"),
        False,
    )


def model_with_member(span, support, designation, point_loads=(), uniform_loads=()):
    return BeamModel(
        span,
        support,
        list(point_loads),
        list(uniform_loads),
        get_member(MemberType.STEEL, designation),
        False,
    )


def test_simply_supported_uniform_load():
    result = calculate(steel_model(20, SupportType.SIMPLY_SUPPORTED, uniform_loads=[UniformLoad(1, 0, 20)]))
    assert math.isclose(result.reactions.left, 10, abs_tol=1e-8)
    assert math.isclose(result.reactions.right, 10, abs_tol=1e-8)
    assert math.isclose(abs(result.max_absolute_moment), 50, abs_tol=0.1)
    assert math.isclose(result.deflection_check.actual, 0.609, abs_tol=0.02)


def test_simply_supported_center_point_load():
    result = calculate(steel_model(20, SupportType.SIMPLY_SUPPORTED, point_loads=[PointLoad(10, 10)]))
    assert math.isclose(result.reactions.left, 5, abs_tol=1e-8)
    assert math.isclose(result.reactions.right, 5, abs_tol=1e-8)
    assert math.isclose(abs(result.max_absolute_moment), 50, abs_tol=0.1)
    assert math.isclose(result.deflection_check.actual, 0.487, abs_tol=0.02)


def test_partial_uniform_load():
    result = calculate(steel_model(20, SupportType.SIMPLY_SUPPORTED, uniform_loads=[UniformLoad(1, 5, 15)]))
    assert math.isclose(result.reactions.left, 5, abs_tol=1e-8)
    assert math.isclose(result.reactions.right, 5, abs_tol=1e-8)
    assert math.isclose(abs(result.max_absolute_moment), 37.5, abs_tol=0.2)
    assert math.isclose(max(abs(point.shear) for point in result.points), 5, abs_tol=0.05)


def test_w18x35_partial_uniform_validation_case():
    result = calculate(model_with_member(30, SupportType.SIMPLY_SUPPORTED, "W18 x 35", uniform_loads=[UniformLoad(2, 0, 15)]))
    assert math.isclose(result.reactions.left, 22.5, abs_tol=1e-8)
    assert math.isclose(result.reactions.right, 7.5, abs_tol=1e-8)
    assert math.isclose(abs(result.max_absolute_moment), 126.5625, abs_tol=0.2)
    assert math.isclose(result.governing_moment_location, 11.25, abs_tol=0.05)


def test_cantilever_cases():
    point = calculate(steel_model(10, SupportType.CANTILEVER, point_loads=[PointLoad(10, 10)]))
    uniform = calculate(steel_model(10, SupportType.CANTILEVER, uniform_loads=[UniformLoad(1, 0, 10)]))
    assert math.isclose(point.reactions.left, 10, abs_tol=1e-8)
    assert math.isclose(abs(point.max_absolute_moment), 100, abs_tol=0.2)
    assert math.isclose(point.deflection_check.actual, 0.974, abs_tol=0.03)
    assert math.isclose(abs(uniform.max_absolute_moment), 50, abs_tol=0.2)
    assert math.isclose(uniform.deflection_check.actual, 0.3653, abs_tol=0.03)


def test_upward_load_changes_reaction_sign():
    result = calculate(steel_model(20, SupportType.SIMPLY_SUPPORTED, point_loads=[PointLoad(10, 10, LoadDirection.UP)]))
    assert result.reactions.left < 0
    assert result.reactions.right < 0


def test_point_load_shear_jump_and_moment_continuity():
    result = calculate(steel_model(20, SupportType.SIMPLY_SUPPORTED, point_loads=[PointLoad(10, 10)]))
    before = next(point for point in result.points if point.x < 10 and abs(point.x - 10) < 0.1)
    at_load = next(point for point in result.points if point.x == 10)
    assert math.isclose(before.moment, at_load.moment, abs_tol=0.6)
    assert math.isclose(before.shear - at_load.shear, 10, abs_tol=0.02)


def test_support_boundary_conditions():
    simply = calculate(steel_model(20, SupportType.SIMPLY_SUPPORTED, uniform_loads=[UniformLoad(1, 0, 20)]))
    cantilever = calculate(steel_model(10, SupportType.CANTILEVER, point_loads=[PointLoad(10, 10)]))
    assert math.isclose(simply.points[0].deflection, 0, abs_tol=1e-10)
    assert math.isclose(simply.points[-1].deflection, 0, abs_tol=1e-10)
    assert math.isclose(cantilever.points[0].deflection, 0, abs_tol=1e-10)
    assert math.isclose(cantilever.points[0].slope, 0, abs_tol=1e-8)
