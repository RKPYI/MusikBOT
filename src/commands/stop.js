import { SlashCommandBuilder } from "discord.js";
import { getQueue } from "../queue.js";
import { infoEmbed } from "../embeds.js";

export const data = new SlashCommandBuilder()
    .setName("stop")
    .setDescription("Stop playback, clear queue, and disconnect");

export async function execute(interaction, client) {
    const guildId = interaction.guildId;
    const queue = getQueue(client, guildId);

    queue.cancelDisconnect();
    queue.clear();

    if (queue.player) {
        await queue.player.stopTrack();
        await queue.player.destroy();
        client.shoukaku.leaveVoiceChannel(guildId);
    }

    queue.player = null;
    client.queues.delete(guildId);

    return interaction.reply({
        embeds: [
            infoEmbed(
                "⏹️ Stopped",
                "Playback stopped, queue cleared, and disconnected."
            ),
        ],
    });
}
