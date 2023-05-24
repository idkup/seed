import asyncio
import datetime
import discord
from discord.ext import commands
from io import BytesIO
import os
import pandas as pd
from PIL import Image, ImageOps
import random
import re
import requests
from typing import Optional, Tuple


# EMBED
class EmbedFlags(commands.FlagConverter):
    Author: Optional[discord.Member]
    Title: Optional[str]
    Description: Optional[str]
    Color: Optional[int]
    Image: Optional[str]
    FooterText: Optional[str]
    FooterIcon: Optional[str]
    URL: Optional[str]
    Thumbnail: Optional[str]

    Channel: Optional[int]
    MSG_ID: Optional[int]


# REACTION ROLES
class ReactionRoleFlags(commands.FlagConverter):
    Title: str
    Emojis: Tuple[int, ...]
    Roles: Tuple[int, ...]
    Unique: bool = False


# TIMED GIVEAWAY
class TimedGiveawayFlags(commands.FlagConverter):
    Gift: str
    Donor: Optional[discord.Member]
    Seconds: int = 0
    Minutes: int = 0
    Hours: int = 0
    Days: int = 0


# CONSTANTS
COMMAND_PREFIX = "%"
GARDEN_CHANNEL = 659956684642451463
LEAF_DROP_RATE = 0.05
GIVEAWAY_CHANNEL = 672496562164989983
GIVEAWAY_REACTION = "🎉"
CONFIRM_REACTION = "✅"
CANCEL_REACTION = "❌"
REACTION_ROLES_CHANNEL = 726134052968726571
WORKAROUND_CHANNEL = 1084297203905994813

# VARIABLES
can_collect = False

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

with open('key.txt', 'r') as k:
    key = k.readline()


@bot.command(aliases=["add"])
async def leafadd(ctx, user:discord.Member, amount: int):
    leaf_db = pd.read_csv('leaves.csv')
    if user.id not in leaf_db.userID.values:
        new_row = pd.DataFrame([[user.id, amount]], columns=["userID", "amount"])
        leaf_db = pd.concat([leaf_db, new_row])
    else:
        balance = int(leaf_db.loc[leaf_db.userID == user.id, "amount"]) + amount
        leaf_db.loc[leaf_db.userID == user.id, "amount"] = balance
    leaf_db.to_csv("leaves.csv", index=False)
    await ctx.send(f"Added {amount} leaves to {user.mention}.")


@bot.command(aliases=["balance"])
async def leafbalance(ctx, user: Optional[discord.Member]):
    if not user:
        user = ctx.author
    leaf_db = pd.read_csv('leaves.csv')
    if user.id not in leaf_db.userID.values:
        new_row = pd.DataFrame([[user.id, 0]], columns=["userID", "amount"])
        leaf_db = pd.concat([leaf_db, new_row])
        leaf_db.to_csv("leaves.csv", index=False)
    balance = int(leaf_db.loc[leaf_db.userID == user.id, "amount"])
    await ctx.send(f"{user.mention} has {balance} leaves.")


@bot.command(aliases=["collect", "c"])
async def leafcollect(ctx):
    global can_collect
    if can_collect is True:
        can_collect = False
        leaf_db = pd.read_csv('leaves.csv')
        leaves = abs(int(20 * random.gauss(0, 1)))
        if ctx.author.id not in leaf_db.userID.values:
            new_row = pd.DataFrame([[ctx.author.id, leaves]], columns=["userID", "amount"])
            leaf_db = pd.concat([leaf_db, new_row])
        else:
            balance = int(leaf_db.loc[leaf_db.userID == ctx.author.id, "amount"]) + leaves
            leaf_db.loc[leaf_db.userID == ctx.author.id, "amount"] = balance
        leaf_db.to_csv("leaves.csv", index=False)
        e = discord.Embed(title="Leaves!", color=5763719, description=f"{ctx.author.mention} has collected {leaves} leaves!")
        noti = await ctx.send(embed=e)
        await asyncio.sleep(5)
        await noti.delete()
    else:
        await ctx.author.send("Cannot collect leaves right now.")
    await ctx.message.delete()


@bot.command()
async def leafderboard(ctx):
    leaf_db = pd.read_csv('leaves.csv')
    leaf_db["userID"] = leaf_db["userID"].map(lambda x: f"{bot.get_user(x).display_name}")
    leaf_db.sort_values(by="amount", ascending=False, inplace=True)
    await ctx.send(f"{leaf_db.to_string(index=False)}")


