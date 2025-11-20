# ============================================================
#                         ELURA UTILITY
#                     All-In-One main.py
#         Ultra-Professional Discord Utility Framework
# ============================================================

import discord
from discord.ext import commands, tasks
from discord import app_commands, Embed, Interaction, File
import json, aiofiles, asyncio, os, datetime, random
from deep_translator import GoogleTranslator
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")

# ------------------------------------------------------------
# Load or Create Config
# ------------------------------------------------------------
if not os.path.exists("config.json"):
    with open("config.json", "w") as f:
        json.dump({
            "guild_id": "",
            "welcome_channel": "",
            "leave_channel": "",
            "log_channel": "",
            "count_channel": "",
            "economy_channel": "",
            "founder_role": "1438894978230259793",
            "tier1_roles": ["1438894988237738087"],
            "tier2_roles": ["1438894985909899285", "1438894986891497607"],
            "tier3_roles": ["1438894984677031957"],
            "tier4_roles": [
                "1438894983456227418",
                "1438894982537810081",
                "1438894980646305922",
                "1438894979119579169",
                "1438894978230259793"
            ]
        }, f, indent=4)

with open("config.json", "r") as f:
    config = json.load(f)

# ------------------------------------------------------------
# JSON Databases Auto-Created
# ------------------------------------------------------------
for db in ["economy.json", "punishments.json", "count.json"]:
    if not os.path.exists(db):
        with open(db, "w") as f:
            json.dump({}, f, indent=4)

# Utility for reading/writing JSON
async def read_json(file):
    async with aiofiles.open(file, "r") as f:
        data = await f.read()
        return json.loads(data)

async def write_json(file, data):
    async with aiofiles.open(file, "w") as f:
        await f.write(json.dumps(data, indent=4))

# ============================================================
#                     BOT INITIALIZATION
# ============================================================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.reactions = True

bot = commands.Bot(
    command_prefix=".",              # slash + dot both supported
    intents=intents,
    help_command=None                # custom /help later
)

tree = bot.tree

# ============================================================
#                   PERMISSION CHECK SYSTEM
# ============================================================

FOUNDER = config["founder_role"]
TIER1 = config["tier1_roles"]
TIER2 = config["tier2_roles"]
TIER3 = config["tier3_roles"]
TIER4 = config["tier4_roles"]

def has_role(user: discord.Member, role_id: str):
    return discord.utils.get(user.roles, id=int(role_id)) is not None

def can_use_punishments(user: discord.Member):
    uid = str(user.id)

    # Founder bypass
    if has_role(user, FOUNDER):
        return True

    role_ids = [str(r.id) for r in user.roles]

    # Tier 1 permissions
    if any(r in role_ids for r in TIER1):
        return True
    # Tier 2 permissions
    if any(r in role_ids for r in TIER2):
        return True
    # Tier 3 permissions
    if any(r in role_ids for r in TIER3):
        return True
    # Tier 4 permissions
    if any(r in role_ids for r in TIER4):
        return True

    return False

# ============================================================
#                UNIVERSAL RESPONSE / CLEAN EMBEDS
# ============================================================

def clean_embed(title=None, description=None, color=0x1e466f):
    embed = Embed(
        title=title,
        description=description,
        color=color
    )
    embed.timestamp = datetime.datetime.utcnow()
    return embed

def error_embed(msg):
    return clean_embed(
        title="❌ Error",
        description=msg,
        color=0xC72C3B
    )

def success_embed(msg):
    return clean_embed(
        title="✅ Success",
        description=msg,
        color=0x2ECC71
    )

# ============================================================
#                LOAD JSON UTILITIES AS HELPERS
# ============================================================

async def get_punishments():
    return await read_json("punishments.json")

async def save_punishments(data):
    await write_json("punishments.json", data)

async def get_economy():
    return await read_json("economy.json")

async def save_economy(data):
    await write_json("economy.json", data)

async def get_count():
    return await read_json("count.json")

async def save_count(data):
    await write_json("count.json", data)

# ============================================================
#                     ECONOMY HELPER LOGIC
# ============================================================

def generate_work_amount():
    return random.randint(50, 250)

def generate_rob_amount():
    return random.randint(80, 300)

# ============================================================
#                 CASE NUMBER GENERATION HELPER
# ============================================================

async def next_case_number():
    punish = await get_punishments()
    existing = [int(x.replace("case_", "")) for x in punish.keys()] or [0]
    return max(existing) + 1

# ============================================================
#                           /SETUP
#       Billion-dollar level interactive configuration wizard
# ============================================================

