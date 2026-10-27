"""Database repository layer."""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import DownloadHistory, User


class UserRepository:
    """User CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        telegram_id: int,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        username: Optional[str] = None,
    ) -> tuple[User, bool]:
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            user.last_activity = datetime.now(timezone.utc)
            if first_name:
                user.first_name = first_name
            if last_name is not None:
                user.last_name = last_name
            if username is not None:
                user.username = username
            await self.session.flush()
            return user, False

        user = User(
            telegram_id=telegram_id,
            first_name=first_name,
            last_name=last_name,
            username=username,
            language="uz",
            last_activity=datetime.now(timezone.utc),
        )
        self.session.add(user)
        await self.session.flush()
        return user, True

    async def set_language(self, telegram_id: int, language: str) -> None:
        await self.session.execute(
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(language=language, updated_at=datetime.now(timezone.utc))
        )
        await self.session.flush()

    async def complete_onboarding(
        self,
        telegram_id: int,
        reason: Optional[str] = None,
        source: Optional[str] = None,
        skipped: bool = False,
    ) -> None:
        values = {
            "onboarding_completed": True,
            "onboarding_skipped": skipped,
            "updated_at": datetime.now(timezone.utc),
        }
        if reason is not None:
            values["reason_choice"] = reason
        if source is not None:
            values["source_choice"] = source
        await self.session.execute(
            update(User).where(User.telegram_id == telegram_id).values(**values)
        )
        await self.session.flush()

    async def reset_onboarding(self, telegram_id: int) -> None:
        await self.session.execute(
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(
                onboarding_completed=False,
                onboarding_skipped=False,
                reason_choice=None,
                source_choice=None,
                updated_at=datetime.now(timezone.utc),
            )
        )
        await self.session.flush()

    async def count_users(self) -> int:
        result = await self.session.execute(select(func.count(User.id)))
        return result.scalar_one()


class HistoryRepository:
    """Download history operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(
        self,
        user_id: int,
        platform: str,
        status: str,
        media_type: Optional[str] = None,
        error_category: Optional[str] = None,
        file_size: Optional[int] = None,
    ) -> DownloadHistory:
        record = DownloadHistory(
            user_id=user_id,
            platform=platform,
            media_type=media_type,
            status=status,
            error_category=error_category,
            file_size=file_size,
        )
        self.session.add(record)
        await self.session.flush()
        return record

    async def get_user_history(
        self, user_id: int, limit: int = 20
    ) -> List[DownloadHistory]:
        result = await self.session.execute(
            select(DownloadHistory)
            .where(DownloadHistory.user_id == user_id)
            .order_by(DownloadHistory.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def clear_user_history(self, user_id: int) -> int:
        result = await self.session.execute(
            delete(DownloadHistory).where(DownloadHistory.user_id == user_id)
        )
        await self.session.flush()
        return result.rowcount or 0

    async def count_total(self) -> int:
        result = await self.session.execute(select(func.count(DownloadHistory.id)))
        return result.scalar_one()

    async def count_by_status(self, status: str) -> int:
        result = await self.session.execute(
            select(func.count(DownloadHistory.id)).where(DownloadHistory.status == status)
        )
        return result.scalar_one()
