import warnings
from typing import cast

from ps3838api.models.odds import OddsEventV3, OddsTotalV3

warnings.warn(
    f"{__name__} is experimental and its interface is not stable yet.",
    FutureWarning,
)


class OddsTotal(OddsTotalV3):
    """Has line id"""

    lineId: int


def calculate_margin(total: OddsTotalV3) -> float:
    return (1 / total["over"] + 1 / total["under"]) - 1


def get_all_total_lines(
    odds: OddsEventV3,
    periods: list[int] = [
        0,
    ],
) -> list[OddsTotal]:
    result: list[OddsTotal] = []
    for period in odds["periods"]:  # type: ignore
        if "number" not in period:
            # skip if unknown period
            continue
        if period["number"] not in periods:
            # skip if wrong periood
            continue
        if "totals" not in period:
            # skip if no totals in this period
            continue
        if "lineId" not in period:
            # skip if don't have lineId
            continue

        lineId = period["lineId"]
        maxTotal = period["maxTotal"] if "maxTotal" in period else None

        for total in period["totals"]:
            odds_total = cast(OddsTotal, total.copy())
            odds_total["lineId"] = lineId
            # each total should have lineId

            if "altLineId" not in total:
                if maxTotal is not None:
                    odds_total["max"] = maxTotal
            result.append(odds_total)
    return result


def get_best_total_line(odds: OddsEventV3, periods: list[int] = [0, 1]) -> OddsTotal | None:
    try:
        return min(get_all_total_lines(odds, periods=periods), key=calculate_margin)
    except Exception:
        return None
