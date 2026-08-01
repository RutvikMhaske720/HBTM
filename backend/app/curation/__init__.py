"""Profile-driven curation: turn who a user is into media they can actually open.

* `profile` — reads the identity graph and goals into a `UserProfile`, and
  builds the query vector everything else is measured against.
* `sources`  — one adapter per real content source, all returning the same
  candidate shape.
* `pipeline` — fetch, validate, gate on recency and semantic relevance,
  suppress near-duplicates, persist, and index into the vector database.
"""
