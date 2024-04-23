import datetime
import discord
from discord.ext import commands

BOT_TOKEN = "MTIyMzQ2NTYwNTExODgyMDQ2Mw.GbYyZy.-tTxblAv66x99NUmRXddevvKWxh5hDYliJzQIg"

CHANNELS = {
    "DISCORD_STATUS": 1231832076135956490,
    "MONGODB_STATUS": 1231831742822748221,
    "MQTT_STATUS": 1231832188777926726,
    "DISCORD_UPDATES": 1231832351504334898,
    "MONGODB_UPDATES": 1231832290783395880,
    "MQTT_UPDATES": 1231832320017698849,
    "DISCORD_ERRORS": 1231831955495190529,
    "MONGODB_ERRORS": 1231832271472951326,
    "MQTT_ERRORS": 1231832133778145341,
}

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())


@bot.event
async def on_ready():
    channel = bot.get_channel(CHANNELS["DISCORD_STATUS"])

    embed_message = discord.Embed()
    embed_message.title = "IOT-Manager Bot"
    embed_message.description = ("The discord bot is now online and listening to incoming data.")
    embed_message.color = discord.Color.blue()
    embed_message.timestamp = datetime.datetime.now()

    await channel.send(embed=embed_message)


async def get_channel(channel_type):
    channel_id = CHANNELS.get(channel_type)
    if channel_id:
        return bot.get_channel(channel_id)
    else:
        return None


async def send_message(channel_type, message_content, is_error=False):
    channel = await get_channel(CHANNELS[channel_type])

    if channel:
        embed_color = discord.Color.red() if is_error else discord.Color.green()
        embed_title = ("IOT Data Logger - Error" if is_error else "IOT Data Logger - Update")

        embed_message = discord.Embed(
            title=embed_title,
            description=message_content,
            color=embed_color,
            timestamp=datetime.datetime.now(),
        )

        await channel.send(embed=embed_message)


async def setup():
    await bot.start(BOT_TOKEN)
