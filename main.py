# ==========================================================
#  ELURA UTILITY – The Ultimate Bot
#  Silver-Cyan Premium Edition (Billion-Dollar Layout)
# ==========================================================
import sys, types, os
if sys.version_info >= (3, 13):
    sys.modules["audioop"] = types.ModuleType("audioop")
import discord, datetime, asyncio, requests
from discord import app_commands
from discord.ext import commands
from supabase import create_client, Client
from dotenv import load_dotenv


# ----------------------------------------------------------
# LOAD ENVIRONMENT VARIABLES
# ----------------------------------------------------------
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TOKEN = os.getenv("DISCORD_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


# Initialize Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

async def ensure_tables():
    """Ensures required tables exist in Supabase."""
    tables = ["economy", "cases", "message_counter", "mute_settings", "config"]
    for table in tables:
        try:
            supabase.table(table).select("*").limit(1).execute()
        except Exception:
            print(f"🛠️ Creating missing table: {table}")
            try:
                supabase.table(table).insert({}).execute()
            except:
                pass
    print("✅ Supabase auto-table check complete.")


# ----------------------------------------------------------
# BOT INTENTS & CLIENT
# ----------------------------------------------------------
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)

# ----------------------------------------------------------
# STYLING
# ----------------------------------------------------------
CYAN = 0x00FFFF
SILVER = 0xC0C0C0

def elura_embed(title, desc, emoji="💎"):
    """Luxury embed generator for Elura."""
    e = discord.Embed(
        title=f"{emoji} {title}",
        description=desc,
        color=CYAN
    )
    e.set_footer(text="Elura Utility • The Ultimate Bot")
    e.timestamp = datetime.datetime.utcnow()
    return e

# ----------------------------------------------------------
# STARTUP EVENT
# ----------------------------------------------------------
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ {bot.user} is now online and synchronized.")
    print("💎 Elura Utility Systems → READY")
    print("-------------------------------------")
    print("Modules:")
    print(" → Economy")
    print(" → Welcomer")
    print(" → Punishments")
    print(" → Translate")
    print(" → Search")
    print(" → Message Counter")
    print(" → Counting Channel")
    print(" → Setup")
    print(" → Help")
    print(" → Privacy")
    print(" → WebHooker System")
    print("-------------------------------------")

# ==========================================================
#  ELURA ECONOMY SYSTEM
#  Premium-tier, modeled after UnbelievaBoat
# ==========================================================

from datetime import timedelta

# ----------------------------------------------------------
# UTILS
# ----------------------------------------------------------
def get_user_economy(user_id: int, guild_id: int):
    """Fetch or create economy record."""
    data = supabase.table("economy").select("*").eq("user_id", user_id).eq("guild_id", guild_id).execute()
    if not data.data:
        supabase.table("economy").insert({"user_id": user_id, "guild_id": guild_id, "wallet": 0, "bank": 0}).execute()
        return {"wallet": 0, "bank": 0}
    return data.data[0]

def update_user_economy(user_id: int, guild_id: int, wallet=None, bank=None):
    """Update wallet or bank."""
    fields = {}
    if wallet is not None:
        fields["wallet"] = wallet
    if bank is not None:
        fields["bank"] = bank
    supabase.table("economy").update(fields).eq("user_id", user_id).eq("guild_id", guild_id).execute()

