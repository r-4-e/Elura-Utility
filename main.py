# ============================================================
#                         ELURA UTILITY
#                     All-In-One main.py
#         Ultra-Professional Discord Utility Framework
# ============================================================

import discord
from discord.ext import commands, tasks
from discord import app_commands, Embed, Interaction, File
from deep_translator import GoogleTranslator
from dotenv import load_dotenv

import json
import os
import aiofiles

# ===========================================
# ALL-IN-ONE JSON FILE
# ===========================================
ALLIANCE_FILE = "alliance.json"

# Default structure
default_alliance = {
    "bot": {
        "token": "",
        "founder_role": "1438894978230259793"
    },
    "punishment_roles": {
        "tier1": [],
        "tier2": [],
        "tier3": [],
        "tier4": []
    },
    "guild_settings": {
        "guild_id": None,
        "welcome_channel": None,
        "leave_channel": None,
        "logs_channel": None,
        "count_channel": None,
        "economy_channel": None,
        "welcome_message": "Welcome **{usermention}**! You’ve successfully joined **{guildname}**. We hope you enjoy your stay.",
        "leave_message": "**{usermention}** has left **{guildname}**. We hope to see them again in the future.",
        "welcome_color": "#1e466f",
        "leave_color": "#ff3b3b"
    },
    "economy": {
        "starting_balance": 0,
        "work_min": 50,
        "work_max": 150,
        "rob_min": 20,
        "rob_max": 200,
        "cooldowns": {"work": 3600, "rob": 7200},
        "users": {}
    },
    "punishments": {
        "cases": [],
        "last_case_id": 0
    },
    "counting": {
        "current_number": 0,
        "last_user": None
    },
    "other": {}
}

# -------------------------------------------
# Load alliance.json safely
# -------------------------------------------
def load_alliance():
    if not os.path.exists(ALLIANCE_FILE):
        with open(ALLIANCE_FILE, "w") as f:
            json.dump(default_alliance, f, indent=4)
        return default_alliance

    try:
        with open(ALLIANCE_FILE, "r") as f:
            data = json.load(f)
            # Ensure all top-level keys exist
            for key, value in default_alliance.items():
                if key not in data:
                    data[key] = value
            return data
    except (json.JSONDecodeError, ValueError):
        with open(ALLIANCE_FILE, "w") as f:
            json.dump(default_alliance, f, indent=4)
        return default_alliance

# -------------------------------------------
# Save alliance.json
# -------------------------------------------
def save_alliance(data):
    with open(ALLIANCE_FILE, "w") as f:
        json.dump(data, f, indent=4)

# -------------------------------------------
# Async helpers for reading/writing JSON sections
# -------------------------------------------
async def read_json_section(section: str):
    data = load_alliance()
    return data.get(section, {})

async def write_json_section(section: str, value):
    data = load_alliance()
    data[section] = value
    save_alliance(data)

# ===========================================
# Load on startup
# ===========================================
alliance = load_alliance()

# Bot & roles
TOKEN = alliance["bot"]["token"]
FOUNDER_ROLE = alliance["bot"]["founder_role"]
TIER1 = alliance["punishment_roles"].get("tier1", [])
TIER2 = alliance["punishment_roles"].get("tier2", [])
TIER3 = alliance["punishment_roles"].get("tier3", [])
TIER4 = alliance["punishment_roles"].get("tier4", [])

# Guild channels & messages
WELCOME_CHANNEL = alliance["guild_settings"].get("welcome_channel")
LEAVE_CHANNEL = alliance["guild_settings"].get("leave_channel")
LOGS_CHANNEL = alliance["guild_settings"].get("logs_channel")
COUNT_CHANNEL = alliance["guild_settings"].get("count_channel")
ECONOMY_CHANNEL = alliance["guild_settings"].get("economy_channel")

WELCOME_MESSAGE = alliance["guild_settings"].get("welcome_message")
LEAVE_MESSAGE = alliance["guild_settings"].get("leave_message")
WELCOME_COLOR = alliance["guild_settings"].get("welcome_color", "#1e466f")
LEAVE_COLOR = alliance["guild_settings"].get("leave_color", "#ff3b3b")

