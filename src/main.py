"""
Main entry point - bot initialization and startup.
"""
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import TELEGRAM_BOT_TOKEN, LOG_LEVEL
from handlers import router


def setup_logging():
    """Configure logging."""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )


async def main():
    """Main async entry point."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not set!")
        sys.exit(1)
    
    # Initialize bot with default properties
    bot = Bot(
        token=TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # Privacy mode can only be changed in @BotFather - without it the bot
    # sees only commands in groups, so auto-translation never triggers
    me = await bot.get_me()
    if not me.can_read_all_group_messages:
        logger.warning(
            "⚠️ Privacy mode is ON - bot will NOT see regular group messages. "
            "Fix: @BotFather -> /setprivacy -> @%s -> Disable, then remove and re-add the bot to the group.",
            me.username,
        )
    
    # Initialize dispatcher
    dp = Dispatcher()
    dp.include_router(router)

    # Log every incoming update - makes it obvious whether Telegram delivers anything
    @dp.update.outer_middleware()
    async def log_updates(handler, event, data):
        msg = event.message or event.channel_post
        if msg:
            logger.info(f"📩 {event.event_type} chat={msg.chat.id} ({msg.chat.type}) text={(msg.text or '')[:50]!r}")
        else:
            logger.info(f"📩 {event.event_type}")
        return await handler(event, data)

    logger.info("🚀 Bot starting...")
    
    try:
        # Start polling
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    asyncio.run(main())