@bot.command(aliases=["embed", "embededit"])
async def embedmanual(ctx, *, flags: EmbedFlags):
    if flags.MSG_ID:
        if flags.Channel:
            channel = ctx.guild.get_channel(int(flags.Channel))
        else:
            channel = ctx.channel
        message = await channel.fetch_message(int(flags.MSG_ID))
        e = message.embeds[0]
        if flags.Author:
            e.set_author(name=f"{flags.Author.display_name}", icon_url=flags.Author.display_avatar.url)
        if flags.Title:
            e.title = flags.Title
        if flags.Description:
            e.description = flags.Description
        if flags.Color:
            e.colour = flags.Color
        if flags.Image:
            e.set_image(url=flags.Image)
        if flags.Thumbnail:
            e.set_thumbnail(url=flags.Thumbnail)
        if flags.FooterIcon or flags.FooterText:
            e.set_footer(text=flags.FooterText, icon_url=flags.FooterIcon)
        if flags.URL:
            e.url = flags.URL
        await message.edit(embed=e)
    else:
        e = discord.Embed()
        if flags.Author:
            e.set_author(name=f"{flags.Author.display_name}", icon_url=flags.Author.display_avatar.url)
        if flags.Title:
            e.title = flags.Title
        if flags.Description:
            e.description = flags.Description
        if flags.Color:
            e.colour = flags.Color
        if flags.Image:
            e.set_image(url=flags.Image)
        if flags.Thumbnail:
            e.set_thumbnail(url=flags.Thumbnail)
        if flags.FooterIcon or flags.FooterText:
            e.set_footer(text=flags.FooterText, icon_url=flags.FooterIcon)
        if flags.URL:
            e.url = flags.URL
        if not flags.Channel:
            await ctx.send(embed=e)
        else:
            await bot.get_channel(flags.Channel).send(embed=e)


@bot.command()
async def embedresize(ctx, channel_id, message_id, width):
    channel = ctx.guild.get_channel(int(channel_id))
    message = await channel.fetch_message(int(message_id))
    embed = message.embeds[0]
    image = Image.open(BytesIO(requests.get(embed.image.url).content)) if embed.image.url else Image.new(mode='RGBA', size=(100, 2), color=(0, 0, 0, 0))
    image = image.convert("RGBA")
    pad = (int(width) - image.width)//2
    new_image = ImageOps.expand(image, border=(pad, 0, pad, 0), fill=(0, 0, 0, 0))

    with BytesIO() as imb:
        new_image.save(imb, 'PNG')
        imb.seek(0)
        temp_message = await ctx.guild.get_channel(WORKAROUND_CHANNEL).send(file=discord.File(fp=imb, filename='img.png'))
    attach = temp_message.attachments[0]
    embed.set_image(url=attach.url)
    await message.edit(embed=embed)
    await temp_message.delete()


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
    embed = discord.Embed(title=flags.Title)
    desc = ""
    if flags.Unique:
        desc += "*You may only select one of the following roles.*\n"
    else:
        desc += "*You may select as many of the following roles as you please.*\n"
    for e, r in zip(flags.Emojis, flags.Roles):
        desc += f"{bot.get_emoji(e)} <@&{r}>\n"
    embed.description = desc
    message = await bot.get_channel(REACTION_ROLES_CHANNEL).send(embed=embed)
    for e in flags.Emojis:
        await message.add_reaction(bot.get_emoji(e))


# @bot.command(aliases=["g"])
# async def giveaway(ctx, obj):
#     if ctx.channel.id == GIVEAWAY_CHANNEL:
#         e = discord.Embed(title="Giveaway!", description=f"<@{ctx.author.id}> is giving away **{obj}**! React with {GIVEAWAY_REACTION} to join!")
#         message = await ctx.send(embed=e)
#         await message.add_reaction(GIVEAWAY_REACTION)
#         await message.add_reaction(CANCEL_REACTION)


