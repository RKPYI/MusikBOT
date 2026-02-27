import {
    Client,
    GatewayIntentBits,
    ActivityType,
    Collection,
} from "discord.js";
import { Shoukaku, Connectors } from "shoukaku";
import { config } from "dotenv";
import { readdirSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath, pathToFileURL } from "url";

config();

const __dirname = dirname(fileURLToPath(import.meta.url));

// ─── Validate env ────────────────────────────────────────────────────────────
const { DISCORD_TOKEN, LAVALINK_HOST, LAVALINK_PORT, LAVALINK_PASSWORD } =
    process.env;

if (!DISCORD_TOKEN) {
    console.error("DISCORD_TOKEN is not set. Copy .env.example → .env and fill it in.");
    process.exit(1);
}

// ─── Lavalink nodes ─────────────────────────────────────────────────────────
const nodes = [
    {
        name: "main",
        url: `${LAVALINK_HOST ?? "localhost"}:${LAVALINK_PORT ?? "2333"}`,
        auth: LAVALINK_PASSWORD ?? "youshallnotpass",
    },
];

// ─── Discord client ─────────────────────────────────────────────────────────
const client = new Client({
    intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildVoiceStates],
});

client.commands = new Collection();

// ─── Shoukaku (Lavalink) ────────────────────────────────────────────────────
const shoukaku = new Shoukaku(new Connectors.DiscordJS(client), nodes, {
    moveOnDisconnect: false,
    reconnectTries: 5,
    reconnectInterval: 5,
});

shoukaku.on("error", (_, error) =>
    console.error(`[Shoukaku] Error: ${error.message}`)
);
shoukaku.on("ready", (name) =>
    console.log(`[Shoukaku] Node "${name}" connected`)
);
shoukaku.on("disconnect", (name, reason) =>
    console.log(`[Shoukaku] Node "${name}" disconnected (${reason ?? "unknown"})`)
);

client.shoukaku = shoukaku;

/** Per-guild music queues: Map<guildId, GuildQueue> */
client.queues = new Collection();

// ─── Load commands ──────────────────────────────────────────────────────────
const commandsPath = join(__dirname, "commands");
const commandFiles = readdirSync(commandsPath).filter((f) => f.endsWith(".js"));

for (const file of commandFiles) {
    const filePath = pathToFileURL(join(commandsPath, file)).href;
    const command = await import(filePath);
    if (command.data && command.execute) {
        client.commands.set(command.data.name, command);
    }
}

// ─── Events ─────────────────────────────────────────────────────────────────
client.once("ready", async () => {
    console.log(`Logged in as ${client.user.tag} (ID: ${client.user.id})`);
    console.log(`Connected to ${client.guilds.cache.size} guild(s)`);

    client.user.setActivity("/play 🎶", { type: ActivityType.Listening });

    // Register slash commands globally
    const commands = [...client.commands.values()].map((c) => c.data.toJSON());
    try {
        const synced = await client.application.commands.set(commands);
        console.log(`Synced ${synced.size} slash command(s)`);
    } catch (err) {
        console.error("Failed to sync commands:", err);
    }
});

client.on("interactionCreate", async (interaction) => {
    if (!interaction.isChatInputCommand()) return;

    const command = client.commands.get(interaction.commandName);
    if (!command) return;

    try {
        await command.execute(interaction, client);
    } catch (error) {
        console.error(`[Command Error] /${interaction.commandName}:`, error);
        const reply = {
            content: "❌ An error occurred while executing this command.",
            ephemeral: true,
        };
        if (interaction.replied || interaction.deferred) {
            await interaction.followUp(reply);
        } else {
            await interaction.reply(reply);
        }
    }
});

// ─── Start ──────────────────────────────────────────────────────────────────
client.login(DISCORD_TOKEN);
