from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    UniqueConstraint,
    and_,
    or_,
    select,
    delete,
    func,
    text,
)
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("TRUE"))
    allowed_start_hour: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=text("0"))
    allowed_end_hour: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=text("24"))
    language_code: Mapped[str] = mapped_column(String(8), nullable=False, server_default=text("'ru'"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("allowed_start_hour >= 0 AND allowed_start_hour <= 24", name="chk_users_start_hour"),
        CheckConstraint("allowed_end_hour >= 0 AND allowed_end_hour <= 24", name="chk_users_end_hour"),
    )

    locations: Mapped[list["UserLocation"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )


class UserLocation(Base):
    __tablename__ = "user_locations"

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True
    )
    location_code: Mapped[str] = mapped_column(String(32), primary_key=True)

    user: Mapped[User] = relationship(back_populates="locations")

    __table_args__ = (
        UniqueConstraint("user_id", "location_code", name="uq_user_location"),
        Index("idx_user_locations_location", "location_code"),
    )


def _to_asyncpg_dsn(dsn: str) -> str:
    if dsn.startswith("postgresql+asyncpg://"):
        return dsn
    if dsn.startswith("postgresql://"):
        return "postgresql+asyncpg://" + dsn[len("postgresql://") :]
    return dsn


def create_engine(dsn: str) -> AsyncEngine:
    return create_async_engine(_to_asyncpg_dsn(dsn), pool_pre_ping=True)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


async def ensure_schema(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def _is_hour_allowed_sql(hour_param, start_col, end_col):
    # start == end -> exactly one hour (== start)
    # start < end  -> [start, end)
    # start > end  -> overnight window [start, 24) U [0, end)
    return or_(
        and_(start_col == end_col, hour_param == start_col),
        and_(start_col < end_col, hour_param >= start_col, hour_param < end_col),
        and_(start_col > end_col, or_(hour_param >= start_col, hour_param < end_col)),
    )


async def upsert_user(session: AsyncSession, user_id: int, *, language_code: Optional[str] = None) -> User:
    user = await session.get(User, user_id)
    if user is None:
        user = User(user_id=user_id)
        session.add(user)
        await session.flush()
    if language_code:
        user.language_code = language_code
    await session.commit()
    await session.refresh(user)
    return user


async def get_user(session: AsyncSession, user_id: int) -> Optional[User]:
    return await session.get(User, user_id)


async def set_notifications_enabled(session: AsyncSession, user_id: int, enabled: bool) -> None:
    user = await session.get(User, user_id)
    if user is None:
        user = User(user_id=user_id, notifications_enabled=enabled)
        session.add(user)
    else:
        user.notifications_enabled = enabled
    await session.commit()


async def set_notification_window(session: AsyncSession, user_id: int, start_hour: int, end_hour: int) -> None:
    if not (0 <= start_hour <= 24 and 0 <= end_hour <= 24):
        raise ValueError("start_hour and end_hour must be within 0..24")
    user = await session.get(User, user_id)
    if user is None:
        user = User(user_id=user_id, allowed_start_hour=start_hour, allowed_end_hour=end_hour)
        session.add(user)
    else:
        user.allowed_start_hour = start_hour
        user.allowed_end_hour = end_hour
    await session.commit()


async def add_location(session: AsyncSession, user_id: int, location_code: str) -> bool:
    user = await session.get(User, user_id)
    if user is None:
        user = User(user_id=user_id)
        session.add(user)
        await session.flush()

    from sqlalchemy import select
    exists_q = select(UserLocation).where(
        UserLocation.user_id == user_id, UserLocation.location_code == location_code
    )
    exists = (await session.execute(exists_q)).scalar_one_or_none()
    if exists:
        return False

    session.add(UserLocation(user_id=user_id, location_code=location_code))
    await session.commit()
    return True


async def remove_location(session: AsyncSession, user_id: int, location_code: str) -> bool:
    q = delete(UserLocation).where(UserLocation.user_id == user_id, UserLocation.location_code == location_code).execution_options(synchronize_session=False)
    res = await session.execute(q)
    await session.commit()
    return (res.rowcount or 0) > 0


async def get_user_locations(session: AsyncSession, user_id: int) -> set[str]:
    q = select(UserLocation.location_code).where(UserLocation.user_id == user_id)
    rows = await session.execute(q)
    return {str(code) for (code,) in rows.all()}


async def users_to_notify_for_location(session: AsyncSession, location_code: str, *, now_utc: Optional[datetime] = None) -> list[int]:
    if now_utc is None:
        now_utc = datetime.now(timezone.utc)
    hour = now_utc.hour

    u = User
    l = UserLocation
    q = select(u.user_id).join(l, l.user_id == u.user_id).where(
        u.notifications_enabled.is_(True),
        l.location_code == location_code,
        _is_hour_allowed_sql(hour, u.allowed_start_hour, u.allowed_end_hour),
    )
    rows = await session.execute(q)
    return [int(uid) for (uid,) in rows.all()]
