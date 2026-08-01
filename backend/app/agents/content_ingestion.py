"""Content Ingestion Agent — the entry point for pulling in fresh media.

Thin by design: profile resolution lives in `app.curation.profile`, source
adapters in `app.curation.sources`, and the filtering gates in
`app.curation.pipeline`. This module only decides *what to ask for*.
"""

from app.curation import pipeline
from app.curation.profile import UserProfile, build_profile
from app.db.database import Store


def fetch_more_like_this(
    db: Store,
    content_type: str,
    domain: str | None = None,
    max_results: int | None = None,
    user_id: str | None = None,
    profile: UserProfile | None = None,
) -> tuple[list[dict], dict]:
    """Curate a fresh batch of one medium for one user.

    Returns the persisted items plus the pipeline's rejection report, so the
    caller can tell "nothing matched you" apart from "the source was down".
    """
    resolved = profile or build_profile(db, user_id)
    return pipeline.curate(db, resolved, content_type, domain, max_results)
