"""
MusikBOT — A Discord bot for playing music.
Entry point: loads environment, initializes the bot, and loads cogs.
"""

import os
import asyncio
import logging

import discord
from discord.ext import commands
from dotenv import load_dotenv

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(name)-20s │ %(levelname)-8s │ %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("musikbot")

# ─── Environment ──────────────────────────────────────────────────────────────
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if not DISCORD_TOKEN:
    raise RuntimeError(
        "DISCORD_TOKEN is not set. "
        "Copy .env.example to .env and fill in your bot token."
    )

# ─── Bot Setup ────────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.voice_states = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    description="🎵 MusikBOT — Your personal Discord DJ!",
)


@bot.event
async def on_ready():
    """Fires when the bot successfully connects to Discord."""
    logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    logger.info(f"Connected to {len(bot.guilds)} guild(s)")

    # Sync slash commands globally
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} slash command(s)")
    except Exception as e:
        logger.error(f"Failed to sync commands: {e}")

    # Set a rich presence
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name="/play 🎶",
        )
    )


async def main():
    """Load cogs and start the bot."""
    async with bot:
        await bot.load_extension("cogs.music")
        logger.info("Music cog loaded ✓")
        await bot.start(DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
