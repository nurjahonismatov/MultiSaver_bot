from aiogram import F, Router
from aiogram.types import CallbackQuery

from database.models import User
from database.repository import UserRepository
from database.session import async_session_factory
from keyboards.main_menu import main_menu_kb
from keyboards.onboarding import onboarding_q2_kb
from utils.i18n import get_text

router = Router(name="onboarding")


@router.callback_query(F.data.startswith("onb:q1:"))
async def onboarding_q1_answer(callback: CallbackQuery, db_user: User, lang: str) -> None:
    await callback.answer()
    choice = callback.data.split(":")[-1]

    async with async_session_factory() as session:
        repo = UserRepository(session)
        if choice == "later":
            await repo.complete_onboarding(db_user.telegram_id, skipped=True)
            await session.commit()
            await callback.message.answer(get_text("onboarding.skipped", lang))
            await callback.message.answer(
                get_text("start.main_menu", lang),
                reply_markup=main_menu_kb(lang),
            )
            return

        # Save reason and show Q2
        await repo.complete_onboarding(
            db_user.telegram_id,
            reason=choice,
            skipped=False,
        )
        # Note: we mark completed only after Q2 or skip; for now store reason
        # Actually re-set completed=False until Q2 done
        from sqlalchemy import update
        from database.models import User as UserModel
        from datetime import datetime, timezone

        await session.execute(
            update(UserModel)
            .where(UserModel.telegram_id == db_user.telegram_id)
            .values(
                reason_choice=choice,
                onboarding_completed=False,
                updated_at=datetime.now(timezone.utc),
            )
        )
        await session.commit()

    q2 = get_text("onboarding.q2", lang)
    await callback.message.answer(q2, reply_markup=onboarding_q2_kb(lang))


@router.callback_query(F.data.startswith("onb:q2:"))
async def onboarding_q2_answer(callback: CallbackQuery, db_user: User, lang: str) -> None:
    await callback.answer()
    choice = callback.data.split(":")[-1]

    async with async_session_factory() as session:
        repo = UserRepository(session)
        if choice == "later":
            await repo.complete_onboarding(
                db_user.telegram_id,
                source=None,
                skipped=False,
            )
            # Keep previous reason if any
            await session.commit()
            await callback.message.answer(get_text("onboarding.skipped", lang))
        else:
            await repo.complete_onboarding(
                db_user.telegram_id,
                source=choice,
                skipped=False,
            )
            await session.commit()
            await callback.message.answer(get_text("onboarding.thanks", lang))

    await callback.message.answer(
        get_text("start.main_menu", lang),
        reply_markup=main_menu_kb(lang),
    )
