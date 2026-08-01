"""The user profile, and the search intent derived from it.

Everything the curator fetches starts here. A `UserProfile` carries two
representations of the same person:

* `profile_text` / `terms` — the lexical view, used to build search queries
  and to sanity-check that a candidate mentions anything the user cares about;
* `vector` — the semantic view, used to rank and to reject.

Queries are built per (content type, domain) rather than one query per user,
because "run a first 5K" should reach different corners of YouTube, Open
Library and the open web, and a single blended query reaches none of them well.
"""

from dataclasses import dataclass, field

from app.db.database import Store
from app.mcp_tools import internal_db, semantic_search

DEFAULT_DOMAINS = ["Mindset", "Health", "Creativity"]

# What each medium is *for*, per growth domain. Without this a Music query for
# a Health goal returns songs about running rather than something to run to.
_MUSIC_INTENT = {
    "Mindset": "calm focus instrumental for deep concentration",
    "Creativity": "instrumental music for creative flow and studio work",
    "Health": "high energy workout music to train to",
    "Knowledge": "ambient study music for long reading sessions",
    "Career": "focus music for deep work sessions",
    "Relationships": "warm reflective acoustic music",
    "Finance": "steady focus music for planning and admin work",
    "Purpose": "reflective ambient music for journaling and thinking",
}

# A goal is written as a personal commitment ("Finish one long-form resource a
# month"), which is a statement, not a search query — sent verbatim to a video
# API it matches almost nothing and the ranking fills with noise. Pairing it
# with the domain's subject vocabulary is what makes the search land.
_TOPIC_INTENT = {
    "Mindset": "discipline focus and mental habits",
    "Creativity": "creative practice and craft technique",
    "Health": "training movement and nutrition guidance",
    "Knowledge": "learning techniques deep reading and study skills",
    "Career": "career skills and professional growth",
    "Relationships": "communication and relationship skills",
    "Finance": "personal finance planning and investing basics",
    "Purpose": "finding direction and meaningful work",
}

# Open Library subject headings per domain. Its `subject=` index is far more
# precise than free-text search (see `open_library.search_books`), but only
# for terms that exist as headings — so these are chosen to be real ones.
PRINT_SUBJECTS = {
    "Mindset": "self-actualization",
    "Creativity": "creative ability",
    "Health": "physical fitness",
    "Knowledge": "study skills",
    "Career": "career development",
    "Relationships": "interpersonal relations",
    "Finance": "personal finance",
    "Purpose": "self-realization",
}

_ART_INTENT = {
    "Mindset": "minimalist contemplative art",
    "Creativity": "contemporary illustration and studio practice",
    "Health": "movement and human form in art",
    "Knowledge": "scientific illustration and data art",
    "Career": "workspace and craft photography",
    "Relationships": "portrait photography of people together",
    "Finance": "architectural and geometric composition",
    "Purpose": "landscape and horizon photography",
}

# Publishers that answer a keyword search through their own RSS
# (`?s=<query>&feed=rss2`). This is the query-driven scraping channel: general
# search engines captcha-gate automated traffic, so asking each curated
# publisher directly is what makes Editorial results track a specific goal
# rather than just being whatever a magazine published this week.
# Every host here was verified to return search results in this form.
DOMAIN_SEARCH_SITES = {
    "Mindset": ["nesslabs.com", "jamesclear.com", "www.developgoodhabits.com", "sloww.co"],
    "Creativity": ["www.thisiscolossal.com", "austinkleon.com"],
    "Health": ["nutritionfacts.org", "www.precisionnutrition.com", "www.marathonhandbook.com"],
    # Big Think answers 403 to any non-browser client, so its pages can never
    # be previewed and it is not listed here.
    "Knowledge": ["collegeinfogeek.com", "nesslabs.com", "www.themarginalian.org"],
    "Career": ["careersidekick.com", "asianefficiency.com"],
    "Relationships": ["www.gottman.com", "tinybuddha.com"],
    "Finance": ["ofdollarsanddata.com", "affordanything.com"],
    "Purpose": ["www.themarginalian.org", "sloww.co"],
}

# Plain "latest posts" feeds per domain — the freshness floor, used alongside
# the search feeds so a shelf is never empty just because a query was narrow.
DOMAIN_FEEDS = {
    "Mindset": [
        "https://psyche.co/feed",
        "https://fs.blog/feed/",
        "https://nesslabs.com/feed",
    ],
    "Creativity": [
        "https://www.thisiscolossal.com/feed/",
        "https://austinkleon.com/feed/",
        "https://aeon.co/feed.rss",
    ],
    "Health": [
        "https://www.health.harvard.edu/blog/feed",
        "https://www.outsideonline.com/feed/",
    ],
    "Knowledge": [
        "https://www.quantamagazine.org/feed/",
        "https://aeon.co/feed.rss",
        "https://arstechnica.com/feed/",
    ],
    "Career": [
        "https://review.firstround.com/feed.xml",
        "https://80000hours.org/feed/",
    ],
    "Relationships": [
        "https://greatergood.berkeley.edu/feeds/all.rss",
        "https://psyche.co/feed",
    ],
    "Finance": [
        "https://ofdollarsanddata.com/feed/",
        "https://www.morningstar.com/feeds/articles.rss",
    ],
    "Purpose": [
        "https://www.themarginalian.org/feed/",
        "https://psyche.co/feed",
        "https://aeon.co/feed.rss",
    ],
}