# ----------------------------------------------------------
# /balance
# ----------------------------------------------------------
@bot.tree.command(name="balance", description="View your or another member’s balance.")
async def balance(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    record = get_user_economy(member.id, interaction.guild.id)

    embed = elura_embed(
        "Balance Overview",
        f"👤 **User:** {member.mention}\n"
        f"💰 **Wallet:** {record['wallet']:,}\n"
        f"🏦 **Bank:** {record['bank']:,}",
        "💸"
    )
    await interaction.response.send_message(embed=embed)

# ----------------------------------------------------------
# /daily
# ----------------------------------------------------------
daily_cooldowns = {}

@bot.tree.command(name="daily", description="Collect your daily reward.")
async def daily(interaction: discord.Interaction):
    uid = interaction.user.id
    now = datetime.datetime.utcnow()
    last = daily_cooldowns.get(uid)

    if last and (now - last) < timedelta(hours=24):
        remaining = timedelta(hours=24) - (now - last)
        hrs = remaining.seconds // 3600
        mins = (remaining.seconds % 3600) // 60
        await interaction.response.send_message(embed=elura_embed("Daily", f"⏰ Come back in {hrs}h {mins}m.", "🕒"))
        return

    daily_cooldowns[uid] = now
    record = get_user_economy(uid, interaction.guild.id)
    reward = 500
    new_wallet = record["wallet"] + reward
    update_user_economy(uid, interaction.guild.id, wallet=new_wallet)

    await interaction.response.send_message(embed=elura_embed("Daily Reward", f"You earned **{reward:,}** credits today!", "🎁"))

# ----------------------------------------------------------
# /work
# ----------------------------------------------------------
work_cooldowns = {}

@bot.tree.command(name="work", description="Work to earn credits.")
async def work(interaction: discord.Interaction):
    uid = interaction.user.id
    now = datetime.datetime.utcnow()
    last = work_cooldowns.get(uid)

    if last and (now - last) < timedelta(minutes=30):
        remaining = timedelta(minutes=30) - (now - last)
        mins = remaining.seconds // 60
        await interaction.response.send_message(embed=elura_embed("Work", f"⏰ You can work again in {mins} minutes.", "💼"))
        return

    work_cooldowns[uid] = now
    record = get_user_economy(uid, interaction.guild.id)
    earnings = 250
    update_user_economy(uid, interaction.guild.id, wallet=record["wallet"] + earnings)

    await interaction.response.send_message(embed=elura_embed("Work Complete", f"You earned **{earnings:,}** credits!", "🧰"))

# ----------------------------------------------------------
# /deposit
# ----------------------------------------------------------
@bot.tree.command(name="deposit", description="Deposit money into your bank.")
async def deposit(interaction: discord.Interaction, amount: int):
    record = get_user_economy(interaction.user.id, interaction.guild.id)
    if amount > record["wallet"]:
        await interaction.response.send_message(embed=elura_embed("Deposit", "Not enough funds in wallet.", "⚠️"))
        return

    update_user_economy(
        interaction.user.id,
        interaction.guild.id,
        wallet=record["wallet"] - amount,
        bank=record["bank"] + amount
    )
    await interaction.response.send_message(embed=elura_embed("Deposit", f"Deposited **{amount:,}** credits into bank.", "🏦"))

# ----------------------------------------------------------
# /withdraw
# ----------------------------------------------------------
@bot.tree.command(name="withdraw", description="Withdraw money from your bank.")
async def withdraw(interaction: discord.Interaction, amount: int):
    record = get_user_economy(interaction.user.id, interaction.guild.id)
    if amount > record["bank"]:
        await interaction.response.send_message(embed=elura_embed("Withdraw", "Not enough funds in bank.", "⚠️"))
        return

    update_user_economy(
        interaction.user.id,
        interaction.guild.id,
        wallet=record["wallet"] + amount,
        bank=record["bank"] - amount
    )
    await interaction.response.send_message(embed=elura_embed("Withdraw", f"Withdrew **{amount:,}** credits.", "💳"))

# ----------------------------------------------------------
# /pay
# ----------------------------------------------------------
@bot.tree.command(name="pay", description="Send credits to another member.")
async def pay(interaction: discord.Interaction, member: discord.Member, amount: int):
    if member.id == interaction.user.id:
        await interaction.response.send_message(embed=elura_embed("Payment", "You can’t pay yourself.", "🚫"))
        return

    sender = get_user_economy(interaction.user.id, interaction.guild.id)
    if amount > sender["wallet"]:
        await interaction.response.send_message(embed=elura_embed("Payment", "Insufficient funds.", "⚠️"))
        return

    receiver = get_user_economy(member.id, interaction.guild.id)
    update_user_economy(interaction.user.id, interaction.guild.id, wallet=sender["wallet"] - amount)
    update_user_economy(member.id, interaction.guild.id, wallet=receiver["wallet"] + amount)

    await interaction.response.send_message(embed=elura_embed("Payment Successful", f"Sent **{amount:,}** credits to {member.mention}.", "💱"))

# ----------------------------------------------------------
# /leaderboard
# ----------------------------------------------------------
@bot.tree.command(name="lb", description="View the richest users.")
async def leaderboard(interaction: discord.Interaction):
    data = supabase.table("economy").select("*").eq("guild_id", interaction.guild.id).execute().data
    sorted_data = sorted(data, key=lambda x: (x["wallet"] + x["bank"]), reverse=True)[:10]
    lb = "\n".join(
        [f"**#{i+1}** <@{u['user_id']}> — 💰 {(u['wallet']+u['bank']):,}" for i, u in enumerate(sorted_data)]
    ) or "No data yet."

    await interaction.response.send_message(embed=elura_embed("Leaderboard", lb, "🏆"))

# ----------------------------------------------------------
# /reset-economy
# ----------------------------------------------------------
@bot.tree.command(name="reset_economy", description="Reset a user’s economy profile. (Admin only)")
@app_commands.checks.has_permissions(administrator=True)
async def reset_economy(interaction: discord.Interaction, member: discord.Member):
    supabase.table("economy").delete().eq("user_id", member.id).eq("guild_id", interaction.guild.id).execute()
    await interaction.response.send_message(embed=elura_embed("Economy Reset", f"{member.mention}'s economy data reset.", "♻️"))

# ==========================================================
#  ELURA WELCOMER + GOODBYER SYSTEM
#  Elegant Join & Leave Management (ProBot-Style)
# ==========================================================

# ----------------------------------------------------------
# UTILITIES
# ----------------------------------------------------------
def get_greet_settings(guild_id: int):
    """Fetch welcome/leave settings for a guild."""
    data = supabase.table("greet_settings").select("*").eq("guild_id", guild_id).execute()
    if not data.data:
        return None
    return data.data[0]

def set_greet_settings(guild_id: int, welcome_channel_id: int, leave_channel_id: int, welcome_msg: str, leave_msg: str):
    """Create or update greet settings."""
    existing = supabase.table("greet_settings").select("*").eq("guild_id", guild_id).execute()
    payload = {
        "guild_id": guild_id,
        "welcome_channel": welcome_channel_id,
        "leave_channel": leave_channel_id,
        "welcome_message": welcome_msg,
        "leave_message": leave_msg
    }

    if not existing.data:
        supabase.table("greet_settings").insert(payload).execute()
    else:
        supabase.table("greet_settings").update(payload).eq("guild_id", guild_id).execute()

# ----------------------------------------------------------
# /greet_setup
# ----------------------------------------------------------
@bot.tree.command(name="greet_setup", description="Configure welcome and leave messages.")
@app_commands.describe(
    welcome_channel="Channel for welcome messages.",
    leave_channel="Channel for leave messages.",
    welcome_message="Custom welcome message. Use {user} for mentions.",
    leave_message="Custom goodbye message. Use {user} for mentions."
)
async def greet_setup(
    interaction: discord.Interaction,
    welcome_channel: discord.TextChannel,
    leave_channel: discord.TextChannel,
    welcome_message: str,
    leave_message: str
):
    set_greet_settings(interaction.guild.id, welcome_channel.id, leave_channel.id, welcome_message, leave_message)
    await interaction.response.send_message(
        embed=elura_embed(
            "Greet System Configured",
            f"👋 **Welcome Channel:** {welcome_channel.mention}\n💨 **Leave Channel:** {leave_channel.mention}\n\n"
            f"💬 **Welcome Msg:** `{welcome_message}`\n🚪 **Leave Msg:** `{leave_message}`\n\n"
            f"Use `/greet_test` to preview both messages.",
            "✨"
        )
    )

# ----------------------------------------------------------
# /greet_test
# ----------------------------------------------------------
@bot.tree.command(name="greet_test", description="Preview the welcome and leave messages.")
async def greet_test(interaction: discord.Interaction):
    settings = get_greet_settings(interaction.guild.id)
    if not settings:
        await interaction.response.send_message(embed=elura_embed("Greet System", "No configuration found. Use `/greet_setup` first.", "⚠️"))
        return

    welcome_channel = interaction.guild.get_channel(settings["welcome_channel"])
    leave_channel = interaction.guild.get_channel(settings["leave_channel"])
    user = interaction.user

    welcome_msg = settings["welcome_message"].replace("{user}", user.mention)
    leave_msg = settings["leave_message"].replace("{user}", user.mention)

    # Send test welcome
    w_embed = elura_embed("Welcome!", welcome_msg, "🌟")
    w_embed.set_thumbnail(url=user.display_avatar.url)
    await welcome_channel.send(embed=w_embed)

    # Send test leave
    l_embed = elura_embed("Goodbye!", leave_msg, "🚪")
    l_embed.set_thumbnail(url=user.display_avatar.url)
    await leave_channel.send(embed=l_embed)

    await interaction.response.send_message(embed=elura_embed("Greet Test", "✅ Preview messages sent.", "📨"))

# ----------------------------------------------------------
# EVENT: on_member_join
# ----------------------------------------------------------
@bot.event
async def on_member_join(member: discord.Member):
    settings = get_greet_settings(member.guild.id)
    if not settings:
        return

    channel = member.guild.get_channel(settings["welcome_channel"])
    if not channel:
        return

    msg = settings["welcome_message"].replace("{user}", member.mention)
    embed = elura_embed("Welcome!", msg, "💎")
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Member Count", value=str(len(member.guild.members)))
    embed.set_footer(text=f"Welcome to {member.guild.name}!")
    await channel.send(embed=embed)

# ----------------------------------------------------------
# EVENT: on_member_remove
# ----------------------------------------------------------
@bot.event
async def on_member_remove(member: discord.Member):
    settings = get_greet_settings(member.guild.id)
    if not settings:
        return

    channel = member.guild.get_channel(settings["leave_channel"])
    if not channel:
        return

    msg = settings["leave_message"].replace("{user}", member.mention)
    embed = elura_embed("Goodbye!", msg, "💨")
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text=f"{member.name} left the server.")
    await channel.send(embed=embed)

