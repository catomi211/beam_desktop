from __future__ import annotations

from models import Member, MemberType


_STEEL = {
    "W12 x 26": Member(MemberType.STEEL, "W12 x 26", "A992", None, 29000, 204, 33.4, 24, 0.026),
    "W10 x 22": Member(MemberType.STEEL, "W10 x 22", "A992", None, 29000, 118, 26.4, 24, 0.022),
    "W16 x 40": Member(MemberType.STEEL, "W16 x 40", "A992", None, 29000, 518, 64.7, 24, 0.040),
    "W18 x 35": Member(MemberType.STEEL, "W18 x 35", "A992", None, 29000, 510, 56.7, 24, 0.035),
}

_LUMBER = {
    "2 x 12": Member(MemberType.LUMBER, "2 x 12", "No. 2", "Douglas Fir-Larch", 1600, 178, 31.64, 1.45, 0.010),
    "2 x 10": Member(MemberType.LUMBER, "2 x 10", "No. 2", "Douglas Fir-Larch", 1600, 98.93, 21.39, 1.45, 0.008),
    "4 x 12": Member(MemberType.LUMBER, "4 x 12", "No. 2", "Douglas Fir-Larch", 1600, 570, 95, 1.45, 0.020),
}


def designations(member_type: MemberType) -> tuple[str, ...]:
    return tuple(_STEEL if member_type is MemberType.STEEL else _LUMBER)


def get_member(member_type: MemberType, designation: str) -> Member | None:
    records = _STEEL if member_type is MemberType.STEEL else _LUMBER
    return records.get(designation)
