import discord
from discord.ext import commands
from discord import app_commands
from bot.utils.constants import *
from bot.utils.helpers import get_user_crew, format_coins

class LeaderboardCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="leaderboard", description="View the top pirates and their crews! 🏆")
    async def leaderboard(self, interaction: discord.Interaction):
        """Display the leaderboard"""
        # Get top 10 users
        leaderboard_data = await self.bot.database.get_leaderboard(10)
        
        if not leaderboard_data:
            embed = discord.Embed(
                title="🏆 Pirate Leaderboard",
                description="No pirates have earned any doubloons yet!\n\nBe the first to claim yer treasure!",
                color=EMBED_COLOR
            )
            await interaction.response.send_message(embed=embed)
            return
        
        # Get crew roles for this guild
        crew_roles = await self.bot.database.get_crew_roles(interaction.guild.id)
        
        embed = discord.Embed(
            title="🏆 Top Pirates of the Seven Seas",
            description="The most legendary pirates and their crews:",
            color=EMBED_COLOR
        )
        
        medal_emojis = ["🥇", "🥈", "🥉"]
        
        leaderboard_text = []
        
        for i, (user_id, balance, total_earned) in enumerate(leaderboard_data):
            # Try to get the user from the guild
            user = interaction.guild.get_member(user_id)
            if not user:
                # If user not in guild, try to fetch from bot
                try:
                    user = await self.bot.fetch_user(user_id)
                    display_name = user.name
                    user_crew_name = "*Unknown*"
                except:
                    display_name = f"Unknown User ({user_id})"
                    user_crew_name = "*Unknown*"
            else:
                display_name = user.display_name
                user_crew_name = get_user_crew(user, crew_roles) or "*Lone Wolf*"
            
            # Get position emoji
            if i < 3:
                position_emoji = medal_emojis[i]
            else:
                position_emoji = f"**{i + 1}.**"
            
            # Format the entry
            entry = f"{position_emoji} **{display_name}**\n"
            entry += f"└ 💰 {format_coins(balance)} | 🏴‍☠️ {user_crew_name}"
            
            leaderboard_text.append(entry)
        
        embed.description = "\n\n".join(leaderboard_text)
        
        # Add some stats
        total_shown = len(leaderboard_data)
        total_coins_shown = sum(user[1] for user in leaderboard_data)
        
        embed.add_field(
            name="📊 Stats",
            value=f"**Pirates Shown:** {total_shown}\n**Total Treasure:** {format_coins(total_coins_shown)}",
            inline=True
        )
        
        embed.set_footer(text="Keep earnin' to climb the ranks, matey! ⚓")
        embed.set_thumbnail(url="https://cdn.jsdelivr.net/gh/twitter/twemoji@latest/assets/svg/1f3c6.svg")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="rank", description="Check yer rank among all pirates! 📊")
    async def rank(self, interaction: discord.Interaction, user: discord.Member = None):
        """Check user's rank"""
        target_user = user or interaction.user
        user_id = target_user.id
        
        # Get user's balance
        balance, total_earned = await self.bot.database.get_user_stats(user_id)
        
        if balance == 0:
            embed = discord.Embed(
                title="📊 Pirate Rank",
                description=f"{target_user.display_name} hasn't earned any doubloons yet!\n\nStart earnin' to get a rank!",
                color=EMBED_COLOR
            )
            await interaction.response.send_message(embed=embed)
            return
        
        # Get full leaderboard to find rank
        full_leaderboard = await self.bot.database.get_leaderboard(1000)
        
        user_rank = None
        for i, (lb_user_id, lb_balance, _) in enumerate(full_leaderboard):
            if lb_user_id == user_id:
                user_rank = i + 1
                break
        
        if user_rank is None:
            user_rank = "Unranked"
        
        # Get crew info
        crew_roles = await self.bot.database.get_crew_roles(interaction.guild.id)
        user_crew = get_user_crew(target_user, crew_roles)
        
        embed = discord.Embed(
            title=f"📊 {target_user.display_name}'s Pirate Rank",
            color=EMBED_COLOR
        )
        
        if isinstance(user_rank, int):
            if user_rank == 1:
                rank_emoji = "🥇"
                rank_text = f"{rank_emoji} **#{user_rank}** - *Legendary Captain!*"
            elif user_rank == 2:
                rank_emoji = "🥈"
                rank_text = f"{rank_emoji} **#{user_rank}** - *First Mate!*"
            elif user_rank == 3:
                rank_emoji = "🥉"
                rank_text = f"{rank_emoji} **#{user_rank}** - *Skilled Navigator!*"
            elif user_rank <= 10:
                rank_text = f"⭐ **#{user_rank}** - *Elite Pirate!*"
            else:
                rank_text = f"**#{user_rank}** - *Seasoned Sailor*"
        else:
            rank_text = "**Unranked** - *Landlubber*"
        
        embed.add_field(
            name="🏆 Current Rank",
            value=rank_text,
            inline=False
        )
        
        embed.add_field(
            name="💰 Current Doubloons",
            value=format_coins(balance),
            inline=True
        )
        
        embed.add_field(
            name="⚡ Total Earned",
            value=format_coins(total_earned),
            inline=True
        )
        
        if user_crew:
            embed.add_field(
                name="🏴‍☠️ Crew",
                value=f"**{user_crew}**",
                inline=True
            )
        else:
            embed.add_field(
                name="🏴‍☠️ Crew",
                value="*Lone Wolf*",
                inline=True
            )
        
        embed.set_thumbnail(url=target_user.display_avatar.url)
        embed.set_footer(text="Keep earnin' to climb the ranks!")
        
        await interaction.response.send_message(embed=embed)
