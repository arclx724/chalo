import logging
from datetime import date

from .http import fetch

LOGGER = logging.getLogger("MissKaty")

IMDB_GRAPHQL_URL = "https://caching.graphql.imdb.com/"
IMDB_GRAPHQL_HEADERS = {
    "accept": "application/graphql+json, application/json",
    "accept-language": "en-US,en;q=0.9",
    "content-type": "application/json",
    "origin": "https://www.imdb.com",
    "referer": "https://www.imdb.com/",
    "priority": "u=1, i",
    "user-agent": (
        "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/137.0.0.0 Mobile Safari/537.36"
    ),
}
IMDB_TITLE_QUERY = """query GetTitle($id: ID!) {
  title(id: $id) {
    id
    titleText { text }
    originalTitleText { text }
    titleType { text }
    releaseYear { year }
    releaseDate { day month year }
    runtime { seconds }
    ratingsSummary { aggregateRating voteCount }
    spokenLanguages { spokenLanguages { text } }
    countriesOfOrigin { countries { text } }
    certificate { rating }
    genres { genres { text } }
    plot { plotText { plainText } }
    primaryImage { url }
    principalCredits {
      category { text }
      credits { name { id nameText { text } } }
    }
    keywords(first: 20) { edges { node { text } } }
    productionStatus { currentProductionStage { text } }
    nominations { total }
    wins { total }
    awardNominations(first: 1) { total }
    prestigiousAwardSummary { wins nominations award { text } }
    trivia(first: 5) { edges { node { text { plainText } } } }
    goofs(first: 5) { edges { node { text { plainText } } } }
    moreLikeThisTitles(first: 5) {
      edges {
        node {
          id
          titleText { text }
          releaseYear { year }
          ratingsSummary { aggregateRating }
        }
      }
    }
    latestTrailer { playbackURLs { url } }
  }
}"""

IMDB_TITLE_QUERY_FALLBACK = """query GetTitle($id: ID!) {
  title(id: $id) {
    id
    titleText { text }
    originalTitleText { text }
    titleType { text }
    releaseYear { year }
    releaseDate { day month year }
    runtime { seconds }
    ratingsSummary { aggregateRating voteCount }
    spokenLanguages { spokenLanguages { text } }
    countriesOfOrigin { countries { text } }
    certificate { rating }
    genres { genres { text } }
    plot { plotText { plainText } }
    primaryImage { url }
    principalCredits {
      category { text }
      credits { name { id nameText { text } } }
    }
    keywords(first: 20) { edges { node { text } } }
    productionStatus { currentProductionStage { text } }
    nominations { total }
    trivia(first: 5) { edges { node { text { plainText } } } }
    goofs(first: 5) { edges { node { text { plainText } } } }
    moreLikeThisTitles(first: 5) {
      edges {
        node {
          id
          titleText { text }
          releaseYear { year }
          ratingsSummary { aggregateRating }
        }
      }
    }
    latestTrailer { playbackURLs { url } }
  }
}"""

_MONTHS_ID = [
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]


def format_imdb_date(raw_date: str | None, locale: str = "id") -> str | None:
    if not raw_date:
        return None
    try:
        year, month, day = [int(part) for part in str(raw_date).split("-")]
        parsed = date(year, month, day)
    except Exception:
        return raw_date
    if locale == "id":
        return f"{parsed.day} {_MONTHS_ID[parsed.month - 1]} {parsed.year}"
    return parsed.strftime("%-d %B %Y")


async def _imdb_query(title_id: str, query: str):
    response = await fetch.post(
        IMDB_GRAPHQL_URL,
        headers=IMDB_GRAPHQL_HEADERS,
        json={
            "query": query,
            "operationName": "GetTitle",
            "variables": {"id": title_id},
        },
    )
    response.raise_for_status()
    return response.json()