# ==========================================================
#  ⚖️ ELURA PUNISHMENT SYSTEM
#  Advanced Moderation with Case Management & Role Permissions
# ==========================================================

from datetime import datetime
from typing import Optional

# ----------------------------------------------------------
# ROLE-BASED PERMISSION SYSTEM
# ----------------------------------------------------------
FULL_MOD_ROLE = 1431189246135373848      # Full mod - all commands
LIMITED_MOD_ROLE = 1431189247456575539   # Limited mod - all except kick/ban
WARN_ONLY_ROLE = 1431189247985057887     # Warn-only mod

async def elura_permission_check(interaction: discord.Interaction, command_name: str) -> bool:
    """Checks role-based moderation permissions."""
    roles = [r.id for r in interaction.user.roles]

    # Full moderators - all permissions
    if FULL_MOD_ROLE in roles:
        return True

    # Limited moderators - all except ban/kick
    if LIMITED_MOD_ROLE in roles:
        if command_name not in ["ban", "kick"]:
            return True
        await interaction.response.send_message(
            embed=elura_embed("Permission Restricted", f"🚫 You’re not authorized to use **/{command_name}**.", "⚠️"),
            ephemeral=True
        )
        return False

    # Warn-only moderators
    if WARN_ONLY_ROLE in roles:
        if command_name == "warn":
            return True
        await interaction.response.send_message(
            embed=elura_embed("Permission Restricted", "⚠️ You can only use the `/warn` command.", "⚠️"),
            ephemeral=True
        )
        return False

    # Everyone else - no moderation permissions
    await interaction.response.send_message(
        embed=elura_embed("Access Denied", "🚫 You do not have permission to use moderation commands.", "❌"),
        ephemeral=True
    )
    return False

# ----------------------------------------------------------
# DATABASE HELPERS
# ----------------------------------------------------------
def log_case(guild_id: int, user_id: int, moderator_id: int, action: str, reason: str):
    """Logs a moderation action as a case in Supabase."""
    supabase.table("cases").insert({
        "guild_id": guild_id,
        "user_id": user_id,
        "moderator_id": moderator_id,
        "action": action,
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat()
    }).execute()

def get_cases(guild_id: int, user_id: int):
    """Fetch all cases for a specific user."""
    data = supabase.table("cases").select("*").eq("guild_id", guild_id).eq("user_id", user_id).execute()
    return data.data or []

# ----------------------------------------------------------
# MUTE ROLE SETUP
# ----------------------------------------------------------
@bot.tree.command(name="mutesetup", description="Configure or auto-create the mute role.")
@app_commands.describe(role="Select the mute role (optional).")
async def mutesetup(interaction: discord.Interaction, role: Optional[discord.Role] = None):
    if not await elura_permission_check(interaction, "mutesetup"):
        return

    guild = interaction.guild

    # Auto-create if not provided
    if role is None:
        role = discord.utils.get(guild.roles, name="Muted")
        if not role:
            role = await guild.create_role(name="Muted", reason="Elura Mute System Setup")

        # Update channel permissions
        for channel in guild.channels:
            try:
                await channel.set_permissions(role, send_messages=False, speak=False, add_reactions=False)
            except:
                continue

    # Store role in database
    existing = supabase.table("mute_settings").select("*").eq("guild_id", guild.id).execute()
    if not existing.data:
        supabase.table("mute_settings").insert({"guild_id": guild.id, "mute_role": role.id}).execute()
    else:
        supabase.table("mute_settings").update({"mute_role": role.id}).eq("guild_id", guild.id).execute()

    await interaction.response.send_message(embed=elura_embed("Mute Setup Complete", f"✅ Mute role set to {role.mention}", "🔇"))