# Economy
STARTING_BALANCE = alliance["economy"].get("starting_balance", 0)
WORK_MIN = alliance["economy"].get("work_min", 50)
WORK_MAX = alliance["economy"].get("work_max", 150)
ROB_MIN = alliance["economy"].get("rob_min", 20)
ROB_MAX = alliance["economy"].get("rob_max", 200)
COOLDOWNS = alliance["economy"].get("cooldowns", {"work": 3600, "rob": 7200})
USERS_ECONOMY = alliance["economy"].get("users", {})

# Punishments
PUNISHMENTS = alliance["punishments"].get("cases", [])
LAST_CASE_ID = alliance["punishments"].get("last_case_id", 0)

# Counting
COUNTING = alliance.get("counting", {})

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
    data = load_alliance()
    return data.get("punishments", {})

async def save_punishments(punishment_data):
    data = load_alliance()
    data["punishments"] = punishment_data
    save_alliance(data)

async def get_economy():
    data = load_alliance()
    return data.get("economy", {})

async def save_economy(economy_data):
    data = load_alliance()
    data["economy"] = economy_data
    save_alliance(data)

async def get_counting():
    data = load_alliance()
    return data.get("counting", {})

async def save_counting(count_data):
    data = load_alliance()
    data["counting"] = count_data
    save_alliance(data)
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

    # Wait for setup to finish
    await v.wait()

    # Load current alliance.json
    current = load_alliance()

    # Update guild settings
    for key, value in v.result.items():
        if value is not None:
            current["guild_settings"][key] = value

    # Save updated alliance.json
    save_alliance(current)

    await interaction.followup.send(
        embed=success_embed("Setup complete! Elura Utility is now fully configured."),
        ephemeral=True
    )

# ============================================================
#                   WELCOME / LEAVE SYSTEM
# ============================================================

WELCOME_COLOR = int(alliance["guild_settings"].get("welcome_color", "#1e466f")[1:], 16)
LEAVE_COLOR = int(alliance["guild_settings"].get("leave_color", "#ff3b3b")[1:], 16)

@bot.event
async def on_member_join(member: discord.Member):
    try:
        channel_id = alliance["guild_settings"].get("welcome_channel")
        if not channel_id:
            return

        channel = member.guild.get_channel(int(channel_id))
        if not channel:
            return

        embed = discord.Embed(
            title=f"Welcome to {member.guild.name}!",
            description=alliance["guild_settings"]["welcome_message"].format(
                usermention=member.mention,
                guildname=member.guild.name
            ),
            color=WELCOME_COLOR
        )

        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Member #{member.guild.member_count}")
        embed.timestamp = datetime.datetime.utcnow()

        await channel.send(embed=embed)

    except Exception as e:
        print(f"Welcome error: {e}")


