import os
import asyncio
import discord
from discord.ext import commands
import logging

from bot.database import Database
from bot.commands.economy import EconomyCommands
from bot.commands.admin import AdminCommands
from bot.commands.leaderboard import LeaderboardCommands
from bot.commands.inventory import InventoryCommands
from bot.commands.shop import ShopCommands
from bot.utils.constants import *

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NoMansBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            description="Ahoy! No Man's Bot - Your pirate economy companion!"
        )
        
        self.database = Database()
        
    async def setup_hook(self):
        """Called when the bot is starting up"""
        await self.database.initialize()
        
        # Add cogs
        await self.add_cog(EconomyCommands(self))
        await self.add_cog(AdminCommands(self))
        await self.add_cog(LeaderboardCommands(self))
        await self.add_cog(InventoryCommands(self))
        await self.add_cog(ShopCommands(self))
        
        # Sync slash commands
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} command(s)")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")
    
    async def on_ready(self):
        """Called when the bot is ready"""
        logger.info(f'{self.user} has come aboard! ⚓')
        logger.info(f'Bot is in {len(self.guilds)} guild(s)')
        
        # Set bot status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="the seven seas 🏴‍☠️"
        )
        await self.change_presence(activity=activity)
    
    async def on_message(self, message):
        """Handle message events for passive coin earning"""
        # Ignore bot messages
        if message.author.bot:
            return
            
        # Only process messages in guilds
        if not message.guild:
            return
            
        # Process commands first
        await self.process_commands(message)
        
        # Handle passive coin earning
        await self.handle_passive_earning(message)
    
    async def handle_passive_earning(self, message):
        """Handle passive coin earning from messages"""
        user_id = message.author.id
        guild_id = message.guild.id
        
        # Check rate limiting
        if not await self.database.can_earn_passive(user_id):
            return
            
        # Determine if user is in a crew
        crew_roles = await self.database.get_crew_roles(guild_id)
        is_crew_member = False
        user_crew = None
        
        for role in message.author.roles:
            if role.id in crew_roles:
                is_crew_member = True
                user_crew = role.name
                break
        
        # Calculate coins to award
        base_coins = BASE_PASSIVE_COINS
        if is_crew_member:
            coins = int(base_coins * CREW_BONUS_MULTIPLIER)
        else:
            coins = base_coins
        
        # Award coins
        await self.database.add_coins(user_id, coins)
        await self.database.update_passive_cooldown(user_id)
        
        # Optional: Send a subtle notification (uncomment if desired)
        # if random.randint(1, 20) == 1:  # 5% chance
        #     embed = discord.Embed(
        #         description=f"🪙 Ye found {coins} doubloons while chattin'!",
        #         color=EMBED_COLOR
        #     )
        #     await message.channel.send(embed=embed, delete_after=5)

async def main():
    """Main function to run the bot"""
    # Get token from environment
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("DISCORD_TOKEN environment variable not found!")
        return
    
    bot = NoMansBot()
    
    try:
        await bot.start(token)
    except KeyboardInterrupt:
        logger.info("Bot interrupted by user")
    except Exception as e:
        logger.error(f"Bot encountered an error: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
