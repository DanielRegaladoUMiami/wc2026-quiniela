"""Single source of truth for canonical national-team names.

Three independent feeds disagree on spellings — the Kaggle match log
("Czech Republic", "Curaçao"), ESPN's odds API ("Congo DR", "Bosnia-Herzegovina")
and the WC2026 bracket. If they don't match, the model can't find a team and silently
falls back to a uniform 1X2 — which looks like a huge "edge" but is just a bug.

`canonical()` maps every known variant onto the bracket spelling so the match log,
features, market odds and fixtures all line up. Add variants here when a new feed is wired.
"""

from __future__ import annotations

# variant (any feed) -> canonical (the WC2026 bracket spelling)
CANONICAL: dict[str, str] = {
    # Kaggle match-log spellings
    "Czech Republic": "Czechia",
    "Curaçao": "Curacao",
    # ESPN odds-API spellings
    "Congo DR": "DR Congo",
    "Bosnia-Herzegovina": "Bosnia and Herzegovina",
    "Bosnia & Herzegovina": "Bosnia and Herzegovina",
    "Korea Republic": "South Korea",
    "Korea DPR": "North Korea",
    "IR Iran": "Iran",
    "Türkiye": "Turkey",
    "Turkiye": "Turkey",
    "Côte d'Ivoire": "Ivory Coast",
    "Cote d'Ivoire": "Ivory Coast",
    "USA": "United States",
    "Cabo Verde": "Cape Verde",
}


def canonical(name: str | None) -> str | None:
    """Return the canonical (bracket) spelling for a team name, or the input unchanged."""
    if not name:
        return name
    return CANONICAL.get(name.strip(), name.strip())