@bot.event
async def on_member_remove(member: discord.Member):
    try:
        channel_id = alliance["guild_settings"].get("leave_channel")
        if not channel_id:
            return

        channel = member.guild.get_channel(int(channel_id))
        if not channel:
            return

        embed = discord.Embed(
            title="Member Left",
            description=alliance["guild_settings"]["leave_message"].format(
                usermention=member.mention,
                guildname=member.guild.name
            ),
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

    if message.author.bot:
        return

    count_channel_id = alliance["guild_settings"].get("count_channel")
    if not count_channel_id or message.channel.id != int(count_channel_id):
        return await bot.process_commands(message)

    # Load counting section from alliance.json
    count_data = alliance.get("counting", {})
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
        return await bot.process_commands(message)

    # Same user as last → wrong
    if last_user == str(message.author.id):
        await message.add_reaction("❌")
        await message.reply(
            f"{message.author.mention} RUINED IT AT **{num}**!! Next number is **1**. **Wrong number.**"
        )
        count_data[guild_id]["current"] = 0
        count_data[guild_id]["last_user"] = None
        alliance["counting"] = count_data
        save_alliance(alliance)
        return await bot.process_commands(message)

    # Correct number
    if num == current + 1:
        await message.add_reaction("✅")
        count_data[guild_id]["current"] = num
        count_data[guild_id]["last_user"] = str(message.author.id)
        alliance["counting"] = count_data
        save_alliance(alliance)

    else:
        # Wrong number → reset
        await message.add_reaction("❌")
        await message.reply(
            f"{message.author.mention} RUINED IT AT **{num}**!! Next number is **1**. **Wrong number.**"
        )
        count_data[guild_id]["current"] = 0
        count_data[guild_id]["last_user"] = None
        alliance["counting"] = count_data
        save_alliance(alliance)

    await bot.process_commands(message)
    
# ===========================================
# SECTION 6 — PART 1: WARNINGS SYSTEM (All-in-One JSON)
# ===========================================

import discord
from discord import app_commands
from discord.ext import commands
import uuid
import datetime

# Helper functions for all-in-one alliance.json
def new_case_id():
    return str(uuid.uuid4())[:8].upper()

def now_utc():
    return datetime.datetime.utcnow().strftime("%Y-%m-%d • %H:%M UTC")

def get_user_tier(member: discord.Member):
    for role in member.roles:
        if str(role.id) in TIER1 + TIER2 + TIER3 + TIER4:
            return str(role.id)
    if str(FOUNDER) in [str(r.id) for r in member.roles]:
        return "FOUNDER"
    return None

def has_permission(member: discord.Member, command: str):
    tier = get_user_tier(member)
    if tier is None:
        return False
    if tier == "FOUNDER":
        return True
    role_commands = {}
    for t, roles in zip(["tier1","tier2","tier3","tier4"], [TIER1,TIER2,TIER3,TIER4]):
        for r in roles:
            role_commands[str(r)] = {
                "tier1": ["warn"],
                "tier2": ["warn","warnings"],
                "tier3": ["warn","warnings","mute"],
                "tier4": ["warn","warnings","mute","kick","ban","unban"]
            }[t]
    return command in role_commands.get(tier, [])

async def log_action(guild: discord.Guild, embed: discord.Embed):
    if LOGS_CHANNEL:
        channel = guild.get_channel(int(LOGS_CHANNEL))
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

    # Initialize punishments
    if "punishments" not in alliance:
        alliance["punishments"] = {"cases": [], "last_case_id": 0}
    if guild_id not in alliance["punishments"]:
        alliance["punishments"]["cases"] = []

    # Add case
    data = {
        "case": case_id,
        "type": "warn",
        "user": member.id,
        "moderator": interaction.user.id,
        "reason": reason,
        "timestamp": now_utc()
    }
    alliance["punishments"]["cases"].append(data)
    alliance["punishments"]["last_case_id"] += 1
    save_alliance(alliance)

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
    all_cases = alliance.get("punishments", {}).get("cases", [])
    user_cases = [c for c in all_cases if c["user"] == member.id]

    warn_count = sum(1 for c in user_cases if c["type"] == "warn")
    mute_count = sum(1 for c in user_cases if c["type"] == "mute")
    kick_count = sum(1 for c in user_cases if c["type"] == "kick")
    ban_count = sum(1 for c in user_cases if c["type"] == "ban")

    embed = discord.Embed(title="📄 Punishment History", color=discord.Color.blurple())
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="User", value=f"{member.mention}\n`{member.id}`", inline=False)
    embed.add_field(name="Totals", value=f"⚠️ Warned: {warn_count}\n🔇 Muted: {mute_count}\n👢 Kicked: {kick_count}\n⛔ Banned: {ban_count}", inline=False)

    if not user_cases:
        embed.add_field(name="Cases", value="No punishments found.", inline=False)
    else:
        text = ""
        for c in user_cases:
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

        guild_cases = alliance.get("punishments", {}).get("cases", [])
        case_data = next((c for c in guild_cases if c["case"] == self.case_id), None)
        if not case_data:
            return await interaction.response.edit_message(content="❌ Case already removed.", view=None)

        guild_cases.remove(case_data)
        save_alliance(alliance)

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
    guild_cases = alliance.get("punishments", {}).get("cases", [])
    if not any(c["case"] == case_id for c in guild_cases):
        return await interaction.response.send_message("❌ Invalid case ID.", ephemeral=True)

    view = ConfirmUnwarn(interaction.user, guild_id, case_id)
    await interaction.response.send_message(f"Are you sure you want to remove case `{case_id}`?", view=view, ephemeral=True)

