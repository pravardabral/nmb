import discord
from discord.ext import commands
from discord import app_commands
from bot.utils.constants import *

class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    def is_admin():
        """Check if user has administrator permissions"""
        def predicate(interaction: discord.Interaction) -> bool:
            return interaction.user.guild_permissions.administrator
        return app_commands.check(predicate)
    
    @app_commands.command(name="crew_roles", description="View all configured crew roles")
    @is_admin()
    async def view_crew_roles(self, interaction: discord.Interaction):
        """View all crew roles"""
        guild_id = interaction.guild.id
        crew_roles = await self.bot.database.get_crew_roles_with_names(guild_id)
        
        embed = discord.Embed(
            title="🏴‍☠️ Crew Roles Configuration",
            color=EMBED_COLOR
        )
        
        if not crew_roles:
            embed.description = "No crew roles configured yet, cap'n!\n\nUse `/add_crew_role` to add some."
        else:
            role_list = []
            for role_id, role_name in crew_roles:
                role = interaction.guild.get_role(role_id)
                if role:
                    role_list.append(f"• {role.mention} (`{role_id}`)")
                else:
                    role_list.append(f"• ~~{role_name}~~ (`{role_id}`) - *Role deleted*")
            
            embed.description = "\n".join(role_list)
        
        embed.set_footer(text=f"Total crew roles: {len(crew_roles)}")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="add_crew_role", description="Add a crew role with captain and first mate")
    @app_commands.describe(
        crew_role="The main crew role",
        captain_role="The captain role for this crew",
        first_mate_role="The first mate role for this crew"
    )
    @is_admin()
    async def add_crew_role(self, interaction: discord.Interaction, crew_role: discord.Role, captain_role: discord.Role, first_mate_role: discord.Role):
        """Add a crew role with captain and first mate hierarchy"""
        guild_id = interaction.guild.id
        
        # Check if role is already a crew role
        existing_crew_roles = await self.bot.database.get_crew_roles(guild_id)
        if crew_role.id in existing_crew_roles:
            embed = discord.Embed(
                title="⚠️ Blimey!",
                description=f"{crew_role.mention} be already registered as a crew role, cap'n!",
                color=ERROR_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Add the crew role with hierarchy
        await self.bot.database.add_crew_role(guild_id, crew_role.id, crew_role.name, captain_role.id, first_mate_role.id)
        
        embed = discord.Embed(
            title="✅ Crew Added to Fleet!",
            description=f"Aye aye! **{crew_role.name}** has been registered with full command structure!",
            color=SUCCESS_COLOR
        )
        embed.add_field(
            name="🏴‍☠️ Crew Hierarchy",
            value=f"**Crew:** {crew_role.mention} ({len(crew_role.members)} members)\n**Captain:** {captain_role.mention}\n**First Mate:** {first_mate_role.mention}",
            inline=False
        )
        embed.set_footer(text="Crew members will now earn bonus doubloons and access to exclusive items!")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="remove_crew_role", description="Remove a role from crew roles")
    @app_commands.describe(role="The role to remove from crew roles")
    @is_admin()
    async def remove_crew_role(self, interaction: discord.Interaction, role: discord.Role):
        """Remove a crew role"""
        guild_id = interaction.guild.id
        
        # Check if role is a crew role
        existing_crew_roles = await self.bot.database.get_crew_roles(guild_id)
        if role.id not in existing_crew_roles:
            embed = discord.Embed(
                title="⚠️ Shiver me timbers!",
                description=f"{role.mention} ain't registered as a crew role, cap'n!",
                color=ERROR_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Remove the crew role
        await self.bot.database.remove_crew_role(guild_id, role.id)
        
        embed = discord.Embed(
            title="✅ Crew Role Removed!",
            description=f"Arrr! {role.mention} has been removed from the crew roster!",
            color=SUCCESS_COLOR
        )
        embed.add_field(
            name="🏴‍☠️ Role Details",
            value=f"**Name:** {role.name}\n**ID:** `{role.id}`",
            inline=False
        )
        embed.set_footer(text="Members with this role will no longer earn bonus doubloons.")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="give_coins", description="Give doubloons to a user")
    @app_commands.describe(
        user="The user to give coins to",
        amount="Amount of coins to give"
    )
    @is_admin()
    async def give_coins(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        """Give coins to a user (admin only)"""
        if amount <= 0:
            embed = discord.Embed(
                title="⚠️ Invalid Amount",
                description="Amount must be positive, ye scallywag!",
                color=ERROR_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if amount > 1000000:  # Reasonable limit
            embed = discord.Embed(
                title="⚠️ Too Much Treasure!",
                description="That be too much treasure for one grant, cap'n! (Max: 1,000,000)",
                color=ERROR_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Give coins
        await self.bot.database.add_coins(user.id, amount)
        new_balance = await self.bot.database.get_user_balance(user.id)
        
        embed = discord.Embed(
            title="💰 Treasure Granted!",
            description=f"Ye granted **{amount:,}** doubloons to {user.mention}!",
            color=SUCCESS_COLOR
        )
        embed.add_field(
            name="💎 Their New Balance",
            value=f"{new_balance:,} doubloons",
            inline=True
        )
        embed.set_footer(text=f"Granted by {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="stats", description="View bot statistics")
    @is_admin()
    async def stats(self, interaction: discord.Interaction):
        """View bot statistics"""
        # Get leaderboard to count active users
        leaderboard = await self.bot.database.get_leaderboard(1000)  # Get up to 1000 users
        
        total_users = len(leaderboard)
        total_coins = sum(user[1] for user in leaderboard)  # Sum all balances
        total_earned = sum(user[2] for user in leaderboard)  # Sum total earned
        
        crew_roles = await self.bot.database.get_crew_roles_with_names(interaction.guild.id)
        
        embed = discord.Embed(
            title="📊 No Man's Bot Statistics",
            color=EMBED_COLOR
        )
        
        embed.add_field(
            name="👥 Active Users",
            value=f"{total_users:,}",
            inline=True
        )
        
        embed.add_field(
            name="💰 Total Coins in Circulation",
            value=f"{total_coins:,}",
            inline=True
        )
        
        embed.add_field(
            name="⚡ Total Coins Ever Earned",
            value=f"{total_earned:,}",
            inline=True
        )
        
        embed.add_field(
            name="🏴‍☠️ Configured Crew Roles",
            value=f"{len(crew_roles)}",
            inline=True
        )
        
        embed.add_field(
            name="🌊 Guilds",
            value=f"{len(self.bot.guilds)}",
            inline=True
        )
        
        embed.set_footer(text="These be the numbers, cap'n!")
        
        await interaction.response.send_message(embed=embed)
    
    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Handle command errors"""
        if isinstance(error, app_commands.CheckFailure):
            embed = discord.Embed(
                title="⚠️ Access Denied",
                description="Ye need administrator permissions to use this command, matey!",
                color=ERROR_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(
                title="❌ Command Error",
                description="Something went wrong, cap'n! Check the logs.",
                color=ERROR_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