async def get_imdb_details_graphql(title_id: str):
    title_id = title_id if str(title_id).startswith("tt") else f"tt{title_id}"
    body = {}
    try:
        body = await _imdb_query(title_id, IMDB_TITLE_QUERY)
    except Exception as err:
        LOGGER.warning(f"IMDb GraphQL primary query failed for {title_id}: {err}")

    payload = body.get("data", {}).get("title") or {}
    if not payload:
        if body.get("errors"):
            LOGGER.warning(f"IMDb GraphQL primary returned errors for {title_id}: {body.get('errors')}")
        try:
            body = await _imdb_query(title_id, IMDB_TITLE_QUERY_FALLBACK)
            payload = body.get("data", {}).get("title") or {}
        except Exception as err:
            LOGGER.warning(f"IMDb GraphQL fallback query failed for {title_id}: {err}")
            return {}

    if not payload:
        if body.get("errors"):
            LOGGER.warning(f"IMDb GraphQL returned errors for {title_id}: {body.get('errors')}")
        return {}

    principal_credits = payload.get("principalCredits") or []

    def _people(*categories):
        result = []
        for group in principal_credits:
            category = (group.get("category") or {}).get("text", "")
            if category not in categories:
                continue
            for credit in group.get("credits") or []:
                name_data = credit.get("name") or {}
                name_text = (name_data.get("nameText") or {}).get("text")
                person_id = name_data.get("id")
                if not name_text:
                    continue
                result.append({
                    "@type": "Person",
                    "name": name_text,
                    "url": f"https://www.imdb.com/name/{person_id}/" if person_id else "",
                })
        return result

    release_date = payload.get("releaseDate") or {}
    raw_date = None
    if release_date.get("year"):
        raw_date = f"{release_date.get('year')}-{release_date.get('month') or 1}-{release_date.get('day') or 1}"

    runtime_seconds = (payload.get("runtime") or {}).get("seconds")
    duration_text = f"{runtime_seconds // 60} min" if isinstance(runtime_seconds, int) and runtime_seconds > 0 else None

    total_nominations = ((payload.get("nominations") or {}).get("total") or 0)

    def _items_from_edges(container: dict | None) -> list[str]:
        if not isinstance(container, dict):
            return []
        return [
            (((edge or {}).get("node") or {}).get("text") or {}).get("plainText")
            for edge in container.get("edges", [])
            if (((edge or {}).get("node") or {}).get("text") or {}).get("plainText")
        ]

    trivia_items = _items_from_edges(payload.get("trivia"))
    goof_items = _items_from_edges(payload.get("goofs"))

    similar_titles = []
    for edge in (payload.get("moreLikeThisTitles") or {}).get("edges", []):
        node = (edge or {}).get("node") or {}
        title_text = (node.get("titleText") or {}).get("text")
        if not title_text:
            continue
        similar_titles.append({
            "id": node.get("id"),
            "title": title_text,
            "year": (node.get("releaseYear") or {}).get("year"),
            "rating": (node.get("ratingsSummary") or {}).get("aggregateRating"),
        })

    prestigious_award = payload.get("prestigiousAwardSummary") or {}
    prestigious_name = ((prestigious_award.get("award") or {}).get("text") or "").strip()
    prestigious_wins = prestigious_award.get("wins")
    prestigious_nominations = prestigious_award.get("nominations")

    award_nominations_total = ((payload.get("awardNominations") or {}).get("total"))
    total_wins = ((payload.get("wins") or {}).get("total"))

    # Prefer broader totals when available.
    if not isinstance(total_nominations, int):
        total_nominations = 0
    if isinstance(award_nominations_total, int) and award_nominations_total > total_nominations:
        total_nominations = award_nominations_total

    awards_parts = []
    if isinstance(total_wins, int) and total_wins > 0 and total_nominations > 0:
        awards_parts.append(f"{total_wins} wins & {total_nominations} nominations total")
    elif isinstance(total_wins, int) and total_wins > 0:
        awards_parts.append(f"{total_wins} wins total")
    elif total_nominations > 0:
        awards_parts.append(f"{total_nominations} nominations total")

    if prestigious_name:
        if isinstance(prestigious_wins, int) and prestigious_wins > 0:
            awards_parts.append(
                f"Won {prestigious_wins} {prestigious_name}{'' if prestigious_wins == 1 else 's'}"
            )
        if isinstance(prestigious_nominations, int) and prestigious_nominations > 0:
            awards_parts.append(
                f"Nominated for {prestigious_nominations} {prestigious_name}{'' if prestigious_nominations == 1 else 's'}"
            )

    awards_summary = "; ".join(awards_parts)

    return {
        "name": (payload.get("titleText") or {}).get("text"),
        "alternateName": (payload.get("originalTitleText") or {}).get("text"),
        "@type": (payload.get("titleType") or {}).get("text"),
        "releaseYear": (payload.get("releaseYear") or {}).get("year"),
        "datePublished": raw_date,
        "duration": duration_text,
        "inLanguage": [
            (item or {}).get("text")
            for item in (payload.get("spokenLanguages") or {}).get("spokenLanguages", [])
            if (item or {}).get("text")
        ],
        "countryOfOrigin": [
            (item or {}).get("text")
            for item in (payload.get("countriesOfOrigin") or {}).get("countries", [])
            if (item or {}).get("text")
        ],
        "contentRating": (payload.get("certificate") or {}).get("rating"),
        "aggregateRating": {
            "ratingValue": (payload.get("ratingsSummary") or {}).get("aggregateRating"),
            "ratingCount": (payload.get("ratingsSummary") or {}).get("voteCount"),
        },
        "genre": [
            (item or {}).get("text")
            for item in (payload.get("genres") or {}).get("genres", [])
            if (item or {}).get("text")
        ],
        "description": ((payload.get("plot") or {}).get("plotText") or {}).get("plainText"),
        "image": (payload.get("primaryImage") or {}).get("url"),
        "productionStatus": ((payload.get("productionStatus") or {}).get("currentProductionStage") or {}).get("text"),
        "totalNominations": total_nominations,
        "triviaItems": trivia_items,
        "goofItems": goof_items,
        "similarTitles": similar_titles,
        "awards": awards_summary,
        "trailer": (
            {"url": ((payload.get("latestTrailer") or {}).get("playbackURLs") or [{}])[0].get("url")}
            if ((payload.get("latestTrailer") or {}).get("playbackURLs") or [{}])[0].get("url")
            else None
        ),
        "keywords": ", ".join(
            (edge.get("node") or {}).get("text")
            for edge in (payload.get("keywords") or {}).get("edges", [])
            if (edge.get("node") or {}).get("text")
        ),
        "director": _people("Director"),
        "creator": _people("Writers", "Writer", "Creator"),
        "actor": _people("Stars", "Cast"),
    }
