import { SlashCommandBuilder, EmbedBuilder } from "discord.js";
import { getQueue } from "../queue.js";
import { Colors, formatDuration } from "../embeds.js";

export const data = new SlashCommandBuilder()
    .setName("queue")
    .setDescription("Show the current music queue");

export async function execute(interaction, client) {
    const queue = getQueue(client, interaction.guildId);

    if (!queue.current && queue.tracks.length === 0) {
        return interaction.reply({
            embeds: [
                new EmbedBuilder()
                    .setTitle("📋 Queue")
                    .setDescription("The queue is empty. Use `/play` to add songs!")
                    .setColor(Colors.INFO),
            ],
            ephemeral: true,
        });
    }

    const lines = [];

    if (queue.current) {
        const t = queue.current.track;
        lines.push(
            `🎶 **Now Playing:** ${t.info.title} [${formatDuration(t.info.length)}]`
        );
        lines.push("");
    }

    if (queue.tracks.length > 0) {
        lines.push("**Up Next:**");
        const shown = queue.tracks.slice(0, 10);
        shown.forEach((entry, i) => {
            lines.push(
                `\`${i + 1}.\` ${entry.track.info.title} [${formatDuration(entry.track.info.length)}]`
            );
        });
        if (queue.tracks.length > 10) {
            lines.push(`\n*...and ${queue.tracks.length - 10} more*`);
        }
    } else {
        lines.push("*No more tracks in queue.*");
    }

    const embed = new EmbedBuilder()
        .setTitle("📋 Queue")
        .setDescription(lines.join("\n"))
        .setColor(Colors.QUEUED)
        .setFooter({ text: `Volume: ${queue.volume}%` });

    return interaction.reply({ embeds: [embed] });
}
