"""Users router — onboarding, profile CRUD, and GDPR export."""

from fastapi import APIRouter, Depends, HTTPException

from app.api.schemas import (
    OnboardingPayload,
    OnboardingResponse,
    ProfileUpdatePayload,
    UserOut,
)
from app.db.database import Store, get_db
from app.db.models import new_goal, new_identity_node, new_user

router = APIRouter(prefix="/api/v1", tags=["users"])


# ─── Onboarding ───────────────────────────────────────────────────────────────

@router.post("/onboarding", response_model=OnboardingResponse, status_code=201)
def onboard_user(payload: OnboardingPayload, db: Store = Depends(get_db)):
    """
    Create user + seed Identity Graph + seed Goals from onboarding wizard.
    Returns the new user_id so the frontend can store it in state.
    """
    user = new_user(
        id=payload.user_id,
        name=payload.name,
        profile_name=payload.profile_name,
        email=payload.email,
        phone=payload.phone,
    )
    db.users.upsert(user)

    # Build identity graph nodes
    graph_patch: list[dict] = []
    for label in payload.current_self:
        graph_patch.append({"node_type": "archetype", "label": label, "weight": 1.0, "polarity": "current", "source": "self_declared"})
    for label in payload.imagined_self:
        graph_patch.append({"node_type": "archetype", "label": label, "weight": 1.0, "polarity": "imagined", "source": "self_declared"})
    for label in payload.learning_styles:
        graph_patch.append({"node_type": "habit", "label": label, "weight": 0.8, "polarity": "current", "source": "self_declared"})
    for label in payload.media_types:
        graph_patch.append({"node_type": "trait", "label": f"Prefers {label}", "weight": 0.7, "polarity": "current", "source": "self_declared"})

    # Free-text "in your own words" notes — richer signal than pills alone,
    # stored as a distinct node_type so the Identity page can render them as
    # prose instead of squeezing a paragraph into a pill, and so the
    # Identity Agent can fold them into the embedding-driving summary.
    if payload.current_self_notes.strip():
        graph_patch.append({"node_type": "narrative", "label": payload.current_self_notes.strip()[:500], "weight": 0.9, "polarity": "current", "source": "self_declared"})
    if payload.imagined_self_notes.strip():
        graph_patch.append({"node_type": "narrative", "label": payload.imagined_self_notes.strip()[:500], "weight": 0.9, "polarity": "imagined", "source": "self_declared"})

    for entry in graph_patch:
        db.identity_nodes.upsert(new_identity_node(
            user_id=user["id"],
            node_type=entry["node_type"],
            label=entry["label"],
            weight=entry["weight"],
            polarity=entry["polarity"],
            source=entry["source"],
        ))

    # Build goals — pair goal titles with domains
    goal_domains = payload.goal_domains or []
    for i, goal_title in enumerate(payload.goals):
        domain = goal_domains[i] if i < len(goal_domains) else "Knowledge"
        db.goals.upsert(new_goal(
            user_id=user["id"],
            domain=domain,
            title=goal_title,
            timeline=payload.timeline,
            progress=0.0,
            status="active",
        ))

    return OnboardingResponse(user_id=user["id"], name=user["name"])


# ─── Profile ──────────────────────────────────────────────────────────────────

@router.get("/me/{user_id}", response_model=UserOut)
def get_profile(user_id: str, db: Store = Depends(get_db)):
    user = db.users.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserOut(
        id=user["id"],
        name=user["name"],
        profile_name=user["profile_name"],
        email=user["email"],
        photo_url=user["photo_url"],
        created_at=user["created_at"],
    )


@router.patch("/me/{user_id}", response_model=UserOut)
def update_profile(user_id: str, payload: ProfileUpdatePayload, db: Store = Depends(get_db)):
    user = db.users.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.name is not None:
        user["name"] = payload.name
    if payload.profile_name is not None:
        user["profile_name"] = payload.profile_name
    if payload.email is not None:
        user["email"] = payload.email
    if payload.photo_url is not None:
        user["photo_url"] = payload.photo_url
    db.users.upsert(user)
    return UserOut(
        id=user["id"],
        name=user["name"],
        profile_name=user["profile_name"],
        email=user["email"],
        photo_url=user["photo_url"],
        created_at=user["created_at"],
    )