# ===========================================
# SECTION 6 — PART 2: MODERATION COMMANDS (All-in-One JSON)
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

    # Record punishment in alliance.json
    case_id = new_case_id()
    guild_id = str(interaction.guild.id)
    if "punishments" not in alliance:
        alliance["punishments"] = {"cases": [], "last_case_id": 0}
    alliance["punishments"]["cases"].append({
        "case": case_id,
        "type": "mute",
        "user": member.id,
        "moderator": interaction.user.id,
        "reason": reason,
        "timestamp": now_utc(),
        "duration": minutes
    })
    alliance["punishments"]["last_case_id"] += 1
    save_alliance(alliance)

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
    if "punishments" not in alliance:
        alliance["punishments"] = {"cases": [], "last_case_id": 0}
    alliance["punishments"]["cases"].append({
        "case": case_id,
        "type": "kick",
        "user": member.id,
        "moderator": interaction.user.id,
        "reason": reason,
        "timestamp": now_utc()
    })
    alliance["punishments"]["last_case_id"] += 1
    save_alliance(alliance)

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
    if "punishments" not in alliance:
        alliance["punishments"] = {"cases": [], "last_case_id": 0}
    alliance["punishments"]["cases"].append({
        "case": case_id,
        "type": "ban",
        "user": member.id,
        "moderator": interaction.user.id,
        "reason": reason,
        "timestamp": now_utc()
    })
    alliance["punishments"]["last_case_id"] += 1
    save_alliance(alliance)

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
    if "punishments" not in alliance:
        alliance["punishments"] = {"cases": [], "last_case_id": 0}
    alliance["punishments"]["cases"].append({
        "case": case_id,
        "type": "unban",
        "user": target.id,
        "moderator": interaction.user.id,
        "reason": reason,
        "timestamp": now_utc()
    })
    alliance["punishments"]["last_case_id"] += 1
    save_alliance(alliance)

    embed = discord.Embed(title="✅ User Unbanned", color=discord.Color.green())
    embed.add_field(name="User", value=f"{target} (`{target.id}`)")
    embed.add_field(name="Reason", value=reason)
    embed.add_field(name="Case ID", value=case_id)
    embed.set_footer(text=f"Issued by {interaction.user} • {now_utc()}")
    await interaction.response.send_message(embed=embed)
    await log_action(interaction.guild, embed)
    
 # ===========================================
# SECTION 6 — PART 3: LOGGING & UTILITIES (All-in-One)
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
# Centralized punishment JSON functions
# ------------------------------
def get_guild_cases(guild_id: str):
    """Return list of cases for a guild from alliance.json"""
    if "punishments" not in alliance:
        alliance["punishments"] = {"cases": [], "last_case_id": 0}
    return [c for c in alliance["punishments"]["cases"] if str(c.get("guild_id")) == guild_id]

def add_case(guild_id: str, case_data: dict):
    """Add a punishment case to alliance.json"""
    if "punishments" not in alliance:
        alliance["punishments"] = {"cases": [], "last_case_id": 0}
    case_data["guild_id"] = guild_id
    alliance["punishments"]["cases"].append(case_data)
    alliance["punishments"]["last_case_id"] += 1
    save_alliance(alliance)

def remove_case(guild_id: str, case_id: str):
    """Remove a punishment case by ID from alliance.json"""
    guild_cases = [c for c in alliance["punishments"]["cases"] if str(c.get("guild_id")) == guild_id]
    case = next((c for c in guild_cases if c["case"] == case_id), None)
    if case:
        alliance["punishments"]["cases"].remove(case)
        save_alliance(alliance)
        return case
    return None

# ------------------------------
# Integration Notes
# ------------------------------
# 1. All moderation commands (/warn, /mute, /kick, /ban, /unban) now:
#    - Use `add_case()` to save in alliance.json
#    - Use `remove_case()` to remove
#    - Use `create_log_embed()` for embeds
#    - Call `await log_action(guild, embed)` to send log
#
# 2. Permissions handled via `has_permission()`
#
# 3. No separate JSON files required.
#
# 4. This keeps all punishment data in one clean, professional JSON file.

# ===========================================  
# SECTION 7 — ECONOMY SYSTEM (All-in-One with alliances.json)  
# ===========================================

import random
import os
import json
from discord import app_commands
import discord

