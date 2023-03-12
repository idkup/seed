import discord
from discord.ext import commands
import random
import re
from typing import Tuple


# REACTION ROLES
class ReactionRoleFlags(commands.FlagConverter):
    title: str
    emojis: Tuple[int, ...]
    roles: Tuple[int, ...]
    unique: bool = False


# CONSTANTS
COMMAND_PREFIX = "%"
GIVEAWAY_CHANNEL = 1084297203905994813
GIVEAWAY_REACTION = "🎉"
CANCEL_REACTION = "❌"

REACTION_ROLES_CHANNEL = 1084297203905994813

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

with open('key.txt', 'r') as k:
    key = k.readline()


@bot.command()
async def embedsource(ctx, channel_id, message_id):
    channel = ctx.guild.get_channel(int(channel_id))
    message = await channel.fetch_message(int(message_id))
    embeds = message.embeds
    for e in embeds:
        n = discord.Embed(title="Embed Source")
        n.description = f"```{e.to_dict()}```"
        await ctx.send(embed=n)


@bot.command()
async def generate_reaction_roles(ctx, *, flags: ReactionRoleFlags):
    embed = discord.Embed(title=flags.title)
    desc = ""
    if flags.unique:
        desc += "*You may only select one of the following roles.*\n"
    else:
        desc += "*You may select as many of the following roles as you please.*\n"
    for e, r in zip(flags.emojis, flags.roles):
        desc += f"{bot.get_emoji(e)} <@&{r}>\n"
    embed.description = desc
    message = await bot.get_channel(REACTION_ROLES_CHANNEL).send(embed=embed)
    for e in flags.emojis:
        await message.add_reaction(bot.get_emoji(e))


@bot.command(aliases=["g"])
async def giveaway(ctx, obj):
    if ctx.channel.id == GIVEAWAY_CHANNEL:
        e = discord.Embed(title="Giveaway!", description=f"<@{ctx.author.id}> is giving away **{obj}**! React with {GIVEAWAY_REACTION} to join!")
        message = await ctx.send(embed=e)
        await message.add_reaction(GIVEAWAY_REACTION)
        await message.add_reaction(CANCEL_REACTION)


@bot.event
async def on_raw_reaction_add(payload):
    guild = bot.get_guild(payload.guild_id)
    channel = bot.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    embeds = message.embeds
    # END GIVEAWAY
    if payload.channel_id == GIVEAWAY_CHANNEL and str(payload.emoji) == CANCEL_REACTION and \
            f"<@{payload.user_id}>" in embeds[0].description and message.author == bot.user:
        for react in message.reactions:
            if str(react.emoji) == GIVEAWAY_REACTION:
                users = [user async for user in react.users()]
                try:
                    users.remove(bot.user)
                except ValueError:
                    break
                winner = random.choice(users)
                await channel.send(f"{winner.mention} has won **{embeds[0].description.split('**')[1]}** from <@{payload.user_id}>!")
                e = discord.Embed(title="Giveaway!",
                                  description=f"This giveaway is over.")
                await message.edit(embed=e)
    # REACTION ROLES
    if payload.channel_id == REACTION_ROLES_CHANNEL and message.author == bot.user:
        parse = embeds[0].description
        unique = "*You may only select one of the following roles.*" in parse
        parsed_lines = parse.splitlines()[1:]
        for line in parsed_lines:
            role_id = int(re.search(r'(?<=\<@&)(.*?)(?=>)', line)[1])
            if str(payload.emoji) in line:
                await guild.get_member(payload.user_id).add_roles(guild.get_role(role_id))
                continue
            elif unique:
                await guild.get_member(payload.user_id).remove_roles(guild.get_role(role_id))


@bot.event
async def on_raw_reaction_remove(payload):
    guild = bot.get_guild(payload.guild_id)
    channel = bot.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    embeds = message.embeds
    # REACTION ROLES
    if payload.channel_id == REACTION_ROLES_CHANNEL and message.author == bot.user:
        parse = embeds[0].description
        parsed_lines = parse.splitlines()[1:]
        for line in parsed_lines:
            role_id = int(re.search(r'(?<=\<@&)(.*?)(?=>)', line)[1])
            if str(payload.emoji)[1:-1] in line:
                await guild.get_member(payload.user_id).remove_roles(guild.get_role(role_id))



bot.run(key)
