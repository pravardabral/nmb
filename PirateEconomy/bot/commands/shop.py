import discord
from discord.ext import commands
from discord import app_commands
from bot.utils.constants import *
from bot.utils.helpers import get_user_crew, format_coins


class ShopCommands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="shop", description="Browse the pirate shop! 🛒")
    async def shop(self, interaction: discord.Interaction):
        """Display the shop"""
        # Check if user is in a crew
        crew_roles = await self.bot.database.get_crew_roles(
            interaction.guild.id)
        user_crew = get_user_crew(interaction.user, crew_roles)
        is_crew_member = user_crew is not None

        # Get shop items
        regular_items = await self.bot.database.get_shop_items(
            0)  # Non-crew items
        crew_items = await self.bot.database.get_shop_items(
            1) if is_crew_member else []  # Crew items

        embed = discord.Embed(
            title="⚓ The Pirate's Bazaar",
            description="Welcome to the finest shop on the seven seas!",
            color=EMBED_COLOR)

        # Regular items (available to everyone)
        if regular_items:
            consumables = []
            weapons = []

            for item_name, item_type, price, description in regular_items:
                item_line = f"**{item_name}** - {format_coins(price)}\n└ *{description}*"

                if item_type == "consumable":
                    consumables.append(item_line)
                elif item_type == "weapon":
                    weapons.append(item_line)

            if consumables:
                embed.add_field(name="🧪 Consumables",
                                value="\n\n".join(consumables),
                                inline=False)

            if weapons:
                embed.add_field(name="⚔️ Weapons",
                                value="\n\n".join(weapons),
                                inline=False)

        # Crew-exclusive items
        if crew_items and is_crew_member:
            crew_consumables = []
            crew_weapons = []

            for item_name, item_type, price, description in crew_items:
                item_line = f"**{item_name}** - {format_coins(price)}\n└ *{description}*"

                if item_type == "consumable":
                    crew_consumables.append(item_line)
                elif item_type == "weapon":
                    crew_weapons.append(item_line)

            if crew_consumables:
                embed.add_field(name="🏴‍☠️ Crew Consumables",
                                value="\n\n".join(crew_consumables),
                                inline=False)

            if crew_weapons:
                embed.add_field(name="🏴‍☠️ Crew Weapons",
                                value="\n\n".join(crew_weapons),
                                inline=False)

        elif not is_crew_member and crew_items:
            embed.add_field(name="🔒 Crew Exclusive Items",
                            value="Join a crew to access premium items!",
                            inline=False)

        embed.add_field(name="💡 How to Buy",
                        value="Use `/buy <item_name>` to purchase items!",
                        inline=False)

        if is_crew_member:
            embed.set_footer(text=f"Crew Member: {user_crew}")
        else:
            embed.set_footer(text="Join a crew for exclusive items!")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="buy",
                          description="Buy an item from the shop! 💰")
    @app_commands.describe(item="The item to purchase",
                           quantity="How many to buy (default: 1)")
    async def buy_item(self,
                       interaction: discord.Interaction,
                       item: str,
                       quantity: int = 1):
        """Buy an item from the shop"""
        user_id = interaction.user.id

        if quantity <= 0:
            embed = discord.Embed(
                title="❌ Invalid Quantity",
                description=
                "Ye can't buy nothin' or negative items, ye scallywag!",
                color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed,
                                                    ephemeral=True)
            return

        if quantity > 50:
            embed = discord.Embed(
                title="❌ Too Many Items",
                description=
                "Ye can't buy more than 50 of an item at once, matey!",
                color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed,
                                                    ephemeral=True)
            return

        # Get item info
        item_info = await self.bot.database.get_item_info(item)
        if not item_info:
            embed = discord.Embed(
                title="❌ Item Not Found",
                description=
                f"**{item}** doesn't exist in our shop! Check `/shop` for available items.",
                color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed,
                                                    ephemeral=True)
            return

        item_type, price, crew_required, description = item_info
        total_cost = price * quantity

        # Check crew requirement
        if crew_required:
            crew_roles = await self.bot.database.get_crew_roles(
                interaction.guild.id)
            user_crew = get_user_crew(interaction.user, crew_roles)

            if not user_crew:
                embed = discord.Embed(
                    title="🔒 Crew Required",
                    description=
                    f"**{item}** is only available to crew members! Join a crew first.",
                    color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed,
                                                        ephemeral=True)
                return

        # Check user's balance
        user_balance = await self.bot.database.get_user_balance(user_id)
        if user_balance < total_cost:
            embed = discord.Embed(
                title="💸 Insufficient Funds",
                description=
                f"Ye need {format_coins(total_cost)} but only have {format_coins(user_balance)}!",
                color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed,
                                                    ephemeral=True)
            return

        # Process purchase
        await self.bot.database.add_coins(user_id, -total_cost)  # Remove coins
        await self.bot.database.add_to_inventory(user_id, item,
                                                 quantity)  # Add items

        new_balance = await self.bot.database.get_user_balance(user_id)

        embed = discord.Embed(
            title="✅ Purchase Successful!",
            description=
            f"Ye bought **{quantity}x {item}** for {format_coins(total_cost)}!",
            color=SUCCESS_COLOR)

        embed.add_field(name="📦 Item Info",
                        value=f"*{description}*",
                        inline=False)

        embed.add_field(name="💰 Remaining Balance",
                        value=format_coins(new_balance),
                        inline=True)

        if item_type == "weapon":
            embed.add_field(name="💡 Tip",
                            value="Use `/equip` to equip this weapon!",
                            inline=True)
        elif item_type == "consumable" and item in ["Compass", "Spyglass"]:
            embed.add_field(name="💡 Tip",
                            value="Use `/use` to activate this item!",
                            inline=True)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="sell", description="Sell items for half their shop price! 💸")
    @app_commands.describe(item="The item to sell",
                           quantity="How many to sell (default: 1)")
    async def sell_item(self,
                        interaction: discord.Interaction,
                        item: str,
                        quantity: int = 1):
        """Sell an item for half shop price"""
        user_id = interaction.user.id

        if quantity <= 0:
            embed = discord.Embed(
                title="❌ Invalid Quantity",
                description="Ye can't sell nothin' or negative items!",
                color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed,
                                                    ephemeral=True)
            return

        # Check if user has the item
        inventory = await self.bot.database.get_user_inventory(user_id)
        inventory_dict = dict(inventory)

        if item not in inventory_dict or inventory_dict[item] < quantity:
            available = inventory_dict.get(item, 0)
            embed = discord.Embed(
                title="❌ Not Enough Items",
                description=
                f"Ye only have {available}x **{item}** but want to sell {quantity}!",
                color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed,
                                                    ephemeral=True)
            return

        # Get item info for pricing
        item_info = await self.bot.database.get_item_info(item)
        if not item_info:
            embed = discord.Embed(
                title="❌ Unknown Item",
                description=f"**{item}** is not a valid shop item!",
                color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed,
                                                    ephemeral=True)
            return

        item_type, shop_price, crew_required, description = item_info
        sell_price = shop_price // 2  # Half of shop price
        total_earned = sell_price * quantity

        # Process sale
        await self.bot.database.remove_from_inventory(user_id, item, quantity)
        await self.bot.database.add_coins(user_id, total_earned)

        new_balance = await self.bot.database.get_user_balance(user_id)

        embed = discord.Embed(
            title="💸 Item Sold!",
            description=
            f"Ye sold **{quantity}x {item}** for {format_coins(total_earned)}!",
            color=SUCCESS_COLOR)

        embed.add_field(name="💰 New Balance",
                        value=format_coins(new_balance),
                        inline=True)

        embed.add_field(
            name="📊 Sell Price",
            value=f"{format_coins(sell_price)} each\n(50% of shop price)",
            inline=True)

        await interaction.response.send_message(embed=embed)
