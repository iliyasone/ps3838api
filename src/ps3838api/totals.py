from typing import cast
from typing import NotRequired
from ps3838api.models.odds import OddsTotalV3, OddsEventV3
from ps3838api.models.odds import OddsTotalV3


class OddsTotal(OddsTotalV3):
    """Either has line or alt line id"""

    lineId: NotRequired[int]


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
        if (
            "number" not in period
            or period["number"] not in periods
            or "totals" not in period
        ):
            continue

        lineId = period["lineId"] if "lineId" in period else None
        maxTotal = period["maxTotal"] if "maxTotal" in period else None

        for total in period["totals"]:
            if "altLineId" not in total and lineId is not None:
                odds_total = cast(OddsTotal, total.copy())
                odds_total["lineId"] = lineId
                if maxTotal is not None:
                    odds_total["max"] = maxTotal
                result.append(odds_total)
            else:
                result.append(cast(OddsTotal, total))
    return result


def get_best_total_line(
    odds: OddsEventV3, periods: list[int] = [0, 1]
) -> OddsTotal | None:
    try:
        return min(get_all_total_lines(odds, periods=periods), key=calculate_margin)
    except Exception:
        return None