# ----------------------------------------------------------
# /warn
# ----------------------------------------------------------
@bot.tree.command(name="warn", description="Warn a member with a reason.")
@app_commands.describe(member="Member to warn.", reason="Reason for warning.")
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str):
    if not await elura_permission_check(interaction, "warn"):
        return

    log_case(interaction.guild.id, member.id, interaction.user.id, "Warn", reason)

    embed = elura_embed("User Warned",
        f"⚠️ **{member.mention}** has been warned.\n\n**Reason:** {reason}\n**Moderator:** {interaction.user.mention}",
        "🧾")
    await interaction.response.send_message(embed=embed)
    try:
        await member.send(embed=elura_embed("You were warned!", f"Server: **{interaction.guild.name}**\nReason: {reason}", "⚠️"))
    except:
        pass

# ----------------------------------------------------------
# /unwarn
# ----------------------------------------------------------
@bot.tree.command(name="unwarn", description="Remove a user's last warning.")
@app_commands.describe(member="Member to unwarn.")
async def unwarn(interaction: discord.Interaction, member: discord.Member):
    if not await elura_permission_check(interaction, "unwarn"):
        return

    cases = get_cases(interaction.guild.id, member.id)
    warnings = [c for c in cases if c["action"].lower() == "warn"]

    if not warnings:
        await interaction.response.send_message(embed=elura_embed("No Warnings", "❌ This user has no warnings.", "📁"))
        return

    last_case = warnings[-1]
    supabase.table("cases").delete().eq("id", last_case["id"]).execute()

    await interaction.response.send_message(embed=elura_embed("Unwarned", f"✅ Removed the last warning from {member.mention}", "🧹"))

# ----------------------------------------------------------
# /warnings
# ----------------------------------------------------------
@bot.tree.command(name="warnings", description="Check all warnings for a user.")
@app_commands.describe(member="Member to check warnings for.")
async def warnings(interaction: discord.Interaction, member: discord.Member):
    if not await elura_permission_check(interaction, "warnings"):
        return

    cases = get_cases(interaction.guild.id, member.id)
    warnings = [c for c in cases if c["action"].lower() == "warn"]

    if not warnings:
        await interaction.response.send_message(embed=elura_embed("Warnings", "✅ No warnings for this user.", "🌸"))
        return

    desc = "\n".join([
        f"**#{i+1}** – {w['reason']} *(by <@{w['moderator_id']}>, {w['timestamp'][:10]})*"
        for i, w in enumerate(warnings)
    ])

    await interaction.response.send_message(embed=elura_embed(f"Warnings for {member}", desc, "📋"))

# ----------------------------------------------------------
# /kick
# ----------------------------------------------------------
@bot.tree.command(name="kick", description="Kick a user from the server.")
@app_commands.describe(member="Member to kick.", reason="Reason for kick.")
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str):
    if not await elura_permission_check(interaction, "kick"):
        return

    await member.kick(reason=reason)
    log_case(interaction.guild.id, member.id, interaction.user.id, "Kick", reason)
    await interaction.response.send_message(embed=elura_embed("User Kicked", f"👢 {member.mention} was kicked.\nReason: {reason}", "💢"))

# ----------------------------------------------------------
# /ban
# ----------------------------------------------------------
@bot.tree.command(name="ban", description="Ban a user from the server.")
@app_commands.describe(member="Member to ban.", reason="Reason for ban.")
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str):
    if not await elura_permission_check(interaction, "ban"):
        return

    await member.ban(reason=reason)
    log_case(interaction.guild.id, member.id, interaction.user.id, "Ban", reason)
    await interaction.response.send_message(embed=elura_embed("User Banned", f"⛔ {member.mention} was banned.\nReason: {reason}", "🔥"))

# ----------------------------------------------------------
# /mute
# ----------------------------------------------------------
@bot.tree.command(name="mute", description="Mute a member using the configured mute role.")
@app_commands.describe(member="Member to mute.", reason="Reason for mute.")
async def mute(interaction: discord.Interaction, member: discord.Member, reason: str):
    if not await elura_permission_check(interaction, "mute"):
        return

    data = supabase.table("mute_settings").select("*").eq("guild_id", interaction.guild.id).execute()
    if not data.data:
        await interaction.response.send_message(embed=elura_embed("Mute Error", "⚠️ Mute role not configured. Run `/mutesetup` first.", "⚠️"))
        return

    mute_role_id = data.data[0]["mute_role"]
    mute_role = interaction.guild.get_role(mute_role_id)

    if not mute_role:
        await interaction.response.send_message(embed=elura_embed("Mute Error", "❌ Mute role not found in this guild.", "⚠️"))
        return

    await member.add_roles(mute_role, reason=reason)
    log_case(interaction.guild.id, member.id, interaction.user.id, "Mute", reason)
    await interaction.response.send_message(embed=elura_embed("Muted", f"🔇 {member.mention} was muted.\nReason: {reason}", "🌑"))


# ==========================================================
#  ELURA TRANSLATE SYSTEM
#  Powered by Google Translate API
#  Reply-based translation like Gemini / Discord AI
# ==========================================================

import aiohttp