class SetupView(discord.ui.View):
    def __init__(self, author):
        super().__init__(timeout=120)
        self.author = author
        self.result = {
            "welcome_channel": None,
            "leave_channel": None,
            "count_channel": None,
            "log_channel": None,
            "economy_channel": None
        }

    async def interaction_check(self, interaction: Interaction):
        return interaction.user.id == self.author.id

    # ----------------------------
    # BUTTONS
    # ----------------------------

    @discord.ui.button(label="Set Welcome Channel", style=discord.ButtonStyle.primary)
    async def welcome_btn(self, interaction: Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Mention the welcome channel:", ephemeral=True
        )
        msg = await bot.wait_for(
            "message",
            check=lambda m: m.author.id == self.author.id,
            timeout=60
        )
        if msg.channel_mentions:
            self.result["welcome_channel"] = msg.channel_mentions[0].id
            await interaction.followup.send(
                f"Welcome channel set to {msg.channel_mentions[0].mention}", ephemeral=True
            )
        else:
            await interaction.followup.send("Invalid channel.", ephemeral=True)

    @discord.ui.button(label="Set Leave Channel", style=discord.ButtonStyle.primary)
    async def leave_btn(self, interaction: Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Mention the leave channel:", ephemeral=True
        )
        msg = await bot.wait_for(
            "message",
            check=lambda m: m.author.id == self.author.id,
            timeout=60
        )
        if msg.channel_mentions:
            self.result["leave_channel"] = msg.channel_mentions[0].id
            await interaction.followup.send(
                f"Leave channel set to {msg.channel_mentions[0].mention}", ephemeral=True
            )
        else:
            await interaction.followup.send("Invalid channel.", ephemeral=True)

    @discord.ui.button(label="Set Count Channel", style=discord.ButtonStyle.primary)
    async def count_btn(self, interaction: Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Mention the counting channel:", ephemeral=True
        )
        msg = await bot.wait_for(
            "message",
            check=lambda m: m.author.id == self.author.id,
            timeout=60
        )
        if msg.channel_mentions:
            self.result["count_channel"] = msg.channel_mentions[0].id
            await interaction.followup.send(
                f"Count channel set to {msg.channel_mentions[0].mention}", ephemeral=True
            )
        else:
            await interaction.followup.send("Invalid channel.", ephemeral=True)

    @discord.ui.button(label="Set Logs Channel", style=discord.ButtonStyle.primary)
    async def logs_btn(self, interaction: Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Mention the logs channel:", ephemeral=True
        )
        msg = await bot.wait_for(
            "message",
            check=lambda m: m.author.id == self.author.id,
            timeout=60
        )
        if msg.channel_mentions:
            self.result["log_channel"] = msg.channel_mentions[0].id
            await interaction.followup.send(
                f"Logs channel set to {msg.channel_mentions[0].mention}", ephemeral=True
            )
        else:
            await interaction.followup.send("Invalid channel.", ephemeral=True)

    @discord.ui.button(label="Set Economy Channel", style=discord.ButtonStyle.primary)
    async def eco_btn(self, interaction: Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Mention the economy channel:", ephemeral=True
        )
        msg = await bot.wait_for(
            "message",
            check=lambda m: m.author.id == self.author.id,
            timeout=60
        )
        if msg.channel_mentions:
            self.result["economy_channel"] = msg.channel_mentions[0].id
            await interaction.followup.send(
                f"Economy channel set to {msg.channel_mentions[0].mention}", ephemeral=True
            )
        else:
            await interaction.followup.send("Invalid channel.", ephemeral=True)

    @discord.ui.button(label="Finish Setup", style=discord.ButtonStyle.success)
    async def finish_btn(self, interaction: Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        self.stop()

# ============================================================
#                       SLASH COMMAND: /setup
# ============================================================

@tree.command(name="setup", description="Run the full Elura Utility setup wizard.")
async def setup_cmd(interaction: Interaction):

    if not has_role(interaction.user, FOUNDER):
        return await interaction.response.send_message(
            embed=error_embed("Only founders can run /setup."),
            ephemeral=True
        )

    v = SetupView(interaction.user)

    embed = clean_embed(
        title="⚙️ Elura Setup Wizard",
        description=(
            "Use the buttons below to configure your server.\n"
            "You have **2 minutes** to complete setup.\n\n"
            "**Required:**\n"
            "• Welcome Channel\n"
            "• Leave Channel\n"
            "• Logs Channel\n"
            "• Count Channel\n"
            "• Economy Channel\n\n"
            "Press **Finish Setup** when done."
        )
    )

    await interaction.response.send_message(embed=embed, view=v)

    await v.wait()

    # Save new config
    with open("config.json", "r") as f:
        current = json.load(f)

    for k, v2 in v.result.items():
        if v2 is not None:
            current[k] = v2

    with open("config.json", "w") as f:
        json.dump(current, f, indent=4)

    await interaction.followup.send(
        embed=success_embed("Setup complete! Elura Utility is now fully configured."),
        ephemeral=True
  )

# ============================================================
#                   WELCOME / LEAVE SYSTEM
# ============================================================

WELCOME_COLOR = 0x1e466f          # your hex blue
LEAVE_COLOR   = 0xC72C3B          # bright red

# ------------------------------------------------------------
#   Welcome Message Template:
#   **Welcome {usermention}!** You’ve successfully joined 
#   **{guildname}**. We hope you enjoy your stay.
# ------------------------------------------------------------

# ------------------------------------------------------------
#   Leave Message Template:
#   {Usermention} has left **{guildname}**. 
#   We hope to see them again in the future.
# ------------------------------------------------------------

@bot.event
async def on_member_join(member: discord.Member):
    try:
        with open("config.json", "r") as f:
            data = json.load(f)

        channel_id = data.get("welcome_channel")
        if not channel_id:
            return
        
        channel = member.guild.get_channel(int(channel_id))
        if not channel:
            return

        # Create embed
        embed = Embed(
            title=f"Welcome to {member.guild.name}!",
            description=f"**Welcome {member.mention}!** You’ve successfully joined **{member.guild.name}**.\nWe hope you enjoy your stay.",
            color=WELCOME_COLOR
        )

        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Member #{member.guild.member_count}")
        embed.timestamp = datetime.datetime.utcnow()

        await channel.send(embed=embed)

    except Exception as e:
        print(f"Welcome error: {e}")

# ------------------------------------------------------------
#                      MEMBER LEAVE EVENT
# ------------------------------------------------------------

@bot.event
async def on_member_remove(member: discord.Member):
    try:
        with open("config.json", "r") as f:
            data = json.load(f)

        channel_id = data.get("leave_channel")
        if not channel_id:
            return
        
        channel = member.guild.get_channel(int(channel_id))
        if not channel:
            return

        # Create embed
        embed = Embed(
            title=f"Member Left",
            description=f"{member.mention} has left **{member.guild.name}**.\nWe hope to see them again in the future.",
            color=LEAVE_COLOR
        )

        embed.set_thumbnail(url=member.display_avatar.url)
        embed.timestamp = datetime.datetime.utcnow()

        await channel.send(embed=embed)

    except Exception as e:
        print(f"Leave error: {e}")

# ============================================================
#                         COUNTING SYSTEM
# ============================================================

@bot.event
async def on_message(message: discord.Message):

    # Ignore bot messages
    if message.author.bot:
        return

    # Load config
    with open("config.json", "r") as f:
        config = json.load(f)

    count_channel_id = config.get("count_channel")

    # If message is NOT in the count channel → ignore
    if not count_channel_id or message.channel.id != int(count_channel_id):
        return await bot.process_commands(message)

    # Load current count
    count_data = await get_count()

    guild_id = str(message.guild.id)

    if guild_id not in count_data:
        count_data[guild_id] = {
            "current": 0,
            "last_user": None
        }

    current = count_data[guild_id]["current"]
    last_user = count_data[guild_id]["last_user"]

    # Check if message is a number
    try:
        num = int(message.content)
    except:
        # Not a number → ignore silently
        return await bot.process_commands(message)

    # Check if same user as last number
    if last_user == str(message.author.id):
        await message.add_reaction("❌")
        await message.reply(
            f"{message.author.mention} RUINED IT AT **{num}**!! Next number is **1**. **Wrong number.**"
        )
        count_data[guild_id]["current"] = 0
        count_data[guild_id]["last_user"] = None
        await save_count(count_data)
        return await bot.process_commands(message)

    # Correct next number
    if num == current + 1:
        await message.add_reaction("✅")
        count_data[guild_id]["current"] = num
        count_data[guild_id]["last_user"] = str(message.author.id)
        await save_count(count_data)

    else:
        # Wrong number → reset
        await message.add_reaction("❌")
        await message.reply(
            f"{message.author.mention} RUINED IT AT **{num}**!! Next number is **1**. **Wrong number.**"
        )

        # Reset
        count_data[guild_id]["current"] = 0
        count_data[guild_id]["last_user"] = None
        await save_count(count_data)

    await bot.process_commands(message)

  # ===========================================
# SECTION 6 — PART 1: WARNINGS SYSTEM
# ===========================================

import discord
from discord import app_commands
from discord.ext import commands
import uuid
import datetime
import json
import asyncio
import os

# Ensure data folder exists
if not os.path.exists("data"):
    os.mkdir("data")

punishments_file = "data/punishments.json"

# Load or create JSON
if os.path.exists(punishments_file):
    with open(punishments_file, "r") as f:
        punishments = json.load(f)
else:
    punishments = {}

# Helper functions
def save_punishments():
    with open(punishments_file, "w") as f:
        json.dump(punishments, f, indent=4)

def new_case_id():
    return str(uuid.uuid4())[:8].upper()

def now_utc():
    return datetime.datetime.utcnow().strftime("%Y-%m-%d • %H:%M UTC")

# Tier Permissions mapping
TIER_COMMANDS = {
    "1438894988237738087": ["warn"],
    "1438894985909899285": ["warn", "warnings"],
    "1438894986891497607": ["warn", "warnings", "mute"],
    "1438894984677031957": ["warn", "warnings", "mute", "kick"],
    "1438894983456227418": ["warn", "warnings", "mute", "kick", "ban", "unban"],
    "1438894982537810081": ["warn", "warnings", "mute", "kick", "ban", "unban"],
    "1438894980646305922": ["warn", "warnings", "mute", "kick", "ban", "unban"],
    "1438894979119579169": ["warn", "warnings", "mute", "kick", "ban", "unban"],
    "1438894978230259793": ["ALL"]  # Founders bypass
}

def get_user_tier(member: discord.Member):
    for role in member.roles:
        if str(role.id) in TIER_COMMANDS:
            return str(role.id)
    return None

def has_permission(member: discord.Member, command: str):
    tier = get_user_tier(member)
    if tier is None:
        return False
    if "ALL" in TIER_COMMANDS[tier]:
        return True
    return command in TIER_COMMANDS[tier]

# Mod log channel (to be set via /setup)
mod_log_channel = None

async def log_action(guild, embed):
    if mod_log_channel is None:
        return
    channel = guild.get_channel(mod_log_channel)
    if channel:
        await channel.send(embed=embed)

# ------------------------------
# /warn
# ------------------------------
@tree.command(name="warn", description="Warn a member.")
@app_commands.describe(member="Member to warn", reason="Reason for warning")
async def warn_cmd(interaction: discord.Interaction, member: discord.Member, reason: str):
    if member.id == interaction.user.id:
        return await interaction.response.send_message("❌ You cannot warn yourself.", ephemeral=True)

    if not has_permission(interaction.user, "warn"):
        return await interaction.response.send_message("❌ You lack permission to warn.", ephemeral=True)

    case_id = new_case_id()
    guild_id = str(interaction.guild.id)

    punishments.setdefault(guild_id, {"cases": []})
    data = {
        "case": case_id,
        "type": "warn",
        "user": member.id,
        "moderator": interaction.user.id,
        "reason": reason,
        "timestamp": now_utc()
    }
    punishments[guild_id]["cases"].append(data)
    save_punishments()

    embed = discord.Embed(title="⚠️ Warning Issued", color=discord.Color.yellow())
    embed.add_field(name="User", value=member.mention, inline=False)
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.add_field(name="Case ID", value=case_id, inline=False)
    embed.set_footer(text=f"Issued by {interaction.user} • {now_utc()}")

    await interaction.response.send_message(embed=embed)
    await log_action(interaction.guild, embed)

# ------------------------------
# /warnings
# ------------------------------
@tree.command(name="warnings", description="View a user's punishment history.")
@app_commands.describe(member="User to check")
async def warnings_cmd(interaction: discord.Interaction, member: discord.Member):
    guild_id = str(interaction.guild.id)
    user_list = [c for c in punishments.get(guild_id, {}).get("cases", []) if c["user"] == member.id]

    warn_count = sum(1 for c in user_list if c["type"] == "warn")
    mute_count = sum(1 for c in user_list if c["type"] == "mute")
    kick_count = sum(1 for c in user_list if c["type"] == "kick")
    ban_count = sum(1 for c in user_list if c["type"] == "ban")

    embed = discord.Embed(title="📄 Punishment History", color=discord.Color.blurple())
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="User", value=f"{member.mention}\n`{member.id}`", inline=False)
    embed.add_field(name="Totals", value=f"⚠️ Warned: {warn_count}\n🔇 Muted: {mute_count}\n👢 Kicked: {kick_count}\n⛔ Banned: {ban_count}", inline=False)

    if not user_list:
        embed.add_field(name="Cases", value="No punishments found.", inline=False)
    else:
        text = ""
        for c in user_list:
            text += f"**Case {c['case']}** — {c['type'].capitalize()}\n• Reason: `{c['reason']}`\n• Staff: <@{c['moderator']}>\n• Time: `{c['timestamp']}`\n\n"
        embed.add_field(name="Case List", value=text, inline=False)

    await interaction.response.send_message(embed=embed)

