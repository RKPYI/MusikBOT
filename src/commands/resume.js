import { SlashCommandBuilder } from "discord.js";
import { getQueue } from "../queue.js";
import { errorEmbed, infoEmbed, Colors } from "../embeds.js";
import { EmbedBuilder } from "discord.js";

export const data = new SlashCommandBuilder()
    .setName("resume")
    .setDescription("Resume the paused track");

export async function execute(interaction, client) {
    const queue = getQueue(client, interaction.guildId);

    if (!queue.player || !queue.current) {
        return interaction.reply({
            embeds: [errorEmbed("Nothing is paused right now.")],
            ephemeral: true,
        });
    }

    await queue.player.setPaused(false);
    return interaction.reply({
        embeds: [new EmbedBuilder().setTitle("▶️ Resumed").setColor(Colors.PLAYING)],
    });
}
