import discord
from discord.ext import commands
from discord import app_commands
import random
import time
from bot.utils.constants import *
from bot.utils.helpers import get_user_crew, format_coins

class EconomyCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="search", description="Search for treasure and items! 🔍")
    async def search(self, interaction: discord.Interaction):
        """Search command for finding coins and items"""
        user_id = interaction.user.id
        
        # Check cooldown
        if not await self.bot.database.can_use_search_command(user_id):
            embed = discord.Embed(
                title="🕒 Still Searchin'!",
                description="Ye already searched this area, matey! Wait a bit before searchin' again.",
                color=ERROR_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Get user's active effects
        active_compass, active_spyglass, compass_dur, spyglass_dur, active_weapon = await self.bot.database.get_user_effects(user_id)
        
        # Determine if user is in a crew
        crew_roles = await self.bot.database.get_crew_roles(interaction.guild.id)
        user_crew = get_user_crew(interaction.user, crew_roles)
        is_crew_member = user_crew is not None
        
        # Base search results
        base_coin_chance = 60  # 60% chance to find coins
        base_item_chance = 20  # 20% chance to find items
        coin_multiplier = 1.0
        
        # Apply consumable effects
        if active_compass:
            base_coin_chance += 15  # +15% coin finding chance
            await self.bot.database.reduce_consumable_durability(user_id, "Compass")
        
        if active_spyglass:
            base_coin_chance += 20  # +20% coin finding chance
            await self.bot.database.reduce_consumable_durability(user_id, "Spyglass")
        
        # Check inventory for other consumables
        inventory = await self.bot.database.get_user_inventory(user_id)
        inventory_dict = dict(inventory)
        
        # Ship Maintenance effect (crew only)
        if is_crew_member and "Ship Maintenance" in inventory_dict:
            base_coin_chance += 30  # Greatly increases chances
            coin_multiplier += 0.5
            await self.bot.database.remove_from_inventory(user_id, "Ship Maintenance", 1)
        
        # Treasure Map effect (crew only)
        if is_crew_member and "Treasure Map" in inventory_dict:
            base_coin_chance += 25  # Increases odds
            coin_multiplier += 1.0  # Doubles money found
            await self.bot.database.remove_from_inventory(user_id, "Treasure Map", 1)
        
        # Roll for findings
        coin_roll = random.randint(1, 100)
        item_roll = random.randint(1, 100)
        
        found_coins = 0
        found_item = None
        
        # Check for coins
        if coin_roll <= base_coin_chance:
            base_coins = random.randint(15, 45)
            found_coins = int(base_coins * coin_multiplier)
            if is_crew_member:
                found_coins = int(found_coins * CREW_BONUS_MULTIPLIER)
            
            await self.bot.database.add_coins(user_id, found_coins)
        
        # Check for items
        if item_roll <= base_item_chance:
            # Available items based on crew membership
            if is_crew_member:
                available_items = [
                    "Compass", "Spyglass", "Rum", "Pirate Hook", "Cutlass", "Flintlock Pistol",
                    "Ship Maintenance", "Treasure Map", "Barrel", "Flintlock Musket", "Cannon", "Grenade"
                ]
                # Higher chance for crew items
                weights = [10, 10, 15, 8, 6, 4, 5, 3, 7, 4, 2, 1]
            else:
                available_items = ["Compass", "Spyglass", "Rum", "Pirate Hook", "Cutlass", "Flintlock Pistol"]
                weights = [15, 15, 20, 12, 8, 5]
            
            found_item = random.choices(available_items, weights=weights)[0]
            await self.bot.database.add_to_inventory(user_id, found_item, 1)
        
        # Update cooldown
        await self.bot.database.update_search_command_cooldown(user_id)
        
        # Create response
        search_locations = [
            "explored a mysterious cave",
            "searched through old shipwrecks",
            "dug around a palm tree",
            "investigated a hidden cove",
            "rummaged through abandoned barrels",
            "followed a treasure map fragment",
            "searched the coral reefs",
            "explored a sea cave",
            "investigated ruins on a beach"
        ]
        
        location = random.choice(search_locations)
        
        embed = discord.Embed(
            title="🔍 Search Complete!",
            description=f"Ye {location}...",
            color=SUCCESS_COLOR
        )
        
        results = []
        if found_coins > 0:
            results.append(f"💰 Found **{format_coins(found_coins)}**!")
            
        if found_item:
            results.append(f"📦 Found a **{found_item}**!")
            
        if not results:
            results.append("🏝️ Found nothin' but sand and seaweed...")
            embed.color = WARNING_COLOR
        
        embed.add_field(
            name="🎯 Search Results",
            value="\n".join(results),
            inline=False
        )
        
        # Show active effects
        effects = []
        if active_compass and compass_dur > 0:
            effects.append(f"🧭 Compass ({compass_dur-1} uses left)")
        if active_spyglass and spyglass_dur > 0:
            effects.append(f"🔭 Spyglass ({spyglass_dur-1} uses left)")
            
        if effects:
            embed.add_field(
                name="⚡ Active Effects",
                value="\n".join(effects),
                inline=True
            )
        
        if is_crew_member:
            embed.add_field(
                name="🏴‍☠️ Crew Bonus",
                value=f"**{user_crew}** (+50% coins)",
                inline=True
            )
        
        embed.set_footer(text="Next search available in 5 minutes")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="balance", description="Check yer doubloon stash! 💰")
    async def balance(self, interaction: discord.Interaction, user: discord.Member = None):
        """Check balance command"""
        target_user = user or interaction.user
        user_id = target_user.id
        
        balance, total_earned = await self.bot.database.get_user_stats(user_id)
        
        # Determine crew
        crew_roles = await self.bot.database.get_crew_roles(interaction.guild.id)
        user_crew = get_user_crew(target_user, crew_roles)
        
        embed = discord.Embed(
            title=f"💰 {target_user.display_name}'s Treasure Chest",
            color=EMBED_COLOR
        )
        
        embed.add_field(
            name="💎 Current Doubloons",
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
        embed.set_footer(text="Keep earnin' those doubloons, matey!")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="daily", description="Claim yer daily ration of doubloons! 🗓️")
    async def daily(self, interaction: discord.Interaction):
        """Daily reward command"""
        user_id = interaction.user.id
        
        # For now, we'll use the earn command cooldown mechanism
        # In a full implementation, you'd want a separate daily cooldown table
        
        # Determine if user is in a crew
        crew_roles = await self.bot.database.get_crew_roles(interaction.guild.id)
        user_crew = get_user_crew(interaction.user, crew_roles)
        is_crew_member = user_crew is not None
        
        # Daily reward amount
        base_daily = DAILY_REWARD
        if is_crew_member:
            daily_coins = int(base_daily * CREW_BONUS_MULTIPLIER)
            bonus_text = f" (Crew bonus: +{int((CREW_BONUS_MULTIPLIER - 1) * 100)}%)"
        else:
            daily_coins = base_daily
            bonus_text = ""
        
        # Add coins
        await self.bot.database.add_coins(user_id, daily_coins)
        new_balance = await self.bot.database.get_user_balance(user_id)
        
        embed = discord.Embed(
            title="🗓️ Daily Ration Claimed!",
            description=f"Ye claimed yer daily ration of **{format_coins(daily_coins)}**{bonus_text}!",
            color=SUCCESS_COLOR
        )
        
        if is_crew_member:
            embed.add_field(
                name="🏴‍☠️ Crew",
                value=f"**{user_crew}**",
                inline=True
            )
        
        embed.add_field(
            name="💰 New Balance",
            value=format_coins(new_balance),
            inline=True
        )
        
        embed.set_footer(text="Come back tomorrow for another ration!")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="steal", description="Attempt to steal doubloons from another pirate! 🏴‍☠️")
    @app_commands.describe(target="The pirate ye want to steal from")
    async def steal(self, interaction: discord.Interaction, target: discord.Member):
        """Steal command for attempting to steal coins from other players"""
        thief_id = interaction.user.id
        victim_id = target.id
        
        # Can't steal from yourself
        if thief_id == victim_id:
            embed = discord.Embed(
                title="🤔 Confused Pirate",
                description="Ye can't steal from yerself, ye scallywag! That's just movin' coins from one pocket to another!",
                color=ERROR_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Can't steal from bots
        if target.bot:
            embed = discord.Embed(
                title="🤖 Invalid Target",
                description="Ye can't steal from a bot, matey! They don't carry doubloons!",
                color=ERROR_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Check cooldown
        if not await self.bot.database.can_use_steal_command(thief_id):
            embed = discord.Embed(
                title="⏰ Too Soon, Matey!",
                description="Ye've been causin' too much trouble! Wait a bit before yer next heist.\n\nNext steal available in 10 minutes.",
                color=ERROR_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Get balances
        thief_balance = await self.bot.database.get_user_balance(thief_id)
        victim_balance = await self.bot.database.get_user_balance(victim_id)
        
        # Check if victim has enough coins
        if victim_balance < 10:
            embed = discord.Embed(
                title="💰 Empty Pockets",
                description=f"Arrr! {target.display_name} doesn't have enough doubloons worth stealin'! (Need at least 10)",
                color=ERROR_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Get crew bonuses for success chance
        crew_roles = await self.bot.database.get_crew_roles(interaction.guild.id)
        thief_crew = get_user_crew(interaction.user, crew_roles)
        victim_crew = get_user_crew(target, crew_roles)
        
        # Base success chance: 40%
        success_chance = 40
        
        # Crew bonuses
        if thief_crew:
            success_chance += 10  # +10% if thief is in crew
        if victim_crew:
            success_chance -= 10  # -10% if victim is in crew (they're protected)
        
        # Weapon bonuses
        active_compass, active_spyglass, compass_dur, spyglass_dur, active_weapon = await self.bot.database.get_user_effects(thief_id)
        weapon_bonus = 0
        
        if active_weapon:
            weapon_bonuses = {
                "Pirate Hook": 5,
                "Cutlass": 10,
                "Flintlock Pistol": 15,
                "Flintlock Musket": 20,
                "Cannon": 25,
                "Grenade": 30
            }
            weapon_bonus = weapon_bonuses.get(active_weapon, 0)
            success_chance += weapon_bonus
        
        # Ensure success chance stays within reasonable bounds
        success_chance = max(20, min(60, success_chance))
        
        # Roll for success
        roll = random.randint(1, 100)
        steal_successful = roll <= success_chance
        
        # Update cooldown regardless of success
        await self.bot.database.update_steal_cooldown(thief_id)
        
        if steal_successful:
            # Calculate stolen amount (5-25% of victim's balance, minimum 10, maximum 500)
            steal_percentage = random.uniform(0.05, 0.25)
            stolen_amount = int(victim_balance * steal_percentage)
            stolen_amount = max(10, min(500, stolen_amount))
            
            # Make sure victim has enough after minimum check above
            stolen_amount = min(stolen_amount, victim_balance)
            
            # Transfer the coins
            await self.bot.database.transfer_coins(victim_id, thief_id, stolen_amount)
            
            # Get updated balances
            new_thief_balance = await self.bot.database.get_user_balance(thief_id)
            new_victim_balance = await self.bot.database.get_user_balance(victim_id)
            
            success_messages = [
                "snuck into their cabin and nabbed",
                "pickpocketed them while they were distracted and got",
                "raided their treasure chest and made off with",
                "ambushed them on the docks and stole",
                "distracted them with rum and pilfered",
                "challenged them to cards and cheated to win"
            ]
            
            action = random.choice(success_messages)
            
            embed = discord.Embed(
                title="🏴‍☠️ Successful Heist!",
                description=f"Arrr! Ye {action} **{format_coins(stolen_amount)}** from {target.display_name}!",
                color=SUCCESS_COLOR
            )
            
            embed.add_field(
                name="🎯 Success Rate",
                value=f"{success_chance}%",
                inline=True
            )
            
            embed.add_field(
                name="💰 Yer New Balance",
                value=format_coins(new_thief_balance),
                inline=True
            )
            
            if thief_crew:
                embed.add_field(
                    name="🏴‍☠️ Crew Bonus",
                    value=f"**{thief_crew}** (+10% success)",
                    inline=True
                )
            
            embed.set_footer(text="Crime doesn't pay... or does it? Next steal in 10 minutes")
            
        else:
            # Failed steal attempt
            # Small penalty for failed attempt (5-15 coins lost to guards/authorities)
            penalty = random.randint(5, min(15, thief_balance))
            if penalty > 0 and thief_balance >= penalty:
                await self.bot.database.transfer_coins(thief_id, victim_id, penalty)
                penalty_text = f"\n\nYe lost **{format_coins(penalty)}** in the struggle!"
            else:
                penalty_text = ""
            
            fail_messages = [
                "were caught red-handed by the town guard",
                "tripped over a rope and alerted everyone",
                "were spotted by a lookout",
                "accidentally rang the ship's bell while sneaking",
                "were outsmarted by yer target",
                "got lost in the fog and missed yer chance"
            ]
            
            fail_reason = random.choice(fail_messages)
            
            embed = discord.Embed(
                title="⚠️ Heist Failed!",
                description=f"Blimey! Ye {fail_reason}! {target.display_name} kept their treasure safe.{penalty_text}",
                color=ERROR_COLOR
            )
            
            embed.add_field(
                name="🎯 Success Rate",
                value=f"{success_chance}%",
                inline=True
            )
            
            embed.add_field(
                name="🎲 Roll Result",
                value=f"{roll}/100 (needed ≤{success_chance})",
                inline=True
            )
            
            if victim_crew:
                embed.add_field(
                    name="🛡️ Target Protected",
                    value=f"**{victim_crew}** (-10% your success)",
                    inline=True
                )
            
            embed.set_footer(text="Better luck next time, matey! Next steal in 10 minutes")
        
        await interaction.response.send_message(embed=embed)