# ------------------------------
# /unwarn
# ------------------------------
class ConfirmUnwarn(discord.ui.View):
    def __init__(self, staff, guild_id, case_id):
        super().__init__(timeout=25)
        self.staff = staff
        self.guild_id = guild_id
        self.case_id = case_id

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def yes(self, interaction: discord.Interaction, button):
        if interaction.user.id != self.staff.id:
            return await interaction.response.send_message("❌ Not your confirmation.", ephemeral=True)

        guild_cases = punishments.get(self.guild_id, {}).get("cases", [])
        case_data = next((c for c in guild_cases if c["case"] == self.case_id), None)
        if not case_data:
            return await interaction.response.edit_message(content="❌ Case already removed.", view=None)

        guild_cases.remove(case_data)
        save_punishments()

        embed = discord.Embed(title="🗑 Case Removed", color=discord.Color.green())
        embed.add_field(name="Case ID", value=self.case_id)
        embed.add_field(name="Action", value=case_data["type"].capitalize())
        embed.add_field(name="User", value=f"<@{case_data['user']}>")
        embed.set_footer(text=f"Removed by {interaction.user} • {now_utc()}")
        await interaction.response.edit_message(content="", embed=embed, view=None)
        await log_action(interaction.guild, embed)

    @discord.ui.button(label="No", style=discord.ButtonStyle.red)
    async def no(self, interaction: discord.Interaction, button):
        await interaction.response.edit_message(content="❌ Cancelled.", view=None)


