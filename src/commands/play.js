import { SlashCommandBuilder } from "discord.js";
import { getQueue } from "../queue.js";
import { nowPlayingEmbed, queuedEmbed, errorEmbed } from "../embeds.js";

export const data = new SlashCommandBuilder()
    .setName("play")
    .setDescription("Play a song from YouTube or search by name")
    .addStringOption((opt) =>
        opt
            .setName("query")
            .setDescription("YouTube URL or search query")
            .setRequired(true)
    );

export async function execute(interaction, client) {
    await interaction.deferReply();

    const member = interaction.member;
    if (!member.voice?.channel) {
        return interaction.followUp({
            embeds: [errorEmbed("You need to be in a voice channel!")],
            ephemeral: true,
        });
    }

    const query = interaction.options.getString("query", true);
    const guildId = interaction.guildId;
    const queue = getQueue(client, guildId);

    // Get a Lavalink node
    const node = client.shoukaku.getIdealNode();
    if (!node) {
        return interaction.followUp({
            embeds: [errorEmbed("No Lavalink nodes available.")],
        });
    }

    // Search for the track
    const isUrl = /^https?:\/\//.test(query);
    const searchQuery = isUrl ? query : `ytsearch:${query}`;

    let result;
    try {
        result = await node.rest.resolve(searchQuery);
    } catch (err) {
        console.error("[Play] Search failed:", err);
        return interaction.followUp({
            embeds: [errorEmbed(`Search failed: ${err.message}`)],
        });
    }

    if (!result?.data || result.loadType === "empty" || result.loadType === "error") {
        return interaction.followUp({
            embeds: [errorEmbed(`No results found for: **${query}**`)],
        });
    }

    // Pick the track(s)
    let track;
    if (result.loadType === "track" || result.loadType === "short") {
        track = result.data;
    } else if (result.loadType === "search") {
        track = result.data[0];
    } else if (result.loadType === "playlist") {
        // Add all playlist tracks
        for (const t of result.data.tracks) {
            queue.enqueue(t, member.displayName);
        }
        // If not playing, start
        if (!queue.player) {
            await startPlayer(interaction, client, queue, guildId, member);
        }
        return interaction.followUp({
            embeds: [
                queuedEmbed(
                    result.data.tracks[0],
                    queue.tracks.length,
                    member.displayName
                ).setTitle(`📋 Added Playlist: ${result.data.info.name}`),
            ],
        });
    }

    if (!track) {
        return interaction.followUp({
            embeds: [errorEmbed(`No results found for: **${query}**`)],
        });
    }

    queue.enqueue(track, member.displayName);

    // If already playing, just add to queue
    if (queue.player && queue.current) {
        return interaction.followUp({
            embeds: [queuedEmbed(track, queue.tracks.length, member.displayName)],
        });
    }

    // Otherwise, join and play
    await startPlayer(interaction, client, queue, guildId, member);

    return interaction.followUp({
        embeds: [nowPlayingEmbed(queue.current.track, queue.current.requester)],
    });
}

async function startPlayer(interaction, client, queue, guildId, member) {
    queue.cancelDisconnect();

    // Join voice channel
    let player = queue.player;
    if (!player) {
        player = await client.shoukaku.joinVoiceChannel({
            guildId,
            channelId: member.voice.channel.id,
            shardId: 0,
            deaf: true,
        });
        queue.player = player;
        console.log(`[Player] Joined voice channel in guild ${guildId}`);

        // Handle track end
        player.on("end", (data) => {
            console.log(`[Player] Track ended — reason: ${data.reason}`);

            // "replaced" means another track was started (e.g. skip) — ignore
            if (data.reason === "replaced") return;

            // If the track failed to load, log it clearly
            if (data.reason === "loadFailed") {
                console.error("[Player] Track failed to load!");
            }

            const next = queue.dequeue();
            if (next) {
                queue.current = next;
                console.log(`[Player] Playing next: ${next.track.info?.title ?? "unknown"}`);
                player.playTrack({ track: { encoded: next.track.encoded } });
            } else {
                queue.current = null;
                console.log("[Player] Queue empty, scheduling auto-disconnect.");
                queue.scheduleDisconnect(client, guildId);
            }
        });

        // Handle errors
        player.on("exception", (error) => {
            console.error("[Player] Exception:", error);
            const next = queue.dequeue();
            if (next) {
                queue.current = next;
                player.playTrack({ track: { encoded: next.track.encoded } });
            } else {
                queue.current = null;
                console.log("[Player] Queue empty after exception, scheduling auto-disconnect.");
                queue.scheduleDisconnect(client, guildId);
            }
        });

        player.on("stuck", () => {
            console.warn("[Player] Track stuck, skipping...");
            const next = queue.dequeue();
            if (next) {
                queue.current = next;
                player.playTrack({ track: { encoded: next.track.encoded } });
            } else {
                queue.current = null;
                console.log("[Player] Queue empty after stuck, scheduling auto-disconnect.");
                queue.scheduleDisconnect(client, guildId);
            }
        });

        player.on("closed", (data) => {
            console.log(`[Player] WebSocket closed — code: ${data?.code}, reason: ${data?.reason}`);
            queue.clear();
            queue.player = null;
            client.queues.delete(guildId);
        });
    }

    // Play the first track
    const entry = queue.dequeue();
    if (entry) {
        queue.current = entry;
        await player.playTrack({ track: { encoded: entry.track.encoded } });
        await player.setGlobalVolume(queue.volume);
    }
}