@dataclass
class UserProfile:
    user_id: str
    identity_summary: str = ""
    traits: list[str] = field(default_factory=list)
    aspirations: list[str] = field(default_factory=list)
    goals: list[dict] = field(default_factory=list)
    media_preferences: list[str] = field(default_factory=list)
    feedback_history: list[dict] = field(default_factory=list)
    vector: list[float] = field(default_factory=list)

    @property
    def domains(self) -> list[str]:
        """Goal domains, in declaration order, falling back to sane defaults."""
        seen = list(dict.fromkeys(goal["domain"] for goal in self.goals if goal.get("domain")))
        return seen or DEFAULT_DOMAINS

    @property
    def goal_titles(self) -> list[str]:
        return [goal["title"] for goal in self.goals if goal.get("title")]

    @property
    def profile_text(self) -> str:
        parts = [
            self.identity_summary,
            " ".join(self.goal_titles),
            " ".join(self.domains),
            " ".join(self.aspirations),
        ]
        return " ".join(part for part in parts if part).strip()

    @property
    def terms(self) -> set[str]:
        """Lowercased content words from the profile, for lexical overlap."""
        raw = self.profile_text.lower().replace("/", " ").replace(",", " ").replace(".", " ")
        return {word for word in raw.split() if len(word) > 3}

    def goals_in(self, domain: str) -> list[dict]:
        return [goal for goal in self.goals if goal.get("domain") == domain]


def build_profile(db: Store, user_id: str | None) -> UserProfile:
    """Load a user's identity, goals and feedback into one object.

    With no `user_id` (an anonymous library browse) this returns an empty
    profile whose vector is empty — callers treat that as "no relevance gate
    is possible" and fall back to domain-scoped queries.
    """
    if not user_id:
        return UserProfile(user_id="")

    graph = internal_db.get_identity_graph(db, user_id)
    goals = [
        {"domain": goal["domain"], "title": goal["title"]}
        for goal in db.goals.filter(lambda goal: goal["user_id"] == user_id and goal["status"] == "active")
    ]
    feedback = internal_db.get_feedback_history(db, user_id, time_range_days=180)

    traits, aspirations, media_preferences, narratives = [], [], [], []
    for node in sorted(graph["nodes"], key=lambda node: node["weight"], reverse=True):
        label = node["label"]
        if node["type"] == "narrative":
            narratives.append(label)
        elif label.startswith("Prefers "):
            media_preferences.append(label.removeprefix("Prefers "))
        elif node["polarity"] == "imagined":
            aspirations.append(label)
        else:
            traits.append(label)

    summary = " ".join(
        part for part in [
            f"Currently: {', '.join(traits)}." if traits else "",
            f"Working toward: {', '.join(aspirations)}." if aspirations else "",
            " ".join(narratives),
        ] if part
    )

    profile = UserProfile(
        user_id=user_id,
        identity_summary=summary,
        traits=traits,
        aspirations=aspirations,
        goals=goals,
        media_preferences=media_preferences,
        feedback_history=feedback,
    )
    profile.vector = semantic_search.build_user_query_vector(
        summary, [f"{goal['domain']} {goal['title']}" for goal in goals] or ["personal growth"],
        db=db, feedback_history=feedback,
    )
    semantic_search.save_user_vector(user_id, profile.vector, {"domains": profile.domains})
    return profile


def build_queries(profile: UserProfile, content_type: str, domain: str, limit: int = 3) -> list[str]:
    """Search strings for one medium in one domain, most specific first.

    The first query is always anchored to a concrete goal when one exists —
    that is what makes results specific to this user rather than to the
    domain in general.
    """
    goals = profile.goals_in(domain) or profile.goals
    goal_titles = [goal["title"] for goal in goals if goal.get("title")][:2]
    aspiration = profile.aspirations[0] if profile.aspirations else ""
    topic = _TOPIC_INTENT.get(domain, f"{domain.lower()} personal growth")
    queries: list[str] = []

    if content_type == "Music":
        intent = _MUSIC_INTENT.get(domain, "focus music")
        queries = [intent, f"{intent} playlist", f"{domain.lower()} {intent}"]
    elif content_type == "Art":
        intent = _ART_INTENT.get(domain, "contemporary art")
        queries = [intent] + [f"{title} {intent}" for title in goal_titles]
    elif content_type == "Animation":
        queries = [f"{topic} animated short film"]
        queries += [f"{title} animated short" for title in goal_titles]
    elif content_type == "Print":
        # Book search matches titles and subjects, so the subject vocabulary
        # is more useful here than the user's phrasing of their goal.
        queries = [topic]
        queries += [f"{title}" for title in goal_titles]
        if aspiration:
            queries.append(f"{aspiration} {domain.lower()}")
    elif content_type == "Podcast":
        queries = [f"{topic} podcast"]
        queries += [f"{title} podcast" for title in goal_titles]
    elif content_type == "Editorial":
        queries = [f"{topic} evidence based guide"]
        queries += list(goal_titles)
    else:  # Videos, and anything new that hasn't been given an intent yet
        queries = [f"{title} {topic}" for title in goal_titles]
        queries.append(f"how to improve {topic}")
        if aspiration:
            queries.append(f"{aspiration} {domain.lower()}")

    cleaned = [" ".join(query.split()) for query in queries if query and query.strip()]
    return list(dict.fromkeys(cleaned))[:limit] or [f"{domain} personal growth"]