@tree.command(name="unwarn", description="Remove a punishment case.")
@app_commands.describe(case_id="Case ID")
async def unwarn_cmd(interaction: discord.Interaction, case_id: str):
    if not has_permission(interaction.user, "unwarn"):
        return await interaction.response.send_message("❌ You lack permission.", ephemeral=True)

    guild_id = str(interaction.guild.id)
    guild_cases = punishments.get(guild_id, {}).get("cases", [])
    if not any(c["case"] == case_id for c in guild_cases):
        return await interaction.response.send_message("❌ Invalid case ID.", ephemeral=True)

    view = ConfirmUnwarn(interaction.user, guild_id, case_id)
    await interaction.response.send_message(f"Are you sure you want to remove case `{case_id}`?", view=view, ephemeral=True)


# ===========================================
# SECTION 6 — PART 2: MODERATION COMMANDS
# ===========================================

# ------------------------------
# /mute
# ------------------------------
@tree.command(name="mute", description="Mute a member.")
@app_commands.describe(member="User to mute", minutes="Duration in minutes", reason="Reason for mute")
async def mute_cmd(interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str):
    if not has_permission(interaction.user, "mute"):
        return await interaction.response.send_message("❌ You lack permission to mute.", ephemeral=True)

    if member.id == interaction.user.id:
        return await interaction.response.send_message("❌ You cannot mute yourself.", ephemeral=True)

    mute_role = discord.utils.get(interaction.guild.roles, name="Muted")
    if not mute_role:
        mute_role = await interaction.guild.create_role(name="Muted", reason="Auto-created by Elura Utility")

    await member.add_roles(mute_role, reason=reason)

    # Record punishment
    case_id = new_case_id()
    guild_id = str(interaction.guild.id)
    punishments.setdefault(guild_id, {"cases": []})
    data = {
        "case": case_id,
        "type": "mute",
        "user": member.id,
        "moderator": interaction.user.id,
        "reason": reason,
        "timestamp": now_utc(),
        "duration": minutes
    }
    punishments[guild_id]["cases"].append(data)
    save_punishments()

    embed = discord.Embed(title="🔇 User Muted", color=discord.Color.orange())
    embed.add_field(name="User", value=member.mention)
    embed.add_field(name="Duration", value=f"{minutes} minutes")
    embed.add_field(name="Reason", value=reason)
    embed.add_field(name="Case ID", value=case_id)
    embed.set_footer(text=f"Issued by {interaction.user} • {now_utc()}")
    await interaction.response.send_message(embed=embed)
    await log_action(interaction.guild, embed)

    # Automatically unmute after duration
    async def unmute_after():
        await asyncio.sleep(minutes * 60)
        if mute_role in member.roles:
            await member.remove_roles(mute_role, reason="Mute duration expired")
            embed_unmute = discord.Embed(title="✅ User Unmuted", color=discord.Color.green())
            embed_unmute.add_field(name="User", value=member.mention)
            embed_unmute.add_field(name="Reason", value="Mute duration expired")
            await log_action(interaction.guild, embed_unmute)
    asyncio.create_task(unmute_after())

