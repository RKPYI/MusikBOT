import { EmbedBuilder } from "discord.js";

// ─── Colors ──────────────────────────────────────────────────────────────────
export const Colors = {
    PLAYING: 0x1db954, // Spotify green
    QUEUED: 0x5865f2, // Discord blurple
    ERROR: 0xed4245, // Red
    INFO: 0xfee75c, // Yellow
};

/**
 * Format milliseconds as MM:SS.
 * @param {number} ms
 */
export function formatDuration(ms) {
    if (!ms || ms <= 0) return "Live";
    const totalSeconds = Math.floor(ms / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

/**
 * Create a "Now Playing" embed.
 */
export function nowPlayingEmbed(track, requester) {
    const embed = new EmbedBuilder()
        .setTitle("🎶 Now Playing")
        .setDescription(`**[${track.info.title}](${track.info.uri})**`)
        .setColor(Colors.PLAYING)
        .addFields(
            { name: "Duration", value: formatDuration(track.info.length), inline: true }
        );

    if (requester) {
        embed.addFields({ name: "Requested by", value: requester, inline: true });
    }
    if (track.info.artworkUrl) {
        embed.setThumbnail(track.info.artworkUrl);
    }
    return embed;
}

/**
 * Create an "Added to Queue" embed.
 */
export function queuedEmbed(track, position, requester) {
    const embed = new EmbedBuilder()
        .setTitle("📋 Added to Queue")
        .setDescription(`**[${track.info.title}](${track.info.uri})**`)
        .setColor(Colors.QUEUED)
        .addFields(
            { name: "Position", value: String(position), inline: true },
            { name: "Duration", value: formatDuration(track.info.length), inline: true }
        );

    if (track.info.artworkUrl) {
        embed.setThumbnail(track.info.artworkUrl);
    }
    return embed;
}

/**
 * Create an error embed.
 */
export function errorEmbed(message) {
    return new EmbedBuilder()
        .setTitle("❌ Error")
        .setDescription(message)
        .setColor(Colors.ERROR);
}

/**
 * Create a simple info embed.
 */
export function infoEmbed(title, description) {
    const embed = new EmbedBuilder().setTitle(title).setColor(Colors.INFO);
    if (description) embed.setDescription(description);
    return embed;
}
