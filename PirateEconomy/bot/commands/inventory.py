import discord
from discord.ext import commands
from discord import app_commands
from bot.utils.constants import *
from bot.utils.helpers import get_user_crew, format_coins

class InventoryCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="inventory", description="Check yer inventory and active items! 🎒")
    async def inventory(self, interaction: discord.Interaction, user: discord.Member = None):
        """View user's inventory"""
        target_user = user or interaction.user
        user_id = target_user.id
        
        # Get inventory
        inventory = await self.bot.database.get_user_inventory(user_id)
        
        # Get active effects
        active_compass, active_spyglass, compass_dur, spyglass_dur, active_weapon = await self.bot.database.get_user_effects(user_id)
        
        embed = discord.Embed(
            title=f"🎒 {target_user.display_name}'s Inventory",
            color=EMBED_COLOR
        )
        
        if not inventory:
            embed.description = "Empty as a ghost ship's hold! Use `/search` to find items."
        else:
            # Group items by type
            consumables = []
            weapons = []
            
            for item_name, quantity in inventory:
                item_info = await self.bot.database.get_item_info(item_name)
                if item_info:
                    item_type = item_info[0]
                    if item_type == "consumable":
                        consumables.append(f"• {item_name} x{quantity}")
                    elif item_type == "weapon":
                        weapons.append(f"• {item_name} x{quantity}")
            
            if consumables:
                embed.add_field(
                    name="🧪 Consumables",
                    value="\n".join(consumables) or "None",
                    inline=False
                )
            
            if weapons:
                embed.add_field(
                    name="⚔️ Weapons",
                    value="\n".join(weapons) or "None",
                    inline=False
                )
        
        # Show active effects
        active_effects = []
        if active_compass:
            active_effects.append(f"🧭 Compass (Active - {compass_dur} uses left)")
        if active_spyglass:
            active_effects.append(f"🔭 Spyglass (Active - {spyglass_dur} uses left)")
        if active_weapon:
            active_effects.append(f"⚔️ {active_weapon} (Equipped)")
        
        if active_effects:
            embed.add_field(
                name="⚡ Active Effects",
                value="\n".join(active_effects),
                inline=False
            )
        
        embed.set_thumbnail(url=target_user.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="use", description="Use a consumable item! 🧪")
    @app_commands.describe(item="The item to use")
    async def use_item(self, interaction: discord.Interaction, item: str):
        """Use a consumable item"""
        user_id = interaction.user.id
        
        # Get user's inventory
        inventory = await self.bot.database.get_user_inventory(user_id)
        inventory_dict = dict(inventory)
        
        if item not in inventory_dict or inventory_dict[item] <= 0:
            embed = discord.Embed(
                title="❌ Item Not Found",
                description=f"Ye don't have any **{item}** in yer inventory, matey!",
                color=ERROR_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Get item info
        item_info = await self.bot.database.get_item_info(item)
        if not item_info:
            embed = discord.Embed(
                title="❌ Unknown Item",
                description=f"That item doesn't exist in our records, ye scurvy dog!",
                color=ERROR_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        item_type, price, crew_required, description = item_info
        
        if item_type != "consumable":
            embed = discord.Embed(
                title="❌ Can't Use That",
                description=f"**{item}** is not a consumable item! Use `/equip` for weapons.",
                color=ERROR_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Handle different consumables
        if item in ["Compass", "Spyglass"]:
            # Check if already active
            active_compass, active_spyglass, compass_dur, spyglass_dur, active_weapon = await self.bot.database.get_user_effects(user_id)
            
            if item == "Compass" and active_compass:
                embed = discord.Embed(
                    title="⚠️ Already Active",
                    description="Ye already have a compass active! Wait for it to break before usin' another.",
                    color=WARNING_COLOR
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            if item == "Spyglass" and active_spyglass:
                embed = discord.Embed(
                    title="⚠️ Already Active",
                    description="Ye already have a spyglass active! Wait for it to break before usin' another.",
                    color=WARNING_COLOR
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Activate the item
            await self.bot.database.set_active_consumable(user_id, item, 10)
            await self.bot.database.remove_from_inventory(user_id, item, 1)
            
            embed = discord.Embed(
                title="✅ Item Activated!",
                description=f"Ye activated yer **{item}**! It will help ye find more treasure for 10 searches.",
                color=SUCCESS_COLOR
            )
            
        elif item == "Rum":
            # Reduce search cooldown by 2 minutes
            current_time = int(__import__('time').time())
            reduced_time = current_time - 120  # 2 minutes ago
            
            await self.bot.database._execute_query(
                "UPDATE users SET last_search_command = ? WHERE user_id = ?",
                (reduced_time, user_id)
            )
            await self.bot.database.remove_from_inventory(user_id, item, 1)
            
            embed = discord.Embed(
                title="🍺 Rum Consumed!",
                description="Arrr! That hit the spot! Yer search cooldown has been reduced by 2 minutes.",
                color=SUCCESS_COLOR
            )
            
        else:
            # Other consumables are used automatically during search
            embed = discord.Embed(
                title="ℹ️ Auto-Use Item",
                description=f"**{item}** is automatically used during searches when ye have it in yer inventory!",
                color=EMBED_COLOR
            )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="equip", description="Equip a weapon! ⚔️")
    @app_commands.describe(weapon="The weapon to equip")
    async def equip_weapon(self, interaction: discord.Interaction, weapon: str):
        """Equip a weapon"""
        user_id = interaction.user.id
        
        # Get user's inventory
        inventory = await self.bot.database.get_user_inventory(user_id)
        inventory_dict = dict(inventory)
        
        if weapon not in inventory_dict or inventory_dict[weapon] <= 0:
            embed = discord.Embed(
                title="❌ Weapon Not Found",
                description=f"Ye don't have a **{weapon}** in yer inventory, matey!",
                color=ERROR_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Get item info
        item_info = await self.bot.database.get_item_info(weapon)
        if not item_info:
            embed = discord.Embed(
                title="❌ Unknown Weapon",
                description=f"That weapon doesn't exist in our records!",
                color=ERROR_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        item_type, price, crew_required, description = item_info
        
        if item_type != "weapon":
            embed = discord.Embed(
                title="❌ Not a Weapon",
                description=f"**{weapon}** is not a weapon! Use `/use` for consumables.",
                color=ERROR_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Equip the weapon
        await self.bot.database.set_active_weapon(user_id, weapon)
        
        # Calculate weapon bonus
        weapon_bonuses = {
            "Pirate Hook": 5,
            "Cutlass": 10,
            "Flintlock Pistol": 15,
            "Flintlock Musket": 20,
            "Cannon": 25,
            "Grenade": 30
        }
        
        bonus = weapon_bonuses.get(weapon, 0)
        
        embed = discord.Embed(
            title="⚔️ Weapon Equipped!",
            description=f"Ye equipped yer **{weapon}**! It gives ye +{bonus}% success rate when stealin'.",
            color=SUCCESS_COLOR
        )
        
        embed.add_field(
            name="💡 Tip",
            value="This weapon will be used automatically in steal attempts!",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="crew_inventory", description="View yer crew's inventory! 🏴‍☠️")
    async def crew_inventory(self, interaction: discord.Interaction):
        """View crew inventory"""
        user_id = interaction.user.id
        
        # Check if user is in a crew
        crew_roles = await self.bot.database.get_crew_roles(interaction.guild.id)
        user_crew = get_user_crew(interaction.user, crew_roles)
        
        if not user_crew:
            embed = discord.Embed(
                title="❌ No Crew",
                description="Ye need to be in a crew to view crew inventory, ye lone wolf!",
                color=ERROR_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Get crew inventory (simplified version)
        crew_inventory = await self.bot.database.get_crew_inventory(interaction.guild.id, 0)
        
        embed = discord.Embed(
            title=f"🏴‍☠️ {user_crew} Crew Inventory",
            description="Items owned by all crew members:",
            color=EMBED_COLOR
        )
        
        if not crew_inventory:
            embed.description = "Yer crew's as poor as church mice! Time to get searchin'!"
        else:
            # Group by member
            member_items = {}
            for user_id_item, username, item_name, quantity in crew_inventory:
                if username not in member_items:
                    member_items[username] = []
                member_items[username].append(f"• {item_name} x{quantity}")
            
            for member, items in member_items.items():
                embed.add_field(
                    name=f"👤 {member}",
                    value="\n".join(items[:5]) + ("..." if len(items) > 5 else ""),
                    inline=True
                )
        
        embed.set_footer(text=f"Crew: {user_crew}")
        
        await interaction.response.send_message(embed=embed)