# ------------------------------
# /kick
# ------------------------------
@tree.command(name="kick", description="Kick a member from the server.")
@app_commands.describe(member="User to kick", reason="Reason for kick")
async def kick_cmd(interaction: discord.Interaction, member: discord.Member, reason: str):
    if not has_permission(interaction.user, "kick"):
        return await interaction.response.send_message("❌ You lack permission to kick.", ephemeral=True)

    if member.id == interaction.user.id:
        return await interaction.response.send_message("❌ You cannot kick yourself.", ephemeral=True)

    try:
        await member.kick(reason=reason)
    except discord.Forbidden:
        return await interaction.response.send_message("❌ Cannot kick this user.", ephemeral=True)

    # Record punishment
    case_id = new_case_id()
    guild_id = str(interaction.guild.id)
    punishments.setdefault(guild_id, {"cases": []})
    data = {
        "case": case_id,
        "type": "kick",
        "user": member.id,
        "moderator": interaction.user.id,
        "reason": reason,
        "timestamp": now_utc()
    }
    punishments[guild_id]["cases"].append(data)
    save_punishments()

    embed = discord.Embed(title="👢 User Kicked", color=discord.Color.red())
    embed.add_field(name="User", value=member.mention)
    embed.add_field(name="Reason", value=reason)
    embed.add_field(name="Case ID", value=case_id)
    embed.set_footer(text=f"Issued by {interaction.user} • {now_utc()}")
    await interaction.response.send_message(embed=embed)
    await log_action(interaction.guild, embed)

