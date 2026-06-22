from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.models.db_models import Preference

async def get_preferences(user_id: str, db: AsyncSession) -> Dict[str, str]:
    """Retrieve preferences as a key-value dictionary for a user."""
    stmt = select(Preference).where(Preference.user_id == user_id)
    res = await db.execute(stmt)
    prefs = res.scalars().all()
    return {p.preference_type: p.preference_value for p in prefs}

async def save_preference(
    user_id: str,
    preference_type: str,
    preference_value: str,
    db: AsyncSession
) -> Dict[str, Any]:
    """Create or update a user preference."""
    stmt = select(Preference).where(Preference.user_id == user_id, Preference.preference_type == preference_type)
    res = await db.execute(stmt)
    pref = res.scalar_one_or_none()
    if pref:
        pref.preference_value = preference_value
    else:
        pref = Preference(
            user_id=user_id,
            preference_type=preference_type,
            preference_value=preference_value
        )
        db.add(pref)
    await db.flush()
    return {
        "preference_type": pref.preference_type,
        "preference_value": pref.preference_value
    }

async def delete_preference(user_id: str, preference_type: str, db: AsyncSession) -> bool:
    """Delete a user preference."""
    stmt = select(Preference).where(Preference.user_id == user_id, Preference.preference_type == preference_type)
    res = await db.execute(stmt)
    pref = res.scalar_one_or_none()
    if not pref:
        return False
    await db.delete(pref)
    await db.flush()
    return True
