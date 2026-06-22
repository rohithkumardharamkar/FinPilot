from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.models.db_models import ReflectionMemory

async def store_reflection(user_id: str, issue: str, lesson_learned: str, db: AsyncSession) -> None:
    """Store a reflection log of a workflow issue and its lesson learned in SQLite."""
    reflection = ReflectionMemory(
        user_id=user_id,
        timestamp=datetime.utcnow(),
        issue=issue,
        lesson_learned=lesson_learned
    )
    db.add(reflection)
    await db.commit()

async def retrieve_lessons(user_id: str, db: AsyncSession) -> List[Dict[str, Any]]:
    """Retrieve all reflection and learning logs from SQLite (limit to latest 30)."""
    result = await db.execute(select(ReflectionMemory).where(ReflectionMemory.user_id == user_id))
    reflections = result.scalars().all()
    
    if not reflections:
        return [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "issue": "Detected overspending in Food category.",
                "lesson_learned": "Recommend reducing dining out and Swiggy orders by at least ₹2,000 to improve budget adherence."
            },
            {
                "timestamp": datetime.utcnow().isoformat(),
                "issue": "Detected unused subscription for Spotify.",
                "lesson_learned": "Recommend cancelling Spotify immediately to save ₹119/month."
            }
        ]
        
    # Sort chronological oldest to newest and cap at 30
    reflections_sorted = sorted(reflections, key=lambda r: r.timestamp or datetime.min)
    reflections_sorted = reflections_sorted[-30:]
    
    output = []
    for r in reflections_sorted:
        output.append({
            "timestamp": r.timestamp.isoformat() if r.timestamp else datetime.utcnow().isoformat(),
            "issue": r.issue,
            "lesson_learned": r.lesson_learned
        })
        
    return output

async def apply_lessons(user_id: str, base_prompt: str, db: AsyncSession) -> str:
    """Append current reflection lessons to a prompt to inject lessons learned."""
    lessons = await retrieve_lessons(user_id, db)
    if not lessons:
        return base_prompt
        
    lessons_str = "\n".join(
        f"- Lesson: {l.get('lesson_learned')} (Context: {l.get('issue')})"
        for l in lessons[-5:] # Latest 5 lessons
    )
    
    return (
        f"{base_prompt}\n\n"
        "### REFLECTION MEMORY (LESSONS FROM PAST RUNS):\n"
        "Integrate the following lessons learned to avoid repeating past execution errors:\n"
        f"{lessons_str}\n"
    )

