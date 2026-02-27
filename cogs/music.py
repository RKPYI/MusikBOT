"""
Music cog for MusikBOT.
Provides slash commands for playing, pausing, skipping, and managing a music queue.
"""
import asyncio
import logging
from collections import deque
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from utils.music_sources import (
    resolve_query,
    TrackInfo,
    MusicSourceError,
    FFMPEG_OPTIONS,
)

logger = logging.getLogger("musikbot.music")

# ─── Embed Colors ────────────────────────────────────────────────────────────
COLOR_PLAYING = 0x1DB954   # Spotify green
COLOR_QUEUED = 0x5865F2     # Discord blurple
COLOR_ERROR = 0xED4245      # Red
COLOR_INFO = 0xFEE75C       # Yellow


class GuildMusicState:
    """Per-guild state for music playback."""

    def __init__(self):
        self.queue: deque[TrackInfo] = deque()
        self.current: Optional[TrackInfo] = None
        self.voice_client: Optional[discord.VoiceClient] = None
        self.volume: float = 0.5
        self.loop: bool = False
        self._play_next_event = asyncio.Event()

    def clear(self):
        self.queue.clear()
        self.current = None
        self.loop = False


class Music(commands.Cog):
    """🎵 Music commands for MusikBOT."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.states: dict[int, GuildMusicState] = {}

    def _get_state(self, guild_id: int) -> GuildMusicState:
        """Get or create the music state for a guild."""
        if guild_id not in self.states:
            self.states[guild_id] = GuildMusicState()
        return self.states[guild_id]

    # ─── Helpers ──────────────────────────────────────────────────────────────

    def _make_now_playing_embed(self, track: TrackInfo) -> discord.Embed:
        """Create a 'Now Playing' embed."""
        embed = discord.Embed(
            title="🎶 Now Playing",
            description=f"**[{track.title}]({track.url})**",
            color=COLOR_PLAYING,
        )
        embed.add_field(name="Duration", value=track.duration_str, inline=True)
        if track.requester:
            embed.add_field(name="Requested by", value=track.requester, inline=True)
        if track.thumbnail:
            embed.set_thumbnail(url=track.thumbnail)
        return embed

    def _make_queued_embed(self, track: TrackInfo, position: int) -> discord.Embed:
        """Create a 'Added to Queue' embed."""
        embed = discord.Embed(
            title="📋 Added to Queue",
            description=f"**[{track.title}]({track.url})**",
            color=COLOR_QUEUED,
        )
        embed.add_field(name="Position", value=str(position), inline=True)
        embed.add_field(name="Duration", value=track.duration_str, inline=True)
        if track.thumbnail:
            embed.set_thumbnail(url=track.thumbnail)
        return embed

    def _make_error_embed(self, message: str) -> discord.Embed:
        """Create an error embed."""
        return discord.Embed(
            title="❌ Error",
            description=message,
            color=COLOR_ERROR,
        )

    async def _ensure_voice(
        self, interaction: discord.Interaction
    ) -> Optional[discord.VoiceClient]:
        """Ensure the bot is in the user's voice channel. Returns VoiceClient or None."""
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.followup.send(
                embed=self._make_error_embed("You need to be in a voice channel!"),
                ephemeral=True,
            )
            return None

        channel = interaction.user.voice.channel
        state = self._get_state(interaction.guild_id)

        if state.voice_client and state.voice_client.is_connected():
            if state.voice_client.channel.id != channel.id:
                await state.voice_client.move_to(channel)
            return state.voice_client

        try:
            vc = await channel.connect(self_deaf=True)
            state.voice_client = vc
            return vc
        except Exception as e:
            logger.error(f"Failed to connect to voice channel: {e}")
            await interaction.followup.send(
                embed=self._make_error_embed(f"Could not join the voice channel: {e}"),
                ephemeral=True,
            )
            return None

    def _play_next(self, guild_id: int, error=None):
        """Callback after a track finishes. Plays the next track in the queue."""
        if error:
            logger.error(f"Player error: {error}")

        state = self._get_state(guild_id)

        # If looping, re-add the current track
        if state.loop and state.current:
            state.queue.appendleft(state.current)

        if not state.queue:
            state.current = None
            # Schedule auto-disconnect after 2 minutes of inactivity
            asyncio.run_coroutine_threadsafe(
                self._auto_disconnect(guild_id), self.bot.loop
            )
            return

        next_track = state.queue.popleft()
        state.current = next_track

        try:
            source = discord.PCMVolumeTransformer(
                discord.FFmpegPCMAudio(next_track.stream_url, **FFMPEG_OPTIONS),
                volume=state.volume,
            )
            state.voice_client.play(
                source,
                after=lambda e: self._play_next(guild_id, e),
            )
        except Exception as e:
            logger.error(f"Failed to play next track: {e}")
            self._play_next(guild_id)

    async def _auto_disconnect(self, guild_id: int):
        """Disconnect from voice after 2 minutes of inactivity."""
        await asyncio.sleep(120)
        state = self._get_state(guild_id)
        if (
            state.voice_client
            and state.voice_client.is_connected()
            and not state.voice_client.is_playing()
            and not state.voice_client.is_paused()
        ):
            await state.voice_client.disconnect()
            state.voice_client = None
            state.clear()
            logger.info(f"Auto-disconnected from guild {guild_id}")

    # ─── Slash Commands ───────────────────────────────────────────────────────

    @app_commands.command(name="play", description="Play a song from YouTube or search by name")
    @app_commands.describe(query="YouTube URL or search query")
    async def play(self, interaction: discord.Interaction, query: str):
        """Play a track or add it to the queue."""
        await interaction.response.defer()

        vc = await self._ensure_voice(interaction)
        if not vc:
            return

        state = self._get_state(interaction.guild_id)

        # Resolve the query (YouTube URL or search)
        try:
            track = await resolve_query(query)
        except MusicSourceError as e:
            await interaction.followup.send(embed=self._make_error_embed(str(e)))
            return

        if not track:
            await interaction.followup.send(
                embed=self._make_error_embed(f"No results found for: **{query}**")
            )
            return

        track.requester = interaction.user.display_name

        if vc.is_playing() or vc.is_paused():
            # Add to queue
            state.queue.append(track)
            await interaction.followup.send(
                embed=self._make_queued_embed(track, len(state.queue))
            )
        else:
            # Play immediately
            state.current = track
            source = discord.PCMVolumeTransformer(
                discord.FFmpegPCMAudio(track.stream_url, **FFMPEG_OPTIONS),
                volume=state.volume,
            )
            vc.play(
                source,
                after=lambda e: self._play_next(interaction.guild_id, e),
            )
            await interaction.followup.send(
                embed=self._make_now_playing_embed(track)
            )

    @app_commands.command(name="skip", description="Skip the current track")
    async def skip(self, interaction: discord.Interaction):
        """Skip the currently playing track."""
        state = self._get_state(interaction.guild_id)

        if not state.voice_client or not state.voice_client.is_playing():
            await interaction.response.send_message(
                embed=self._make_error_embed("Nothing is playing right now."),
                ephemeral=True,
            )
            return

        state.voice_client.stop()  # Triggers _play_next via the after callback
        await interaction.response.send_message(
            embed=discord.Embed(
                title="⏭️ Skipped",
                description=f"Skipped **{state.current.title}**" if state.current else "Skipped.",
                color=COLOR_INFO,
            )
        )

    @app_commands.command(name="queue", description="Show the current music queue")
    async def queue(self, interaction: discord.Interaction):
        """Display the current queue."""
        state = self._get_state(interaction.guild_id)

        if not state.current and not state.queue:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="📋 Queue",
                    description="The queue is empty. Use `/play` to add songs!",
                    color=COLOR_INFO,
                ),
                ephemeral=True,
            )
            return

        lines = []
        if state.current:
            lines.append(f"🎶 **Now Playing:** {state.current.title} [{state.current.duration_str}]")
            lines.append("")

        if state.queue:
            lines.append("**Up Next:**")
            for i, track in enumerate(list(state.queue)[:10], 1):
                lines.append(f"`{i}.` {track.title} [{track.duration_str}]")

            if len(state.queue) > 10:
                lines.append(f"\n*...and {len(state.queue) - 10} more*")
        else:
            lines.append("*No more tracks in queue.*")

        embed = discord.Embed(
            title="📋 Queue",
            description="\n".join(lines),
            color=COLOR_QUEUED,
        )
        embed.set_footer(text=f"Volume: {int(state.volume * 100)}%")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="pause", description="Pause the current track")
    async def pause(self, interaction: discord.Interaction):
        """Pause playback."""
        state = self._get_state(interaction.guild_id)

        if not state.voice_client or not state.voice_client.is_playing():
            await interaction.response.send_message(
                embed=self._make_error_embed("Nothing is playing right now."),
                ephemeral=True,
            )
            return

        state.voice_client.pause()
        await interaction.response.send_message(
            embed=discord.Embed(title="⏸️ Paused", color=COLOR_INFO)
        )

    @app_commands.command(name="resume", description="Resume the paused track")
    async def resume(self, interaction: discord.Interaction):
        """Resume playback."""
        state = self._get_state(interaction.guild_id)

        if not state.voice_client or not state.voice_client.is_paused():
            await interaction.response.send_message(
                embed=self._make_error_embed("Nothing is paused right now."),
                ephemeral=True,
            )
            return

        state.voice_client.resume()
        await interaction.response.send_message(
            embed=discord.Embed(title="▶️ Resumed", color=COLOR_PLAYING)
        )

    @app_commands.command(name="stop", description="Stop playback, clear queue, and leave")
    async def stop(self, interaction: discord.Interaction):
        """Stop everything and disconnect."""
        state = self._get_state(interaction.guild_id)

        if state.voice_client:
            state.voice_client.stop()
            await state.voice_client.disconnect()
            state.voice_client = None

        state.clear()
        await interaction.response.send_message(
            embed=discord.Embed(
                title="⏹️ Stopped",
                description="Playback stopped, queue cleared, and disconnected.",
                color=COLOR_INFO,
            )
        )

    @app_commands.command(name="nowplaying", description="Show the currently playing track")
    async def nowplaying(self, interaction: discord.Interaction):
        """Show what's currently playing."""
        state = self._get_state(interaction.guild_id)

        if not state.current or not state.voice_client or not (
            state.voice_client.is_playing() or state.voice_client.is_paused()
        ):
            await interaction.response.send_message(
                embed=self._make_error_embed("Nothing is playing right now."),
                ephemeral=True,
            )
            return

        embed = self._make_now_playing_embed(state.current)
        if state.voice_client.is_paused():
            embed.title = "⏸️ Paused"
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="volume", description="Set the playback volume (1-100)")
    @app_commands.describe(level="Volume level from 1 to 100")
    async def volume(self, interaction: discord.Interaction, level: int):
        """Adjust playback volume."""
        if level < 1 or level > 100:
            await interaction.response.send_message(
                embed=self._make_error_embed("Volume must be between 1 and 100."),
                ephemeral=True,
            )
            return

        state = self._get_state(interaction.guild_id)
        state.volume = level / 100.0

        if (
            state.voice_client
            and state.voice_client.source
            and hasattr(state.voice_client.source, "volume")
        ):
            state.voice_client.source.volume = state.volume

        emoji = "🔊" if level > 50 else "🔉" if level > 20 else "🔈"
        await interaction.response.send_message(
            embed=discord.Embed(
                title=f"{emoji} Volume",
                description=f"Set to **{level}%**",
                color=COLOR_INFO,
            )
        )

    @app_commands.command(name="loop", description="Toggle loop for the current track")
    async def loop(self, interaction: discord.Interaction):
        """Toggle loop mode."""
        state = self._get_state(interaction.guild_id)
        state.loop = not state.loop

        status = "enabled 🔁" if state.loop else "disabled"
        await interaction.response.send_message(
            embed=discord.Embed(
                title="🔁 Loop",
                description=f"Loop is now **{status}**.",
                color=COLOR_INFO,
            )
        )


async def setup(bot: commands.Bot):
    """Load the Music cog."""
    await bot.add_cog(Music(bot))
