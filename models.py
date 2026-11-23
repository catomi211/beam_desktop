from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class SupportType(str, Enum):
    SIMPLY_SUPPORTED = "Simply supported"
    CANTILEVER = "Cantilever"


class LoadDirection(str, Enum):
    DOWN = "down"
    UP = "up"


class MemberType(str, Enum):
    STEEL = "Steel W-shape"
    LUMBER = "Lumber"


@dataclass(frozen=True)
class PointLoad:
    magnitude: float
    position: float
    direction: LoadDirection = LoadDirection.DOWN


@dataclass(frozen=True)
class UniformLoad:
    magnitude: float
    start: float
    end: float
    direction: LoadDirection = LoadDirection.DOWN


@dataclass(frozen=True)
class Member:
    member_type: MemberType
    designation: str
    grade: str
    species: Optional[str]
    elastic_modulus: float
    moment_inertia: float
    section_modulus: float
    allowable_bending_stress: float
    assumed_self_weight: float


@dataclass
class BeamModel:
    span: float
    support_type: SupportType
    point_loads: list[PointLoad] = field(default_factory=list)
    uniform_loads: list[UniformLoad] = field(default_factory=list)
    member: Optional[Member] = None
    include_self_weight: bool = False
    deflection_limit: Optional[float] = None


@dataclass(frozen=True)
class ValidationError:
    field: str
    message: str


@dataclass(frozen=True)
class SeriesPoint:
    x: float
    shear: float
    moment: float
    deflection: float
    slope: float


@dataclass(frozen=True)
class Reactions:
    left: float
    right: float
    fixed_moment: float


@dataclass(frozen=True)
class CheckResult:
    actual: float
    allowable: float
    passes: bool
    location: float


@dataclass(frozen=True)
class CutResult:
    location: float
    shear: float
    moment: float
    stress: float
    slope: float


@dataclass(frozen=True)
class CalculationResults:
    reactions: Reactions
    points: tuple[SeriesPoint, ...]
    max_positive_shear: float
    max_negative_shear: float
    max_positive_moment: float
    max_negative_moment: float
    max_absolute_moment: float
    governing_moment_location: float
    deflection_check: CheckResult
    bending_check: CheckResult
    cuts: tuple[CutResult, CutResult]