# ------------------------------
# /ban
# ------------------------------
@tree.command(name="ban", description="Ban a member from the server.")
@app_commands.describe(member="User to ban", reason="Reason for ban")
async def ban_cmd(interaction: discord.Interaction, member: discord.Member, reason: str):
    if not has_permission(interaction.user, "ban"):
        return await interaction.response.send_message("❌ You lack permission to ban.", ephemeral=True)

    if member.id == interaction.user.id:
        return await interaction.response.send_message("❌ You cannot ban yourself.", ephemeral=True)

    try:
        await member.ban(reason=reason)
    except discord.Forbidden:
        return await interaction.response.send_message("❌ Cannot ban this user.", ephemeral=True)

    # Record punishment
    case_id = new_case_id()
    guild_id = str(interaction.guild.id)
    punishments.setdefault(guild_id, {"cases": []})
    data = {
        "case": case_id,
        "type": "ban",
        "user": member.id,
        "moderator": interaction.user.id,
        "reason": reason,
        "timestamp": now_utc()
    }
    punishments[guild_id]["cases"].append(data)
    save_punishments()

    embed = discord.Embed(title="⛔ User Banned", color=discord.Color.dark_red())
    embed.add_field(name="User", value=member.mention)
    embed.add_field(name="Reason", value=reason)
    embed.add_field(name="Case ID", value=case_id)
    embed.set_footer(text=f"Issued by {interaction.user} • {now_utc()}")
    await interaction.response.send_message(embed=embed)
    await log_action(interaction.guild, embed)

# ------------------------------
# /unban
# ------------------------------
@tree.command(name="unban", description="Unban a user by ID.")
@app_commands.describe(user_id="ID of the user to unban", reason="Reason for unban")
async def unban_cmd(interaction: discord.Interaction, user_id: str, reason: str):
    if not has_permission(interaction.user, "unban"):
        return await interaction.response.send_message("❌ You lack permission to unban.", ephemeral=True)

    guild = interaction.guild
    try:
        user = await guild.fetch_member(int(user_id))
        return await interaction.response.send_message("❌ This user is not banned.", ephemeral=True)
    except:
        pass  # User not in guild, proceed to unban

    bans = await guild.bans()
    target = next((b.user for b in bans if str(b.user.id) == str(user_id)), None)
    if target is None:
        return await interaction.response.send_message("❌ User ID not found in ban list.", ephemeral=True)

    await guild.unban(target, reason=reason)

    # Record unban
    case_id = new_case_id()
    guild_id = str(interaction.guild.id)
    punishments.setdefault(guild_id, {"cases": []})
    data = {
        "case": case_id,
        "type": "unban",
        "user": target.id,
        "moderator": interaction.user.id,
        "reason": reason,
        "timestamp": now_utc()
    }
    punishments[guild_id]["cases"].append(data)
    save_punishments()

    embed = discord.Embed(title="✅ User Unbanned", color=discord.Color.green())
    embed.add_field(name="User", value=f"{target} (`{target.id}`)")
    embed.add_field(name="Reason", value=reason)
    embed.add_field(name="Case ID", value=case_id)
    embed.set_footer(text=f"Issued by {interaction.user} • {now_utc()}")
    await interaction.response.send_message(embed=embed)
    await log_action(interaction.guild, embed)

  # ===========================================
# SECTION 6 — PART 3: LOGGING & UTILITIES
# ===========================================

# ------------------------------
# Centralized log embed function
# ------------------------------
async def create_log_embed(action_type: str, member: discord.Member, moderator: discord.Member, reason: str, case_id: str, duration: int = None):
    colors = {
        "warn": discord.Color.yellow(),
        "mute": discord.Color.orange(),
        "kick": discord.Color.red(),
        "ban": discord.Color.dark_red(),
        "unban": discord.Color.green()
    }
    title_icons = {
        "warn": "⚠️ Warning Issued",
        "mute": "🔇 User Muted",
        "kick": "👢 User Kicked",
        "ban": "⛔ User Banned",
        "unban": "✅ User Unbanned"
    }

    embed = discord.Embed(
        title=title_icons.get(action_type, "Action Log"),
        color=colors.get(action_type, discord.Color.blurple())
    )

    embed.add_field(name="User", value=f"{member.mention} (`{member.id}`)", inline=False)
    embed.add_field(name="Moderator", value=f"{moderator.mention} (`{moderator.id}`)", inline=False)
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.add_field(name="Case ID", value=case_id, inline=False)
    if duration:
        embed.add_field(name="Duration", value=f"{duration} minutes", inline=False)

    embed.set_footer(text=f"Timestamp: {now_utc()}")
    return embed

