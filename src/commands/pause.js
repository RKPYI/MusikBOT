import { SlashCommandBuilder } from "discord.js";
import { getQueue } from "../queue.js";
import { errorEmbed, infoEmbed } from "../embeds.js";

export const data = new SlashCommandBuilder()
    .setName("pause")
    .setDescription("Pause the current track");

export async function execute(interaction, client) {
    const queue = getQueue(client, interaction.guildId);

    if (!queue.player || !queue.current) {
        return interaction.reply({
            embeds: [errorEmbed("Nothing is playing right now.")],
            ephemeral: true,
        });
    }

    await queue.player.setPaused(true);
    return interaction.reply({ embeds: [infoEmbed("⏸️ Paused")] });
}
