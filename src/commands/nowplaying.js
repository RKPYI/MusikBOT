import { SlashCommandBuilder } from "discord.js";
import { getQueue } from "../queue.js";
import { errorEmbed, nowPlayingEmbed, Colors } from "../embeds.js";
import { EmbedBuilder } from "discord.js";

export const data = new SlashCommandBuilder()
    .setName("nowplaying")
    .setDescription("Show the currently playing track");

export async function execute(interaction, client) {
    const queue = getQueue(client, interaction.guildId);

    if (!queue.player || !queue.current) {
        return interaction.reply({
            embeds: [errorEmbed("Nothing is playing right now.")],
            ephemeral: true,
        });
    }

    const embed = nowPlayingEmbed(queue.current.track, queue.current.requester);

    // Check if paused
    if (queue.player.paused) {
        embed.setTitle("⏸️ Paused");
    }

    return interaction.reply({ embeds: [embed] });
}