# ------------------------------
# Update /warn, /mute, /kick, /ban, /unban to use centralized logging
# ------------------------------
# Example: replace direct embed in /warn with:
# embed = await create_log_embed("warn", member, interaction.user, reason, case_id)

# Then send:
# await interaction.response.send_message(embed=embed)
# await log_action(interaction.guild, embed)

# ------------------------------
# JSON Utilities
# ------------------------------
def get_guild_cases(guild_id: str):
    return punishments.setdefault(guild_id, {"cases": []})["cases"]

def add_case(guild_id: str, case_data: dict):
    punishments.setdefault(guild_id, {"cases": []})["cases"].append(case_data)
    save_punishments()

def remove_case(guild_id: str, case_id: str):
    guild_cases = get_guild_cases(guild_id)
    case = next((c for c in guild_cases if c["case"] == case_id), None)
    if case:
        guild_cases.remove(case)
        save_punishments()
        return case
    return None

# ------------------------------
# Integration Notes for main.py
# ------------------------------
# 1. Ensure `tree` is the global bot AppCommandTree:
#       tree = bot.tree
#
# 2. Ensure mod_log_channel is set via /setup command:
#       mod_log_channel = <your channel id>
#
# 3. All punishment commands are now JSON-backed and ultra-professional.
#
# 4. Use centralized embed function to maintain consistent branding/colors.
#
# 5. Add any new commands following the same pattern:
#       - Check permission via `has_permission()`
#       - Record case in `punishments.json`
#       - Create embed via `create_log_embed()`
#       - Log via `log_action()`

# ===========================================
# SECTION 7 — ECONOMY SYSTEM
# ===========================================

import random

economy_file = "data/economy.json"

# Load or create JSON
if os.path.exists(economy_file):
    with open(economy_file, "r") as f:
        economy = json.load(f)
else:
    economy = {}

def save_economy():
    with open(economy_file, "w") as f:
        json.dump(economy, f, indent=4)

def get_user_data(guild_id, user_id):
    guild_data = economy.setdefault(str(guild_id), {})
    user_data = guild_data.setdefault(str(user_id), {"wallet": 0, "bank": 0})
    return user_data

