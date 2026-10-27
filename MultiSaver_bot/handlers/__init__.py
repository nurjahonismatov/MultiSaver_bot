from aiogram import Router

from handlers import admin, download, help, history, language, media_actions, onboarding, settings, start


def setup_routers() -> Router:
    root = Router()
    # BUYRUQLAR BIRINCHI
    root.include_router(start.router)
    root.include_router(help.router)
    root.include_router(language.router)
    root.include_router(history.router)
    root.include_router(settings.router)
    root.include_router(onboarding.router)
    root.include_router(media_actions.router)
    root.include_router(admin.router)
    # HAVOLA OXIRIDA
    root.include_router(download.router)
    return root