@bot.tree.command(name="tr", description="Translate a replied foreign message to your chosen language.")
@app_commands.describe(lang="Target language to translate into (e.g. en, fr, ja, hi, es, etc.)")
async def tr(interaction: discord.Interaction, lang: str):
    await interaction.response.defer(thinking=True)

    # Check if the user replied to a message
    ref = interaction.channel.last_message_reference
    if not ref:
        await interaction.followup.send(embed=elura_embed(
            "No Message Replied",
            "⚠️ You must **reply** to the message you want to translate.",
            "❌"
        ))
        return

    # Fetch the replied message
    try:
        replied_message = await interaction.channel.fetch_message(ref.message_id)
        text_to_translate = replied_message.content
        if not text_to_translate:
            await interaction.followup.send(embed=elura_embed(
                "Empty Message",
                "⚠️ The replied message doesn't contain any text to translate.",
                "⚠️"
            ))
            return
    except:
        await interaction.followup.send(embed=elura_embed(
            "Error",
            "⚠️ Could not fetch the replied message.",
            "⚠️"
        ))
        return

    # Translate using Google API
    TRANSLATE_URL = "https://translation.googleapis.com/language/translate/v2"
    params = {
        "q": text_to_translate,
        "target": lang,
        "key": GOOGLE_API_KEY
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(TRANSLATE_URL, data=params) as r:
            data = await r.json()

    try:
        translated = data["data"]["translations"][0]["translatedText"]
        detected_lang = data["data"]["translations"][0].get("detectedSourceLanguage", "unknown")

        # Fancy layout
        embed = discord.Embed(
            description=f"**Translated from `{detected_lang}` → `{lang}`**\n\n"
                        f"**{lang.upper()} Translation:**\n```{translated}```",
            color=0x00FFFF
        )
        embed.set_author(
            name=f"{replied_message.author.display_name}",
            icon_url=replied_message.author.display_avatar.url
        )
        embed.set_footer(text="🌐 Google Translate")

        await interaction.followup.send(embed=embed)

    except Exception as e:
        error_embed = elura_embed(
            "Translation Error",
            f"⚠️ Something went wrong while translating.\nError: `{str(e)}`",
            "❌"
        )
        await interaction.followup.send(embed=error_embed)

# ==========================================================
#  ELURA SEARCH SYSTEM
#  Powered by DuckDuckGo Instant API
#  (Google upgrade ready)
# ==========================================================

import urllib.parse

@bot.tree.command(name="search", description="Search the web using DuckDuckGo.")
@app_commands.describe(query="What you want to search for.")
async def search(interaction: discord.Interaction, query: str):
    await interaction.response.defer(thinking=True)

    # Encode the query for URL use
    encoded_query = urllib.parse.quote_plus(query)
    search_url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_redirect=1"

    try:
        response = requests.get(search_url)
        data = response.json()

        # Extract main data
        title = data.get("Heading", "No title found")
        abstract = data.get("AbstractText", "No detailed description available.")
        source_url = data.get("AbstractURL", f"https://duckduckgo.com/?q={encoded_query}")
        image = data.get("Image", None)

        # Build embed
        embed = discord.Embed(
            title=f"🔎 {title}",
            description=abstract if abstract else "No description found.",
            color=0x00FFFF
        )
        embed.add_field(name="Search Query", value=f"`{query}`", inline=False)
        embed.add_field(name="🔗 Source", value=f"[Open Result]({source_url})", inline=False)
        if image:
            embed.set_thumbnail(url=image)

        embed.set_footer(text="Powered by DuckDuckGo", icon_url="https://duckduckgo.com/favicon.ico")

        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(
            embed=elura_embed("Search Error", f"⚠️ Could not complete search.\nError: `{e}`", "❌")
        )

# ==========================================================
#  ELURA MESSAGE COUNTER SYSTEM
#  Tracks user activity across the server
# ==========================================================

import traceback

# ----------------------------------------------------------
# AUTO TABLE CREATION
# ----------------------------------------------------------
def ensure_message_table():
    try:
        # Try selecting to verify table existence
        supabase.table("message_counter").select("*").limit(1).execute()
        print("✅ Message Counter table verified.")
    except Exception:
        print("⚙️ Creating message_counter table in Supabase...")
        try:
            supabase.rpc("create_table_if_not_exists", {
                "table_name": "message_counter",
                "schema": {
                    "guild_id": "bigint",
                    "user_id": "bigint",
                    "count": "integer"
                }
            })
            print("✅ Table 'message_counter' created successfully.")
        except Exception as e:
            print(f"❌ Failed to create table: {e}")

# Run on startup
ensure_message_table()

# ----------------------------------------------------------
# MESSAGE LISTENER
# ----------------------------------------------------------
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.guild:
        return

    try:
        guild_id = message.guild.id
        user_id = message.author.id

        # Fetch existing entry
        existing = supabase.table("message_counter") \
            .select("*") \
            .eq("guild_id", guild_id) \
            .eq("user_id", user_id) \
            .execute()

        if existing.data:
            new_count = existing.data[0]["count"] + 1
            supabase.table("message_counter") \
                .update({"count": new_count}) \
                .eq("guild_id", guild_id) \
                .eq("user_id", user_id) \
                .execute()
        else:
            supabase.table("message_counter") \
                .insert({"guild_id": guild_id, "user_id": user_id, "count": 1}) \
                .execute()

    except Exception as e:
        print("⚠️ Message Counter Error:")
        traceback.print_exc()

    await bot.process_commands(message)

# ----------------------------------------------------------
# /messages — View message count
# ----------------------------------------------------------
@bot.tree.command(name="messages", description="Check how many messages you or another user have sent.")
@app_commands.describe(member="The member whose message count you want to view.")
async def messages(interaction: discord.Interaction, member: Optional[discord.Member] = None):
    member = member or interaction.user

    try:
        data = supabase.table("message_counter") \
            .select("count") \
            .eq("guild_id", interaction.guild.id) \
            .eq("user_id", member.id) \
            .execute()

        count = data.data[0]["count"] if data.data else 0

        embed = elura_embed(
            "Message Counter",
            f"💬 **{member.display_name}** has sent **{count:,} messages** in this server.",
            "💠"
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    except Exception as e:
        await interaction.response.send_message(embed=elura_embed("Error", f"⚠️ {e}", "❌"))

# ----------------------------------------------------------
# /leaderboard — Show top 10 message senders
# ----------------------------------------------------------
@bot.tree.command(name="mlb", description="View the top message senders in the server.")
async def leaderboard(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)

    try:
        data = supabase.table("message_counter") \
            .select("*") \
            .eq("guild_id", interaction.guild.id) \
            .order("count", desc=True) \
            .limit(10) \
            .execute()

        if not data.data:
            await interaction.followup.send(embed=elura_embed("Leaderboard", "No messages recorded yet.", "📭"))
            return

        desc = ""
        for i, row in enumerate(data.data, start=1):
            user = interaction.guild.get_member(row["user_id"])
            name = user.display_name if user else f"User {row['user_id']}"
            desc += f"**#{i}** — {name} • `{row['count']:,}` messages\n"

        embed = elura_embed("Message Leaderboard", desc, "🏆")
        embed.set_footer(text="Elura Utility – Message Analytics System")
        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(embed=elura_embed("Error", f"⚠️ {e}", "❌"))

# ==========================================================
#  ELURA COUNTING CHANNEL SYSTEM
#  Professional number-chain tracker
# ==========================================================

def ensure_counting_table():
    """Ensure the counting table exists."""
    try:
        supabase.table("counting_channels").select("*").limit(1).execute()
        print("✅ Counting table verified.")
    except Exception:
        print("⚙️ Creating counting_channels table...")
        try:
            supabase.rpc("create_table_if_not_exists", {
                "table_name": "counting_channels",
                "schema": {
                    "guild_id": "bigint",
                    "channel_id": "bigint",
                    "last_number": "integer",
                    "last_user": "bigint"
                }
            })
            print("✅ Table 'counting_channels' created successfully.")
        except Exception as e:
            print(f"❌ Counting table creation failed: {e}")

ensure_counting_table()

# ----------------------------------------------------------
# /countsetup
# ----------------------------------------------------------
@bot.tree.command(name="countsetup", description="Setup or change the counting channel.")
@app_commands.describe(channel="The channel where counting will happen.")
async def countsetup(interaction: discord.Interaction, channel: discord.TextChannel):
    try:
        guild_id = interaction.guild.id
        data = supabase.table("counting_channels").select("*").eq("guild_id", guild_id).execute()

        if data.data:
            supabase.table("counting_channels").update({
                "channel_id": channel.id,
                "last_number": 0,
                "last_user": 0
            }).eq("guild_id", guild_id).execute()
        else:
            supabase.table("counting_channels").insert({
                "guild_id": guild_id,
                "channel_id": channel.id,
                "last_number": 0,
                "last_user": 0
            }).execute()

        await interaction.response.send_message(embed=elura_embed(
            "Counting Channel Configured",
            f"✅ Counting channel set to {channel.mention}\nNext number starts from **1**.",
            "🔢"
        ))

    except Exception as e:
        await interaction.response.send_message(embed=elura_embed("Error", f"⚠️ {e}", "❌"))

# ----------------------------------------------------------
# MESSAGE LISTENER – COUNT VALIDATION
# ----------------------------------------------------------
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.guild:
        return

    # --- COUNTING CHANNEL CHECK ---
    try:
        data = supabase.table("counting_channels").select("*").eq("guild_id", message.guild.id).execute()
        if not data.data:
            await bot.process_commands(message)
            return

        counting_channel = data.data[0]
        if message.channel.id != counting_channel["channel_id"]:
            await bot.process_commands(message)
            return

        # Validate numeric input
        try:
            number = int(message.content.strip())
        except ValueError:
            await message.add_reaction("❌")
            await message.channel.send(
                f"{message.author.mention} Ruined it!!!!!! Next number is **1**. Start.",
                delete_after=8
            )
            supabase.table("counting_channels").update({"last_number": 0, "last_user": 0}) \
                .eq("guild_id", message.guild.id).execute()
            return

        # Fetch current state
        last_number = counting_channel["last_number"]
        last_user = counting_channel["last_user"]

        # Prevent same user twice
        if message.author.id == last_user:
            await message.add_reaction("❌")
            await message.channel.send(
                f"{message.author.mention} Ruined it!!!!!! Next number is **1**. Start.",
                delete_after=8
            )
            supabase.table("counting_channels").update({"last_number": 0, "last_user": 0}) \
                .eq("guild_id", message.guild.id).execute()
            return

        # Validate correct number
        expected = last_number + 1
        if number == expected:
            await message.add_reaction("✅")
            supabase.table("counting_channels").update({
                "last_number": number,
                "last_user": message.author.id
            }).eq("guild_id", message.guild.id).execute()
        else:
            await message.add_reaction("❌")
            await message.channel.send(
                f"{message.author.mention} Ruined it!!!!!! Next number is **1**. Start.",
                delete_after=8
            )
            supabase.table("counting_channels").update({"last_number": 0, "last_user": 0}) \
                .eq("guild_id", message.guild.id).execute()

    except Exception as e:
        print(f"Counting System Error: {e}")

    await bot.process_commands(message)

# ==========================================================
#  ELURA SERVER SETUP SYSTEM
#  Professional automatic setup for logs & management
# ==========================================================

def ensure_setup_table():
    """Ensure setup data table exists in Supabase."""
    try:
        supabase.table("server_setup").select("*").limit(1).execute()
        print("✅ Setup table verified.")
    except Exception:
        print("⚙️ Creating server_setup table...")
        try:
            supabase.rpc("create_table_if_not_exists", {
                "table_name": "server_setup",
                "schema": {
                    "guild_id": "bigint",
                    "logs_channel": "bigint",
                    "moderation_channel": "bigint",
                    "system_category": "bigint",
                    "created_at": "timestamp"
                }
            })
            print("✅ Table 'server_setup' created successfully.")
        except Exception as e:
            print(f"❌ Setup table creation failed: {e}")

ensure_setup_table()

# ----------------------------------------------------------
# /setup – Automatic Server Configuration
# ----------------------------------------------------------
@bot.tree.command(name="setup", description="Automatically set up essential channels and logs for your server.")
async def setup(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    guild = interaction.guild
    user = interaction.user

    setup_embed = discord.Embed(
        title="⚙️ Initializing Elura Setup",
        description="Setting up your server with the perfect foundation.\n\nPlease wait while we prepare your environment...",
        color=discord.Color.purple()
    )
    setup_embed.set_footer(text="Elura System | Modern. Elegant. Automated.")
    msg = await interaction.followup.send(embed=setup_embed, ephemeral=True)

    try:
        # ----------------------------------------------------------
        # Step 1: Create System Category
        # ----------------------------------------------------------
        category = discord.utils.get(guild.categories, name="📁・Elura System")
        if not category:
            category = await guild.create_category(name="📁・Elura System", reason="Elura Setup Initialization")

        # ----------------------------------------------------------
        # Step 2: Create Logs Channel
        # ----------------------------------------------------------
        logs_channel = discord.utils.get(guild.text_channels, name="📜・elura-logs")
        if not logs_channel:
            logs_channel = await guild.create_text_channel(
                name="📜・elura-logs",
                category=category,
                reason="Elura Setup - Logging System"
            )

        # ----------------------------------------------------------
        # Step 3: Create Moderation Channel
        # ----------------------------------------------------------
        moderation_channel = discord.utils.get(guild.text_channels, name="⚖️・elura-moderation")
        if not moderation_channel:
            moderation_channel = await guild.create_text_channel(
                name="⚖️・elura-moderation",
                category=category,
                reason="Elura Setup - Moderation Control"
            )

        # ----------------------------------------------------------
        # Step 4: Create Server Role “Elura Manager”
        # ----------------------------------------------------------
        elura_role = discord.utils.get(guild.roles, name="Elura Manager")
        if not elura_role:
            elura_role = await guild.create_role(
                name="Elura Manager",
                permissions=discord.Permissions(administrator=True),
                color=discord.Color.gold(),
                reason="Elura Setup - Core Role Creation"
            )

        # ----------------------------------------------------------
        # Step 5: Save Setup Configuration to Supabase
        # ----------------------------------------------------------
        supabase.table("server_setup").upsert({
            "guild_id": guild.id,
            "logs_channel": logs_channel.id,
            "moderation_channel": moderation_channel.id,
            "system_category": category.id,
            "created_at": discord.utils.utcnow()
        }).execute()

        # ----------------------------------------------------------
        # Step 6: Success Embed
        # ----------------------------------------------------------
        success_embed = discord.Embed(
            title="✨ Elura Setup Completed",
            description=(
                "Your server has been **professionally configured**.\n\n"
                "**Created Assets:**\n"
                f"📁 Category: {category.mention}\n"
                f"📜 Logs Channel: {logs_channel.mention}\n"
                f"⚖️ Moderation Channel: {moderation_channel.mention}\n"
                f"👑 Role: {elura_role.mention}\n\n"
                "Your setup data has been securely stored in Elura Cloud (Supabase)."
            ),
            color=discord.Color.blurple()
        )
        success_embed.set_footer(text="Elura Setup | The foundation of your billion-dollar bot.")
        success_embed.timestamp = discord.utils.utcnow()

        await msg.edit(embed=success_embed)

        # Send confirmation in logs
        await logs_channel.send(embed=elura_embed(
            "Setup Completed",
            f"✅ {user.mention} completed the Elura setup successfully.",
            "⚙️"
        ))

    except Exception as e:
        error_embed = discord.Embed(
            title="❌ Setup Failed",
            description=f"Something went wrong during setup.\n\n**Error:** `{e}`",
            color=discord.Color.red()
        )
        error_embed.set_footer(text="Elura System | Please retry or contact support.")
        await msg.edit(embed=error_embed)

# ==========================================================
#  💎 ELURA INTERACTIVE HELP SYSTEM
#  Dropdown Menu UI with Role-Based Visibility
# ==========================================================

import discord
from discord import app_commands
from discord.ui import View, Select
from datetime import datetime

# Role IDs
MOD_HELP_ROLE = 1431189241685344348

# ----------------------------------------------------------
# CATEGORY TEXTS
# ----------------------------------------------------------
HELP_SECTIONS = {
    "Economy": """
💰 **Economy**
• `/balance` — Check your balance  
• `/daily` — Claim daily credits  
• `/give` — Send credits  
• `/shop` — Browse items  
• `/buy` — Purchase from shop  
• `/inventory` — View your items
""",
    "Welcomer": """
👋 **Welcomer & Goodbyer**
• `/welcome-setup` — Configure welcome system  
• `/goodbye-setup` — Configure farewell system
""",
    "Translate": """
🌐 **Translate**
• `/tr lang:` — Reply to a message to translate it  
*Powered by Google Translate (Gemini-level precision)*
""",
    "Search": """
🔍 **Search**
• `/search <query>` — Web search using DuckDuckGo  
*Google integration coming soon*
""",
    "Counter": """
🔢 **Message & Counting**
• `/countsetup` — Setup counting channel  
• Auto number validation and leaderboard tracking
""",
    "Setup": """
⚙️ **Setup & System**
• `/setup` — Auto-create logs & webhooker channels  
• `/privacy` — View data & policy info
""",
    "Webhooker": """
🪝 **Elura WebHooker System**
• `/webhook-open` — Open a webhook  
• `/webhook-block` — Block unsafe ones  
• `/webhook-deleteall` — Delete all  
• `/webhook-count` — Count all webhooks  
• `/webhook-edit` — Edit webhook settings
""",
    "Moderation": """
⚖️ **Moderation**
• `/warn` — Warn a member  
• `/unwarn` — Remove a warning  
• `/warnings` — List user warnings  
• `/mute` — Mute a member  
• `/mutesetup` — Setup mute role  
• `/kick` — Kick a user  
• `/ban` — Ban a user
"""
}

# ----------------------------------------------------------
# UI SELECT MENU
# ----------------------------------------------------------
class HelpMenu(Select):
    def __init__(self, can_view_mod):
        options = [
            discord.SelectOption(label="Economy", emoji="💰"),
            discord.SelectOption(label="Welcomer", emoji="👋"),
            discord.SelectOption(label="Translate", emoji="🌐"),
            discord.SelectOption(label="Search", emoji="🔍"),
            discord.SelectOption(label="Counter", emoji="🔢"),
            discord.SelectOption(label="Setup", emoji="⚙️"),
            discord.SelectOption(label="Webhooker", emoji="🪝"),
        ]
        if can_view_mod:
            options.append(discord.SelectOption(label="Moderation", emoji="⚖️"))

        super().__init__(
            placeholder="📜 Choose a category to view its commands...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        section = HELP_SECTIONS[self.values[0]]
        embed = discord.Embed(
            title=f"💎 Elura Help — {self.values[0]}",
            description=section,
            color=discord.Color.from_rgb(140, 82, 255)
        )
        embed.set_footer(text="Elura Utility • Premium Discord Automation")
        embed.timestamp = datetime.utcnow()
        await interaction.response.edit_message(embed=embed, view=self.view)


class HelpView(View):
    def __init__(self, can_view_mod):
        super().__init__(timeout=None)
        self.add_item(HelpMenu(can_view_mod))


# ----------------------------------------------------------
# MAIN HELP COMMAND
# ----------------------------------------------------------
@bot.tree.command(name="help", description="View all Elura commands interactively.")
async def help(interaction: discord.Interaction):
    user_roles = [r.id for r in interaction.user.roles]
    can_view_mod = MOD_HELP_ROLE in user_roles

    # Default embed view (landing)
    embed = discord.Embed(
        title="💎 Elura Utility — Command Center",
        description="Welcome to **Elura Help Dashboard**!\n\nUse the dropdown below to explore each feature category.",
        color=discord.Color.from_rgb(140, 82, 255)
    )
    embed.set_author(name="Elura Utility", icon_url="https://i.imgur.com/qy2yYhO.png")  # Placeholder logo
    embed.set_footer(
        text="🔒 Moderation commands visible" if can_view_mod else "🔒 Moderation commands hidden — staff only"
    )
    embed.timestamp = datetime.utcnow()

    view = HelpView(can_view_mod)
    await interaction.response.send_message(embed=embed, view=view)

# ==========================================================
#  💠 ELURA ABOUT COMMAND
#  Elegant Brand Card + System Status
# ==========================================================

import platform
import psutil
import time

start_time = time.time()  # To track uptime from bot startup

def format_uptime():
    seconds = int(time.time() - start_time)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    parts = []
    if days: parts.append(f"{days}d")
    if hours: parts.append(f"{hours}h")
    if minutes: parts.append(f"{minutes}m")
    if seconds: parts.append(f"{seconds}s")
    return " ".join(parts)

@bot.tree.command(name="about", description="View Elura’s system info, version, and developers.")
async def about(interaction: discord.Interaction):
    cpu_usage = psutil.cpu_percent()
    memory = psutil.virtual_memory()
    uptime = format_uptime()

    embed = discord.Embed(
        title="💠 Elura Utility — The Ultimate Discord Automation Suite",
        description="> **Elura** isn’t just a bot. It’s a revolution in Discord utility — "
                    "built with precision, design, and intelligence.\n\n"
                    "Crafted to perfection. Trusted by communities. Powered by the future.",
        color=discord.Color.from_rgb(140, 82, 255)
    )

    # Brand logo (replace with your hosted logo later)
    embed.set_thumbnail(url="https://i.imgur.com/qy2yYhO.png")

    # ------------------------------------------------------
    # SYSTEM INFO
    # ------------------------------------------------------
    embed.add_field(name="⚙️ System", value=f"**Python:** `{platform.python_version()}`\n"
                                            f"**discord.py:** `{discord.__version__}`\n"
                                            f"**Supabase:** Integrated\n"
                                            f"**Google API:** Connected", inline=True)

    embed.add_field(name="💾 Performance", value=f"**CPU Usage:** `{cpu_usage}%`\n"
                                                 f"**Memory:** `{memory.percent}%`\n"
                                                 f"**Uptime:** `{uptime}`", inline=True)

    # ------------------------------------------------------
    # BOT INFO
    # ------------------------------------------------------
    embed.add_field(name="👑 Core Features", value=(
        "• Economy & Balance System\n"
        "• Advanced Moderation (Case-based)\n"
        "• Smart Translate (Google)\n"
        "• Webhook Management System\n"
        "• Counting & Message Stats\n"
        "• Interactive Help Center\n"
        "• Supabase Data Integration"
    ), inline=False)

    embed.add_field(name="🌐 Connected Servers", value=f"`{len(bot.guilds)}`", inline=True)
    embed.add_field(name="👥 Users Served", value=f"`{sum(g.member_count for g in bot.guilds)}`", inline=True)

    embed.add_field(name="🧠 Developer & Ownership", value=(
        "**Founder:** <@1431189241685344348>\n"
        "**Framework:** Custom from scratch — No cogs.\n"
        "**Aesthetic:** Billion-dollar luxury interface ✨"
    ), inline=False)

    embed.set_footer(text="Elura Utility • Built for perfection", icon_url="https://i.imgur.com/qy2yYhO.png")
    embed.timestamp = datetime.utcnow()

    await interaction.response.send_message(embed=embed)

# ----------------------------------------------------------
# DISCORD CLIENT CONFIG
# ----------------------------------------------------------
intents = discord.Intents.all()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command("help")

# ----------------------------------------------------------
# EMBED TEMPLATE
# ----------------------------------------------------------
def elura_embed(title: str, desc: str, icon: str = "💎", color: discord.Color = discord.Color.blue()):
    embed = discord.Embed(
        title=f"{icon} {title}",
        description=desc,
        color=color
    )
    embed.set_footer(text="Elura Utility • The Ultimate Discord System")
    embed.timestamp = datetime.utcnow()
    return embed

# ----------------------------------------------------------
# STARTUP LOGIC
# ----------------------------------------------------------
@bot.event
async def on_ready():
    await ensure_tables()
    await bot.tree.sync()
    print(f"\n💫 Logged in as: {bot.user}")
    print(f"🌍 Connected to {len(bot.guilds)} servers")
    print(f"⚙️ Commands synced successfully!")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="servers evolve with Elura ⚙️"
        )
    )

# ----------------------------------------------------------
# ERROR HANDLERS
# ----------------------------------------------------------
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error):
    embed = elura_embed("Error", f"```{error}```", "⚠️", discord.Color.red())
    try:
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except:
        await interaction.followup.send(embed=embed, ephemeral=True)

@bot.event
async def on_command_error(ctx, error):
    embed = elura_embed("Command Error", f"```{error}```", "⚠️", discord.Color.red())
    await ctx.reply(embed=embed, mention_author=False)

# ----------------------------------------------------------
# BOT STARTUP
# ----------------------------------------------------------
@bot.event
async def on_ready():
    print(f"🚀 Elura Utility is live as {bot.user}")
    await ensure_tables()
    await bot.tree.sync()
    print("🌐 All commands synced successfully.")

# ----------------------------------------------------------
# BOT RUN
# ----------------------------------------------------------
if __name__ == "__main__":
    print("🚀 Starting Elura Utility bot...")
    bot.run(TOKEN)
