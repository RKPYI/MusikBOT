import { SlashCommandBuilder } from "discord.js";
import { getQueue } from "../queue.js";
import { infoEmbed } from "../embeds.js";

export const data = new SlashCommandBuilder()
    .setName("loop")
    .setDescription("Toggle loop for the current track");

export async function execute(interaction, client) {
    const queue = getQueue(client, interaction.guildId);
    queue.loop = !queue.loop;

    const status = queue.loop ? "enabled 🔁" : "disabled";
    return interaction.reply({
        embeds: [infoEmbed("🔁 Loop", `Loop is now **${status}**.`)],
    });
}
