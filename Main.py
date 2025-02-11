import discord

from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime

class BumpData:
    def __init__(self, channelId, followUp, totalBumpCount, bumpInterval):
        self.channelId = channelId
        self.followUp = followUp

        self.currentBumpCount = 0
        self.totalBumpCount = totalBumpCount
        self.bumpStartTime = datetime.now()

        self.bumpInterval = bumpInterval * 60

    async def Bump(self):
        await self.followUp.send("Bump!")

class Client(commands.Bot):
    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        send_periodic_message.start()

        try:
            synced = await self.tree.sync()
            print(f'Synced {len(synced)} - {synced} commands')
        except Exception as e:
            print(f'Failed to sync commands: {e}')

intents = discord.Intents.default()
intents.message_content = True
client = Client(command_prefix = '/', intents = intents)

followUpList = {}

@tasks.loop(seconds=10)
async def send_periodic_message():
    channelsToRemove = []

    for channelId in followUpList:
        bumpData = followUpList[channelId]
        if bumpData.currentBumpCount >= bumpData.totalBumpCount:
            continue

        if (datetime.now() - bumpData.bumpStartTime).total_seconds() >= bumpData.bumpInterval:
            await bumpData.Bump()
            bumpData.currentBumpCount += 1
            bumpData.bumpStartTime = datetime.now()

            if bumpData.currentBumpCount >= bumpData.totalBumpCount:
                channelsToRemove.append(channelId)

    for channelId in channelsToRemove:
        del followUpList[channelId]

@client.tree.command(name = 'bump', description = "Bumps your post every hour.")
@app_commands.describe(
    bumpcount = "The number of times your post is bumped. Default is 8. Maximum is 24.",
    bumpinterval = "The interval in minutes between each bump. Default is 1 hour."
)
@app_commands.allowed_installs(guilds = False, users = True)
@app_commands.allowed_contexts(guilds = True, dms = False, private_channels = False)
async def registerPostBump(interaction, bumpcount: str = None, bumpinterval: str = None):
    if interaction.channel_id in followUpList:
        await interaction.response.send_message(f"This channel is already being bumped.", ephemeral=True)
        return

    if bumpcount is None:
        bumpcount = 8
    else:
        try:
            bumpcount = int(bumpcount)
        except:
            await interaction.response.send_message(f"Invalid bump count.", ephemeral=True)
            return

    if bumpcount < 1:
        await interaction.response.send_message(f"Bump count must be at least 1.", ephemeral=True)
        return
    if bumpcount > 24:
        await interaction.response.send_message(f"Bump count must be at most 24.", ephemeral=True)
        return

    if bumpinterval is None:
        bumpinterval = 60
    else:
        try:
            bumpinterval = float(bumpinterval)
        except:
            await interaction.response.send_message(f"Invalid bump interval.", ephemeral=True)
            return

    if bumpinterval < 1:
        await interaction.response.send_message(f"Bump interval must be at least 1 minute.", ephemeral=True)
        return
    if bumpinterval > 120:
        await interaction.response.send_message(f"Bump interval must be at most 120 minutes.", ephemeral=True)
        return

    await interaction.response.defer()

    followUp = interaction.followup
    followUpList[interaction.channel_id] = BumpData(
        channelId = interaction.channel_id,
        followUp = followUp,
        totalBumpCount = bumpcount,
        bumpInterval = bumpinterval
    )
    await followUp.send("Starting bumping!")

@client.tree.command(name='bumpy', description="Bumps your post every hour.")
@app_commands.describe(bumpcount="The number of times your post is bumped. Default is 8. Maximum is 24.")
@app_commands.allowed_installs(guilds=False, users=True)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
async def registerPostBumpy(interaction, bumpcount: str = None, bumpinterval: str = None):
    await registerPostBump.callback(interaction, bumpcount, bumpinterval)

with open('BotToken') as file:
    client.run(file.read().strip())