@bot.command(aliases=["tg", "g", "giveaway"])
async def timedgiveaway(ctx, *, flags: TimedGiveawayFlags):
    donor = flags.Donor if flags.Donor else ctx.author
    if ctx.channel.id == GIVEAWAY_CHANNEL:
        giveaway_end = datetime.datetime.now() + datetime.timedelta(days=flags.Days, hours=flags.Hours, minutes=flags.Minutes, seconds=flags.Seconds)
        epoch = int(giveaway_end.timestamp())
        e = discord.Embed(title="Giveaway!", description=f"<@{donor.id}> is giving away **{flags.Gift}**! React with {GIVEAWAY_REACTION} to join!\n This giveaway expires at <t:{epoch}>.")
        e.set_author(name=f"{donor.display_name}", icon_url=donor.display_avatar.url)
        message = await ctx.send(embed=e)
        await ctx.message.delete()
        await message.add_reaction(GIVEAWAY_REACTION)
        await message.add_reaction(CANCEL_REACTION)
        old_data = pd.read_csv('timedGiveaways.csv')
        new_row = pd.DataFrame([[message.id, donor.id, epoch, flags.Gift]], columns=["messageID", "userID", "expire", "gift"])
        new_data = pd.concat([old_data, new_row])
        new_data.to_csv('timedGiveaways.csv', index=False)


@bot.event
async def on_message(msg):
    global can_collect
    await bot.process_commands(msg)
    if msg.channel.id == GARDEN_CHANNEL and random.random() < LEAF_DROP_RATE and msg.author != bot.user:
        can_collect = True
        e = discord.Embed(title="Leaves!", color=5763719, description=f"Some leaves have fallen in the garden. **{COMMAND_PREFIX}collect** to pick them up!")
        e.set_footer(text="5")
        noti = await msg.channel.send(embed=e)
        for i in range(4):
            await asyncio.sleep(1)
            e.set_footer(text=f"{4-i}")
            await noti.edit(embed=e)
        await asyncio.sleep(1)
        await noti.delete()
        can_collect = False


@bot.event
async def on_raw_reaction_add(payload):
    guild = bot.get_guild(payload.guild_id)
    channel = bot.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    embeds = message.embeds
    # END GIVEAWAY
    if payload.channel_id == GIVEAWAY_CHANNEL and str(payload.emoji) == CANCEL_REACTION and \
            f"<@{payload.user_id}>" in embeds[0].description and message.author == bot.user:
        active_giveaways = pd.read_csv("timedGiveaways.csv")
        active_giveaways = active_giveaways.loc[int(active_giveaways["messageID"]) == message.id]
        active_giveaways.to_csv('timedGiveaways.csv', index=False)
        e = message.embeds[0]
        e.description = "This giveaway was cancelled."
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


@bot.event
async def on_ready():
    bot.loop.create_task(timer())


async def timer():
    while True:
        active_giveaways = pd.read_csv("timedGiveaways.csv")
        expired_giveaways = active_giveaways.loc[active_giveaways["expire"] <= int(datetime.datetime.now().timestamp())]
        active_giveaways = active_giveaways.loc[active_giveaways["expire"] > int(datetime.datetime.now().timestamp())]
        active_giveaways.to_csv('timedGiveaways.csv', index=False)

        for i in zip(expired_giveaways["messageID"], expired_giveaways["userID"], expired_giveaways["gift"]):
            channel = bot.get_channel(GIVEAWAY_CHANNEL)
            message = await channel.fetch_message(int(i[0]))
            for react in message.reactions:
                if str(react.emoji) == GIVEAWAY_REACTION:
                    users = [user async for user in react.users()]
                    try:
                        users.remove(bot.user)
                    except ValueError:
                        break
                    winner = random.choice(users)
                    await channel.send(
                        f"{winner.mention} has won **{i[2]}** from <@{int(i[1])}>!")
                    e = message.embeds[0]
                    e.description = f"<@{int(i[1])}> gave away **{i[2]}**. This giveaway is over."
                    await message.edit(embed=e)

        await asyncio.sleep(5)

if not os.path.isfile("timedGiveaways.csv"):
    giveaway_data = pd.DataFrame({"messageID": [], "userID": [], "expire": [], "gift": []})
    giveaway_data.to_csv("timedGiveaways.csv", index=False)
if not os.path.isfile("leaves.csv"):
    leaf_data = pd.DataFrame({"userID": [], "amount": []})
    leaf_data.to_csv("leaves.csv", index=False)


bot.run(key)

