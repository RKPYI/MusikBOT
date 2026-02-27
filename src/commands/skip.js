import { SlashCommandBuilder } from "discord.js";
import { getQueue } from "../queue.js";
import { errorEmbed, infoEmbed } from "../embeds.js";

export const data = new SlashCommandBuilder()
    .setName("skip")
    .setDescription("Skip the current track");

export async function execute(interaction, client) {
    const queue = getQueue(client, interaction.guildId);

    if (!queue.player || !queue.current) {
        return interaction.reply({
            embeds: [errorEmbed("Nothing is playing right now.")],
            ephemeral: true,
        });
    }

    const title = queue.current.track.info.title;
    await queue.player.stopTrack();

    return interaction.reply({
        embeds: [infoEmbed("⏭️ Skipped", `Skipped **${title}**`)],
    });
}