alliance_file = "data/alliances.json"

# Load or create alliances.json
if os.path.exists(alliance_file):
    with open(alliance_file, "r") as f:
        alliance = json.load(f)
else:
    alliance = {}

def save_alliance(data):
    with open(alliance_file, "w") as f:
        json.dump(data, f, indent=4)

def get_user_data(guild_id, user_id):
    """Return or create user economy data inside alliances.json"""
    guild_data = alliance.setdefault(str(guild_id), {})
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
    save_alliance(alliance)
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
        save_alliance(alliance)
        embed = discord.Embed(
            title="💰 Robbery Successful",
            description=f"You successfully robbed **{target.display_name}** for **${stolen}**!",
            color=discord.Color.green()
        )
    else:
        penalty = random.randint(20, min(100, user_data['wallet']))
        user_data['wallet'] -= penalty
        target_data['wallet'] += penalty
        save_alliance(alliance)
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
    save_alliance(alliance)

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
    save_alliance(alliance)

    embed = discord.Embed(
        title="🏦 Withdraw Successful",
        description=f"You withdrew **${withdraw_amount}** from your bank.",
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed)

# ------------------------------
# /gamble
# ------------------------------
@tree.command(name="gamble", description="Gamble money from your wallet.")
@app_commands.describe(amount="Amount to gamble")
async def gamble_cmd(interaction: discord.Interaction, amount: int):
    user_data = get_user_data(interaction.guild.id, interaction.user.id)
    wallet = user_data['wallet']

    if amount > wallet:
        return await interaction.response.send_message("❌ You don't have that much in wallet.", ephemeral=True)

    win = random.choice([True, False])
    if win:
        winnings = int(amount * random.uniform(1.2, 2.0))
        user_data['wallet'] += winnings
        result_text = f"You won **${winnings}**!"
        color = discord.Color.green()
    else:
        user_data['wallet'] -= amount
        result_text = f"You lost **${amount}**."
        color = discord.Color.red()

    save_alliance(alliance)
    embed = discord.Embed(title="🎰 Gamble Result", description=result_text, color=color)
    await interaction.response.send_message(embed=embed)

# ------------------------------
# /leaderboard
# ------------------------------
@tree.command(name="leaderboard", description="Show wallet leaderboard for this guild.")
async def leaderboard_cmd(interaction: discord.Interaction):
    guild_data = alliance.get(str(interaction.guild.id), {})
    leaderboard = sorted(guild_data.items(), key=lambda x: x[1].get("wallet", 0), reverse=True)
    embed = discord.Embed(title="🏆 Wallet Leaderboard", color=discord.Color.gold())
    for i, (user_id, data) in enumerate(leaderboard[:10], start=1):
        member = interaction.guild.get_member(int(user_id))
        name = member.display_name if member else f"User ID {user_id}"
        embed.add_field(name=f"{i}. {name}", value=f"${data.get('wallet', 0)}", inline=False)
    await interaction.response.send_message(embed=embed)

# ------------------------------
# /shop
# ------------------------------
shop_items = {
    "VIP": 500,
    "Special Role": 300,
    "Custom Title": 200
}

@tree.command(name="shop", description="View or buy items from the shop.")
@app_commands.describe(item="Item to buy (optional)")
async def shop_cmd(interaction: discord.Interaction, item: str = None):
    user_data = get_user_data(interaction.guild.id, interaction.user.id)
    if not item:
        embed = discord.Embed(title="🛒 Shop", color=discord.Color.blue())
        for name, price in shop_items.items():
            embed.add_field(name=name, value=f"${price}", inline=False)
        await interaction.response.send_message(embed=embed)
    else:
        item_price = shop_items.get(item)
        if not item_price:
            return await interaction.response.send_message("❌ Item not found.", ephemeral=True)
        if user_data['wallet'] < item_price:
            return await interaction.response.send_message("❌ You don't have enough money.", ephemeral=True)
        user_data['wallet'] -= item_price
        save_alliance(alliance)
        await interaction.response.send_message(f"✅ You bought **{item}** for **${item_price}**!")

