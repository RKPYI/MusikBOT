/**
 * Per-guild music queue manager.
 */
export class GuildQueue {
    constructor() {
        /** @type {import("shoukaku").Player | null} */
        this.player = null;

        /** @type {Array<{track: import("shoukaku").Track, requester: string}>} */
        this.tracks = [];

        /** @type {{track: import("shoukaku").Track, requester: string} | null} */
        this.current = null;

        /** @type {number} Volume 0–100 */
        this.volume = 50;

        /** @type {boolean} */
        this.loop = false;

        /** @type {NodeJS.Timeout | null} */
        this._disconnectTimer = null;
    }

    /** Add a track to the queue */
    enqueue(track, requester) {
        this.tracks.push({ track, requester });
    }

    /** Get the next track (respects loop) */
    dequeue() {
        if (this.loop && this.current) {
            return this.current;
        }
        return this.tracks.shift() ?? null;
    }

    /** Clear the queue */
    clear() {
        this.tracks = [];
        this.current = null;
        this.loop = false;
    }

    /** Schedule auto-disconnect after idle timeout */
    scheduleDisconnect(client, guildId, timeoutMs = 120_000) {
        this.cancelDisconnect();
        this._disconnectTimer = setTimeout(async () => {
            try {
                if (this.player) {
                    await this.player.destroy();
                }
                client.shoukaku.leaveVoiceChannel(guildId);
                this.clear();
                this.player = null;
                client.queues.delete(guildId);
                console.log(`[Queue] Auto-disconnected from guild ${guildId}`);
            } catch {
                // ignore
            }
        }, timeoutMs);
    }

    /** Cancel a pending auto-disconnect */
    cancelDisconnect() {
        if (this._disconnectTimer) {
            clearTimeout(this._disconnectTimer);
            this._disconnectTimer = null;
        }
    }
}

/**
 * Get or create a guild queue.
 * @param {import("discord.js").Client} client
 * @param {string} guildId
 * @returns {GuildQueue}
 */
export function getQueue(client, guildId) {
    if (!client.queues.has(guildId)) {
        client.queues.set(guildId, new GuildQueue());
    }
    return client.queues.get(guildId);
}
