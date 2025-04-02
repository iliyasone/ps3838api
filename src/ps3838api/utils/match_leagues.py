# type: ignore
import json
from pathlib import Path
from typing import Any

from ps3838api import ROOT_DIR

def normalize_to_set(name: str) -> set[str]:
    return set(
        name.replace(" II", " 2").replace(" I", "").lower().replace("-", " ").split()
    )


def load_json(path: str | Path) -> list[Any] | dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    # Paths
    betsapi_path = ROOT_DIR / Path("out/betsapi_leagues.json")
    ps3838_path = ROOT_DIR / Path("out/ps3838_leagues.json")
    output_path = ROOT_DIR / Path("out/matched_leagues.json")

    # Load files
    betsapi_leagues = load_json(betsapi_path)
    ps3838_data = load_json(ps3838_path)["leagues"]

    # Build normalized index for ps3838
    ps3838_index = []
    for league in ps3838_data:
        ps3838_index.append(
            {
                "name": league["name"],
                "id": league["id"],
                "norm_set": normalize_to_set(league["name"]),
            }
        )

    # Match
    matched = []
    for betsapi_league in betsapi_leagues:
        norm_betsapi = normalize_to_set(betsapi_league)
        match = next(
            (
                {
                    "betsapi_league": betsapi_league,
                    "ps3838_league": ps["name"],
                    "ps3838_id": ps["id"],
                }
                for ps in ps3838_index
                if ps["norm_set"] == norm_betsapi
            ),
            {
                "betsapi_league": betsapi_league,
                "ps3838_league": None,
                "ps3838_id": None,
            },
        )
        matched.append(match)

    # Save output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(matched, f, indent=2, ensure_ascii=False)

    print(f"✅ Matching complete. Output saved to: {output_path}")


if __name__ == "__main__":
    main()
