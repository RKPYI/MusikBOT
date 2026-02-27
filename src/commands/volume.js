import { SlashCommandBuilder } from "discord.js";
import { getQueue } from "../queue.js";
import { errorEmbed, infoEmbed } from "../embeds.js";

export const data = new SlashCommandBuilder()
    .setName("volume")
    .setDescription("Set the playback volume (1-100)")
    .addIntegerOption((opt) =>
        opt
            .setName("level")
            .setDescription("Volume level from 1 to 100")
            .setRequired(true)
            .setMinValue(1)
            .setMaxValue(100)
    );

export async function execute(interaction, client) {
    const level = interaction.options.getInteger("level", true);
    const queue = getQueue(client, interaction.guildId);

    queue.volume = level;

    if (queue.player) {
        await queue.player.setGlobalVolume(level);
    }

    const emoji = level > 50 ? "🔊" : level > 20 ? "🔉" : "🔈";
    return interaction.reply({
        embeds: [infoEmbed(`${emoji} Volume`, `Set to **${level}%**`)],
    });
}