# ------------------------------
# Notes
# ------------------------------
# 1. All economy data stored inside `alliances.json`.
# 2. Supports slash commands only.
# 3. Combines /balance, /work, /rob, /deposit, /withdraw, /gamble, /leaderboard, /shop.
# 4. All embeds professional and consistent with branding.

# ===========================================
# SECTION 8 — HELP SYSTEM (DYNAMIC & PROFESSIONAL)
# ===========================================

import discord
from discord.ui import Select, View
import json
import os

# ------------------------------
# Load alliances.json
# ------------------------------
ALLIANCE_FILE = "data/alliances.json"

def load_alliance():
    if os.path.exists(ALLIANCE_FILE):
        with open(ALLIANCE_FILE, "r") as f:
            return json.load(f)
    return {}

alliance = load_alliance()

# ------------------------------
# Dynamic economy settings
# ------------------------------
ECONOMY_SETTINGS = alliance.get("economy", {})
STARTING_BALANCE = ECONOMY_SETTINGS.get("starting_balance", 0)
WORK_MIN = ECONOMY_SETTINGS.get("work_min", 50)
WORK_MAX = ECONOMY_SETTINGS.get("work_max", 150)
ROB_MIN = ECONOMY_SETTINGS.get("rob_min", 20)
ROB_MAX = ECONOMY_SETTINGS.get("rob_max", 200)
SHOP_ITEMS = ECONOMY_SETTINGS.get("shop", [])
COOLDOWNS = ECONOMY_SETTINGS.get("cooldowns", {"work": 3600, "rob": 7200})

# ------------------------------
# Command categories
# ------------------------------
HELP_CATEGORIES = {
    "General": [
        {"name": "/setup", "description": "Configure server channels and settings."},
        {"name": "/balance", "description": f"Check your wallet and bank balance. Starting balance: ${STARTING_BALANCE}."},
        {"name": "/work", "description": f"Work to earn coins ({WORK_MIN}-{WORK_MAX})."},
        {"name": "/rob", "description": f"Attempt to rob another member ({ROB_MIN}-{ROB_MAX})."},
        {"name": "/gamble", "description": "Gamble your coins for a chance to win big."},
        {"name": "/bet", "description": "Place a bet on a game or outcome."},
        {"name": "/bj", "description": "Play blackjack against the bot."},
        {"name": "/shop", "description": f"View items available in the shop ({len(SHOP_ITEMS)} items)."},
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
    "Utilities": [
        {"name": "/tr", "description": "Translate a message to English."},
        {"name": "/count", "description": "Check counting channel stats."},
    ],
    "Counting": [
        {"name": "Counting Channel", "description": "Send numbers in sequence. Bot reacts ✅/❌ and tracks progress."},
    ]
}

# ------------------------------
# Help dropdown & view
# ------------------------------
class HelpDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=category, 
                description=f"View {len(HELP_CATEGORIES[category])} commands"
            )
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
# /help command
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
    
# ------------------------------
# On Ready Event
# ------------------------------
@bot.event
async def on_ready():
    print(f"\n✅ Logged in as {bot.user} ({bot.user.id})")
    print(f"🌐 Connected to {len(bot.guilds)} guild(s)")
    print(f"⌚ Startup time: {now_utc()}\n")

    # Send a professional ready embed to the log channel if set
    if log_channel_id:
        try:
            guild = bot.get_guild(int(guild_id)) if guild_id else None
            log_channel = guild.get_channel(int(log_channel_id)) if guild else None
            if log_channel:
                embed = discord.Embed(
                    title="🤖 Elura Utility • Bot Online",
                    description=f"Bot **{bot.user.name}** is now online and ready!",
                    color=discord.Color.green(),
                    timestamp=datetime.now(timezone.utc)
                )
                embed.add_field(name="Servers Connected", value=str(len(bot.guilds)), inline=True)
                embed.add_field(name="Startup Time", value=now_utc(), inline=True)
                embed.set_footer(text="Elura Utility • Professional Bot Startup")
                await log_channel.send(embed=embed)
        except Exception as e:
            print(f"⚠️ Failed to send ready embed: {e}")

# ------------------------------
# Run Bot
# ------------------------------
token = alliance.get("bot", {}).get("token")

if token:
    bot.run(token)
else:
    print("❌ No token found in data/alliances.json! Please add your bot token under alliance['bot']['token'].")