# ------------------------------
# /balance
# ------------------------------
@tree.command(name="balance", description="Check your balance.")
@app_commands.describe(member="Optional member to check")
async def balance_cmd(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    user_data = get_user_data(interaction.guild.id, member.id)
    embed = discord.Embed(
        title=f"💰 {member.display_name}'s Balance",
        color=discord.Color.gold()
    )
    embed.add_field(name="Wallet", value=f"${user_data['wallet']}", inline=True)
    embed.add_field(name="Bank", value=f"${user_data['bank']}", inline=True)
    embed.set_thumbnail(url=member.display_avatar.url)
    await interaction.response.send_message(embed=embed)

# ------------------------------
# /work
# ------------------------------
@tree.command(name="work", description="Work and earn money.")
async def work_cmd(interaction: discord.Interaction):
    user_data = get_user_data(interaction.guild.id, interaction.user.id)
    earnings = random.randint(50, 300)
    user_data['wallet'] += earnings
    save_economy()
    embed = discord.Embed(
        title="💼 Work Completed",
        description=f"You worked hard and earned **${earnings}**!",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)

# ------------------------------
# /rob
# ------------------------------
@tree.command(name="rob", description="Attempt to rob another user.")
@app_commands.describe(target="User to rob")
async def rob_cmd(interaction: discord.Interaction, target: discord.Member):
    if target.id == interaction.user.id:
        return await interaction.response.send_message("❌ You cannot rob yourself.", ephemeral=True)

    user_data = get_user_data(interaction.guild.id, interaction.user.id)
    target_data = get_user_data(interaction.guild.id, target.id)

    if target_data['wallet'] < 100:
        return await interaction.response.send_message("❌ Target does not have enough money to rob.", ephemeral=True)

    success = random.choice([True, False])
    if success:
        stolen = random.randint(50, min(200, target_data['wallet']))
        user_data['wallet'] += stolen
        target_data['wallet'] -= stolen
        save_economy()
        embed = discord.Embed(
            title="💰 Robbery Successful",
            description=f"You successfully robbed **{target.display_name}** for **${stolen}**!",
            color=discord.Color.green()
        )
    else:
        penalty = random.randint(20, min(100, user_data['wallet']))
        user_data['wallet'] -= penalty
        target_data['wallet'] += penalty  # Optional: reward target
        save_economy()
        embed = discord.Embed(
            title="❌ Robbery Failed",
            description=f"You got caught! Paid **${penalty}** as penalty.",
            color=discord.Color.red()
        )
    await interaction.response.send_message(embed=embed)

# ------------------------------
# /deposit
# ------------------------------
@tree.command(name="deposit", description="Deposit money into your bank.")
@app_commands.describe(amount="Amount to deposit, or 'all'")
async def deposit_cmd(interaction: discord.Interaction, amount: str):
    user_data = get_user_data(interaction.guild.id, interaction.user.id)
    wallet = user_data['wallet']

    if amount.lower() == "all":
        deposit_amount = wallet
    else:
        try:
            deposit_amount = int(amount)
        except:
            return await interaction.response.send_message("❌ Invalid amount.", ephemeral=True)
        if deposit_amount > wallet:
            return await interaction.response.send_message("❌ You don't have that much in wallet.", ephemeral=True)

    user_data['wallet'] -= deposit_amount
    user_data['bank'] += deposit_amount
    save_economy()

    embed = discord.Embed(
        title="🏦 Deposit Successful",
        description=f"You deposited **${deposit_amount}** into your bank.",
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed)

# ------------------------------
# /withdraw
# ------------------------------
@tree.command(name="withdraw", description="Withdraw money from your bank.")
@app_commands.describe(amount="Amount to withdraw, or 'all'")
async def withdraw_cmd(interaction: discord.Interaction, amount: str):
    user_data = get_user_data(interaction.guild.id, interaction.user.id)
    bank = user_data['bank']

    if amount.lower() == "all":
        withdraw_amount = bank
    else:
        try:
            withdraw_amount = int(amount)
        except:
            return await interaction.response.send_message("❌ Invalid amount.", ephemeral=True)
        if withdraw_amount > bank:
            return await interaction.response.send_message("❌ You don't have that much in bank.", ephemeral=True)

    user_data['wallet'] += withdraw_amount
    user_data['bank'] -= withdraw_amount
    save_economy()

    embed = discord.Embed(
        title="🏦 Withdraw Successful",
        description=f"You withdrew **${withdraw_amount}** from your bank.",
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed)

# ------------------------------
# Integration Notes
# ------------------------------
# 1. All economy data stored in `data/economy.json`.
# 2. Supports slash commands only.
# 3. All embeds professional and consistent with Elura branding.
# 4. Can extend with /gamble, /leaderboard, /shop later.

# ===========================================
# SECTION 8 — HELP SYSTEM (PROFESSIONAL)
# ===========================================

import discord
from discord.ui import Select, View

# Command categories with descriptions and optional restricted flag
HELP_CATEGORIES = {
    "General": [
        {"name": "/setup", "description": "Configure server channels and settings."},
        {"name": "/balance", "description": "Check your wallet and bank balance."},
        {"name": "/work", "description": "Work to earn coins."},
        {"name": "/rob", "description": "Attempt to rob another member."},
    ],
    "Moderation": [
        {"name": "/warn", "description": "Issue a warning to a member.", "restricted": True},
        {"name": "/warnings", "description": "View a member's warnings.", "restricted": True},
        {"name": "/unwarn", "description": "Remove a warning from a member.", "restricted": True},
        {"name": "/mute", "description": "Mute a member temporarily.", "restricted": True},
        {"name": "/kick", "description": "Kick a member from the server.", "restricted": True},
        {"name": "/ban", "description": "Ban a member from the server.", "restricted": True},
        {"name": "/unban", "description": "Unban a member.", "restricted": True},
    ],
    "Economy": [
        {"name": "/balance", "description": "View wallet and bank balance."},
        {"name": "/deposit", "description": "Deposit money into bank."},
        {"name": "/withdraw", "description": "Withdraw money from bank."},
    ],
    "Utilities": [
        {"name": "/tr", "description": "Translate a message to English."},
        {"name": "/count", "description": "Check counting channel stats."},
    ],
    "Counting": [
        {"name": "Counting Channel", "description": "Send numbers in sequence. Bot reacts ✅/❌ and tracks progress."},
    ]
}

class HelpDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=category, description=f"View {len(HELP_CATEGORIES[category])} commands")
            for category in HELP_CATEGORIES
        ]
        super().__init__(placeholder="Select a command category...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        commands = HELP_CATEGORIES[category]

        embed = discord.Embed(
            title=f"📖 {category} Commands",
            description=f"Showing {len(commands)} command(s) in this category.",
            color=discord.Color.blurple()
        )
        for cmd in commands:
            name = cmd["name"]
            desc = cmd["description"]
            restricted = "🔒" if cmd.get("restricted") else ""
            embed.add_field(name=f"{name} {restricted}", value=desc, inline=False)

        embed.set_footer(text="Elura Utility • Commands professional, clear, and up-to-date")
        await interaction.response.edit_message(embed=embed, view=self.view)

class HelpView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(HelpDropdown())

# ------------------------------
# /help
# ------------------------------
@tree.command(name="help", description="Display the professional help menu with all commands.")
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📖 Elura Utility • Help Menu",
        description="Select a category from the dropdown below to see detailed commands.\n🔒 = Restricted command",
        color=discord.Color.blurple()
    )
    embed.set_footer(text="Elura Utility • Professional and clean interface")
    await interaction.response.send_message(embed=embed, view=HelpView())
