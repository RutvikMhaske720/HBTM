"""Identity router — graph and summary."""

from fastapi import APIRouter, Depends

from app.api.schemas import IdentityGraphOut, IdentityNodeOut
from app.db.database import Store, get_db
from app.mcp_tools import internal_db

router = APIRouter(prefix="/api/v1/identity", tags=["identity"])


@router.get("/{user_id}/graph", response_model=IdentityGraphOut)
def get_identity_graph(user_id: str, db: Store = Depends(get_db)):
    graph = internal_db.get_identity_graph(db, user_id)
    nodes = [
        IdentityNodeOut(
            id=n["id"],
            node_type=n["type"],
            label=n["label"],
            weight=n["weight"],
            source=n["source"],
            polarity=n["polarity"],
        )
        for n in graph["nodes"]
    ]
    return IdentityGraphOut(user_id=user_id, nodes=nodes, edges=graph["edges"])


@router.get("/{user_id}/summary")
def get_identity_summary(user_id: str, db: Store = Depends(get_db)):
    graph = internal_db.get_identity_graph(db, user_id)
    current = [n for n in graph["nodes"] if n["polarity"] == "current"]
    imagined = [n for n in graph["nodes"] if n["polarity"] == "imagined"]

    current_labels = [n["label"] for n in sorted(current, key=lambda x: x["weight"], reverse=True)]
    imagined_labels = [n["label"] for n in sorted(imagined, key=lambda x: x["weight"], reverse=True)]

    if current_labels and imagined_labels:
        summary = (
            f"Current self is shaped by: {', '.join(current_labels[:5])}. "
            f"Imagined self reaches toward: {', '.join(imagined_labels[:5])}."
        )
    elif current_labels:
        summary = f"Current self: {', '.join(current_labels[:5])}."
    else:
        summary = "No identity signal yet."

    return {"user_id": user_id, "summary": summary, "node_count": len(graph["nodes"])}
