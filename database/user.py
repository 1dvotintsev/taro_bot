from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User
from sqlalchemy import select
from datetime import datetime, timezone


async def register_user(
    session: AsyncSession,
    user_id: int,
    username: str,
) -> bool:
    """
    Пытается зарегистрировать пользователя.
    Если пользователя с таким user_id нет — создаёт и возвращает True.
    Если уже есть — ничего не меняет и возвращает False.
    """
    q = select(User).filter_by(id=user_id)
    result = await session.execute(q)
    user = result.scalar_one_or_none()

    if user:
        return False

    new_user = User(id=user_id, username=username)
    session.add(new_user)
    await session.commit()
    return True


async def check_active_subscription(
    session: AsyncSession,
    user_id: int
) -> bool:
    """
    Асинхронно подгружает subscription_end из БД и сравнивает с now.
    """
    result = await session.execute(
        select(User.subscription_end)
        .where(User.id == user_id)
    )
    sub_end = result.scalar_one_or_none()
    if sub_end is None:
        return False
    return sub_end > datetime.now(timezone.utc)


async def check_has_energy(
    session: AsyncSession,
    user_id: int
) -> bool:
    """
    Асинхронно подгружает energy из БД и проверяет >0.
    """
    result = await session.execute(
        select(User.energy)
        .where(User.id == user_id)
    )
    energy = result.scalar_one_or_none() or 0
    return energy > 0