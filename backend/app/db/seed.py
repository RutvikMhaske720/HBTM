"""Synthetic Media Library seed data (spec section 2.6).

Not real licensed content — invented titles/descriptions standing in for
IABTM's curated library, tagged with domain/difficulty/mood/duration the
same way real editorial-tagged content would be, so the recommendation
engine has a real (if small) corpus to score and rank against.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.db.models import ContentItem
from app.embeddings.embedder import get_embedder

CONTENT_LIBRARY = [
    # Creativity
    {"title": "The Creative Habit", "content_type": "Print", "domain": "Creativity", "description": "A working method for turning creative impulse into daily practice, from a working choreographer.", "growth_potential_score": 0.82, "difficulty": "accessible", "duration_minutes": 240, "mood": "curious"},
    {"title": "Studio Ghibli Art Retrospective", "content_type": "Art", "domain": "Creativity", "description": "A visual survey of background painting and world-building technique across three decades of animation.", "growth_potential_score": 0.7, "difficulty": "accessible", "duration_minutes": 25, "mood": "curious"},
    {"title": "Sketchbook: 30 Days of Bad Drawings", "content_type": "Animation", "domain": "Creativity", "description": "A short-form series that reframes creative block as a practice problem, not a talent problem.", "growth_potential_score": 0.75, "difficulty": "accessible", "duration_minutes": 8, "mood": "energized"},
    {"title": "On Writing Badly First", "content_type": "Editorial", "domain": "Creativity", "description": "An essay on why first drafts are supposed to be embarrassing, and what to do about the fear that stops you starting.", "growth_potential_score": 0.68, "difficulty": "accessible", "duration_minutes": 12, "mood": "reflective"},
    {"title": "The Art Directors", "content_type": "Podcast", "domain": "Creativity", "description": "Working art directors talk through one real brief per episode, start to finish.", "growth_potential_score": 0.72, "difficulty": "challenging", "duration_minutes": 48, "mood": "curious"},
    # Mindset
    {"title": "Deep Work — Cal Newport (talk)", "content_type": "Podcast", "domain": "Mindset", "description": "A talk on cultivating the ability to focus without distraction on cognitively demanding tasks.", "growth_potential_score": 0.85, "difficulty": "accessible", "duration_minutes": 42, "mood": "motivated"},
    {"title": "Atomic Habits, Ch. 1–3", "content_type": "Editorial", "domain": "Mindset", "description": "An excerpt on identity-based habit change, and why small systems beat big goals.", "growth_potential_score": 0.8, "difficulty": "accessible", "duration_minutes": 20, "mood": "motivated"},
    {"title": "A Short Film About Discipline", "content_type": "Film", "domain": "Mindset", "description": "A quiet documentary short following an ultramarathon runner's daily routine.", "growth_potential_score": 0.77, "difficulty": "accessible", "duration_minutes": 16, "mood": "reflective"},
    {"title": "Stoicism for the Overwhelmed", "content_type": "Print", "domain": "Mindset", "description": "Practical Stoic exercises for people whose problem is too many open tabs, not too few ideas.", "growth_potential_score": 0.74, "difficulty": "accessible", "duration_minutes": 180, "mood": "reflective"},
    {"title": "The Procrastination Doom Loop", "content_type": "Podcast", "domain": "Mindset", "description": "A behavioral scientist breaks down why willpower isn't the fix for procrastination.", "growth_potential_score": 0.79, "difficulty": "accessible", "duration_minutes": 35, "mood": "curious"},
    # Health
    {"title": "Sleep Is Your Superpower", "content_type": "Editorial", "domain": "Health", "description": "A plain-language summary of sleep science and the three changes with the highest payoff.", "growth_potential_score": 0.83, "difficulty": "accessible", "duration_minutes": 10, "mood": "reflective"},
    {"title": "Zone 2: The Boring Cardio That Works", "content_type": "Podcast", "domain": "Health", "description": "Why low-intensity training builds the aerobic base everything else depends on.", "growth_potential_score": 0.71, "difficulty": "accessible", "duration_minutes": 40, "mood": "energized"},
    {"title": "Kitchen Reset: 10 Meals, No Recipes", "content_type": "Animation", "domain": "Health", "description": "An illustrated explainer on building meals from ratios instead of recipes.", "growth_potential_score": 0.65, "difficulty": "accessible", "duration_minutes": 9, "mood": "curious"},
    {"title": "The Body Keeps the Score, Ch. 1", "content_type": "Print", "domain": "Health", "description": "An introduction to how trauma reshapes the nervous system, and what recovery actually looks like.", "growth_potential_score": 0.78, "difficulty": "challenging", "duration_minutes": 200, "mood": "reflective"},
    {"title": "Out of Shape to 5K", "content_type": "Film", "domain": "Health", "description": "A short documentary following three total beginners through an eight-week running program.", "growth_potential_score": 0.7, "difficulty": "accessible", "duration_minutes": 22, "mood": "motivated"},
    # Knowledge
    {"title": "How Money Actually Moves", "content_type": "Animation", "domain": "Knowledge", "description": "An explainer series on the plumbing of the financial system, one pipe at a time.", "growth_potential_score": 0.73, "difficulty": "challenging", "duration_minutes": 14, "mood": "curious"},
    {"title": "A Field Guide to Bad Arguments", "content_type": "Editorial", "domain": "Knowledge", "description": "A tour of the ten most common logical fallacies, with examples pulled from real headlines.", "growth_potential_score": 0.69, "difficulty": "accessible", "duration_minutes": 15, "mood": "curious"},
    {"title": "The History of Nearly Everything (S1)", "content_type": "Podcast", "domain": "Knowledge", "description": "A single narrative thread connecting ten inventions that quietly reshaped daily life.", "growth_potential_score": 0.66, "difficulty": "accessible", "duration_minutes": 45, "mood": "curious"},
    {"title": "Statistics Without the Fear", "content_type": "Print", "domain": "Knowledge", "description": "An intuitive, low-math introduction to the statistical ideas that show up in every news article.", "growth_potential_score": 0.76, "difficulty": "challenging", "duration_minutes": 150, "mood": "focused"},
    # Career
    {"title": "The Unglamorous Path to Senior", "content_type": "Podcast", "domain": "Career", "description": "Three people who changed careers after 30 talk about what actually moved the needle.", "growth_potential_score": 0.81, "difficulty": "accessible", "duration_minutes": 50, "mood": "motivated"},
    {"title": "Negotiating Without Flinching", "content_type": "Editorial", "domain": "Career", "description": "A field-tested script for salary negotiation that doesn't rely on being naturally confrontational.", "growth_potential_score": 0.77, "difficulty": "accessible", "duration_minutes": 11, "mood": "focused"},
    {"title": "Portfolio Reviews: What Actually Gets You Hired", "content_type": "Film", "domain": "Career", "description": "Hiring managers react to real portfolios, live, unscripted.", "growth_potential_score": 0.72, "difficulty": "accessible", "duration_minutes": 30, "mood": "curious"},
    {"title": "So Good They Can't Ignore You, Ch. 2", "content_type": "Print", "domain": "Career", "description": "An argument against 'follow your passion' and for building rare, valuable skills instead.", "growth_potential_score": 0.8, "difficulty": "accessible", "duration_minutes": 25, "mood": "motivated"},
    # Relationships
    {"title": "The Four Horsemen, Explained", "content_type": "Animation", "domain": "Relationships", "description": "An illustrated breakdown of the communication patterns that predict relationship breakdown — and their antidotes.", "growth_potential_score": 0.79, "difficulty": "accessible", "duration_minutes": 12, "mood": "reflective"},
    {"title": "Attached, Ch. 1–2", "content_type": "Print", "domain": "Relationships", "description": "An accessible introduction to attachment theory and what it predicts about how you show up in relationships.", "growth_potential_score": 0.75, "difficulty": "accessible", "duration_minutes": 90, "mood": "reflective"},
    {"title": "Conversations That Repair", "content_type": "Podcast", "domain": "Relationships", "description": "A therapist walks through what an actual repair conversation sounds like after conflict.", "growth_potential_score": 0.74, "difficulty": "challenging", "duration_minutes": 38, "mood": "reflective"},
    # Finance
    {"title": "The Boring Index Fund Talk", "content_type": "Podcast", "domain": "Finance", "description": "Why the least exciting investment strategy is also the one with the best long-run evidence.", "growth_potential_score": 0.7, "difficulty": "accessible", "duration_minutes": 33, "mood": "focused"},
    {"title": "Your First Budget That Actually Sticks", "content_type": "Editorial", "domain": "Finance", "description": "A budgeting method built around one weekly 10-minute check-in instead of constant tracking.", "growth_potential_score": 0.73, "difficulty": "accessible", "duration_minutes": 9, "mood": "motivated"},
    {"title": "Debt Free at 34", "content_type": "Film", "domain": "Finance", "description": "A short documentary profile of one household's three-year debt payoff, mistakes included.", "growth_potential_score": 0.68, "difficulty": "accessible", "duration_minutes": 19, "mood": "motivated"},
    # Purpose
    {"title": "A Short Film About Discipline: Part II", "content_type": "Film", "domain": "Purpose", "description": "A follow-up documentary on what happens after the streak ends and the habit has to survive without motivation.", "growth_potential_score": 0.78, "difficulty": "accessible", "duration_minutes": 18, "mood": "reflective"},
    {"title": "Man's Search for Meaning, Ch. 1", "content_type": "Print", "domain": "Purpose", "description": "An introduction to logotherapy and the idea that meaning, not happiness, is the primary human drive.", "growth_potential_score": 0.86, "difficulty": "challenging", "duration_minutes": 120, "mood": "reflective"},
    {"title": "Ikigai, Without the Buzzwords", "content_type": "Editorial", "domain": "Purpose", "description": "A skeptical, practical look at the ikigai framework and what's actually useful in it.", "growth_potential_score": 0.71, "difficulty": "accessible", "duration_minutes": 13, "mood": "curious"},
    {"title": "Vocation Interviews, Vol. 3", "content_type": "Podcast", "domain": "Purpose", "description": "Long-form conversations with people mid-career-change about how they knew it was time.", "growth_potential_score": 0.75, "difficulty": "accessible", "duration_minutes": 55, "mood": "reflective"},
    # A few explicitly-flagged low-quality items so the Safety Agent has something to catch
    {"title": "10 SHOCKING Productivity Hacks Gurus Hide From You", "content_type": "Animation", "domain": "Mindset", "description": "Rapid-fire engagement-bait listicle with no sourcing, optimized for watch-time not comprehension.", "growth_potential_score": 0.12, "difficulty": "accessible", "duration_minutes": 6, "mood": "energized"},
    {"title": "Get Rich Quick With This One Weird Trick", "content_type": "Editorial", "domain": "Finance", "description": "Unsourced miracle-return investment claims with no risk disclosure.", "growth_potential_score": 0.05, "difficulty": "accessible", "duration_minutes": 4, "mood": "energized"},
]


def seed_content_library(db: Session) -> int:
    existing = db.query(ContentItem).count()
    if existing > 0:
        return 0

    embedder = get_embedder()
    embedder.fit([f"{c['title']} {c['description']}" for c in CONTENT_LIBRARY])

    now = datetime.now(timezone.utc)
    for i, item in enumerate(CONTENT_LIBRARY):
        embedding = embedder.embed_text(f"{item['title']} {item['description']}")
        db.add(
            ContentItem(
                title=item["title"],
                content_type=item["content_type"],
                domain=item["domain"],
                description=item["description"],
                growth_potential_score=item["growth_potential_score"],
                difficulty=item["difficulty"],
                duration_minutes=item["duration_minutes"],
                mood=item["mood"],
                source="internal",
                published_at=now - timedelta(days=i * 3),
                embedding=embedding,
            )
        )
    db.commit()
    return len(CONTENT_LIBRARY)
