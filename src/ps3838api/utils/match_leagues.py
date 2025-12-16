# type: ignore
import json
from pathlib import Path
from typing import Any

from rapidfuzz import fuzz, process

from ps3838api import ROOT_MODULE_DIR


# Your threshold-based fuzzy function
def is_leagues_match(league1: str, league2: str, threshold: int = 80) -> bool:
    """
    Returns True if leagues are a fuzzy match with a token sort ratio >= threshold.
    fuzz.token_sort_ratio() returns 0-100, so 80 means 80% similar.
    """
    return fuzz.token_sort_ratio(league1, league2) >= threshold


def load_json(path: str | Path) -> list[Any] | dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    betsapi_path = ROOT_MODULE_DIR / Path("out/betsapi_leagues.json")
    ps3838_path = ROOT_MODULE_DIR / Path("out/ps3838_leagues.json")
    output_path = ROOT_MODULE_DIR / Path("out/matched_leagues.json")

    # --------------------------------------------------------------------
    # Load raw data
    # --------------------------------------------------------------------
    betsapi_leagues = load_json(betsapi_path)  # e.g. ["Premier League", "La Liga", ...]
    ps3838_data = load_json(ps3838_path)
    # --------------------------------------------------------------------
    # Build a RapidFuzz index of PS3838 league names to do quick "best-match" lookups
    # --------------------------------------------------------------------
    # 1) Just keep a list of league names:
    ps_names = [league["name"] for league in ps3838_data]

    # 2) Also map name -> (full record) for easy ID lookup:
    ps_map = {league["name"]: league for league in ps3838_data}

    # --------------------------------------------------------------------
    # Compare each BetsAPI league to the best PS3838 league match
    # --------------------------------------------------------------------
    matched = []
    for betsapi_league in betsapi_leagues:
        # RapidFuzz: find the single best match
        # extractOne returns a tuple: (best_match_string, score, index)
        best_match = process.extractOne(betsapi_league, ps_names, scorer=fuzz.token_sort_ratio)

        if best_match is not None:
            ps_name, score, _ = best_match
            if score >= 80:
                # It's a good fuzzy match
                matched_league_info = {
                    "betsapi_league": betsapi_league,
                    "ps3838_league": ps_map[ps_name]["name"],
                    "ps3838_id": ps_map[ps_name]["id"],
                }
            else:
                # We got a best match but it's below threshold
                matched_league_info = {
                    "betsapi_league": betsapi_league,
                    "ps3838_league": None,
                    "ps3838_id": None,
                }
        else:
            # No match at all
            matched_league_info = {
                "betsapi_league": betsapi_league,
                "ps3838_league": None,
                "ps3838_id": None,
            }

        matched.append(matched_league_info)

    # --------------------------------------------------------------------
    # Save output
    # --------------------------------------------------------------------
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(matched, f, indent=2, ensure_ascii=False)

    print(f"✅ Matching complete. Output saved to: {output_path}")


if __name__ == "__main__":
    main()
