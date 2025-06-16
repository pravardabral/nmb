import sqlite3
import asyncio
import time
import logging
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str = "nomansbot.db"):
        self.db_path = db_path
        self._lock = asyncio.Lock()
    
    async def initialize(self):
        """Initialize the database and create tables"""
        async with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    balance INTEGER DEFAULT 0,
                    last_passive_earn INTEGER DEFAULT 0,
                    last_search_command INTEGER DEFAULT 0,
                    last_steal_attempt INTEGER DEFAULT 0,
                    total_earned INTEGER DEFAULT 0,
                    active_compass INTEGER DEFAULT 0,
                    active_spyglass INTEGER DEFAULT 0,
                    compass_durability INTEGER DEFAULT 0,
                    spyglass_durability INTEGER DEFAULT 0,
                    active_weapon TEXT DEFAULT NULL
                )
            """)
            
            # Create crew_roles table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS crew_roles (
                    guild_id INTEGER,
                    role_id INTEGER,
                    role_name TEXT,
                    captain_role_id INTEGER,
                    first_mate_role_id INTEGER,
                    PRIMARY KEY (guild_id, role_id)
                )
            """)
            
            # Create inventory table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inventory (
                    user_id INTEGER,
                    item_name TEXT,
                    quantity INTEGER DEFAULT 0,
                    PRIMARY KEY (user_id, item_name)
                )
            """)
            
            # Create shop table for item definitions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS shop_items (
                    item_name TEXT PRIMARY KEY,
                    item_type TEXT,
                    price INTEGER,
                    crew_required INTEGER DEFAULT 0,
                    description TEXT
                )
            """)
            
            # Initialize shop items
            shop_items = [
                # Non-crew consumables
                ("Compass", "consumable", 100, 0, "Increases odds of finding money, breaks over time"),
                ("Spyglass", "consumable", 150, 0, "Increases odds of finding money, breaks over time"), 
                ("Rum", "consumable", 50, 0, "Decreases cooldown for search command"),
                # Non-crew weapons
                ("Pirate Hook", "weapon", 200, 0, "Basic weapon for stealing"),
                ("Cutlass", "weapon", 350, 0, "Improved weapon for stealing"),
                ("Flintlock Pistol", "weapon", 500, 0, "Advanced weapon for stealing"),
                # Crew consumables
                ("Ship Maintenance", "consumable", 800, 1, "Greatly increases chances of finding money"),
                ("Treasure Map", "consumable", 1200, 1, "Increases odds and amount of money found"),
                ("Barrel", "consumable", 400, 1, "Increases money inventory capacity"),
                # Crew weapons
                ("Flintlock Musket", "weapon", 1000, 1, "Crew weapon for stealing"),
                ("Cannon", "weapon", 1800, 1, "Powerful crew weapon for stealing"),
                ("Grenade", "weapon", 2500, 1, "Elite crew weapon for stealing")
            ]
            
            cursor.executemany(
                "INSERT OR IGNORE INTO shop_items VALUES (?, ?, ?, ?, ?)",
                shop_items
            )
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
    
    async def _execute_query(self, query: str, params: tuple = (), fetch: bool = False):
        """Execute a database query safely"""
        async with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                cursor.execute(query, params)
                
                if fetch:
                    result = cursor.fetchall()
                    conn.close()
                    return result
                else:
                    conn.commit()
                    conn.close()
                    return cursor.rowcount
            except Exception as e:
                conn.close()
                logger.error(f"Database error: {e}")
                raise
    
    async def get_user_balance(self, user_id: int) -> int:
        """Get user's coin balance"""
        result = await self._execute_query(
            "SELECT balance FROM users WHERE user_id = ?",
            (user_id,),
            fetch=True
        )
        return result[0][0] if result else 0
    
    async def add_coins(self, user_id: int, amount: int):
        """Add coins to user's balance"""
        # First, ensure user exists
        await self._execute_query(
            """INSERT OR IGNORE INTO users (user_id, balance, total_earned) 
               VALUES (?, 0, 0)""",
            (user_id,)
        )
        
        # Then update balance and total earned
        await self._execute_query(
            """UPDATE users 
               SET balance = balance + ?, total_earned = total_earned + ?
               WHERE user_id = ?""",
            (amount, amount, user_id)
        )
    
    async def can_earn_passive(self, user_id: int) -> bool:
        """Check if user can earn passive coins (rate limiting)"""
        result = await self._execute_query(
            "SELECT last_passive_earn FROM users WHERE user_id = ?",
            (user_id,),
            fetch=True
        )
        
        if not result:
            return True
        
        last_earn = result[0][0]
        current_time = int(time.time())
        
        # 60 seconds cooldown for passive earning
        return current_time - last_earn >= 60
    
    async def update_passive_cooldown(self, user_id: int):
        """Update the passive earning cooldown"""
        current_time = int(time.time())
        await self._execute_query(
            """INSERT OR REPLACE INTO users (user_id, last_passive_earn, balance, total_earned)
               VALUES (?, ?, COALESCE((SELECT balance FROM users WHERE user_id = ?), 0),
                       COALESCE((SELECT total_earned FROM users WHERE user_id = ?), 0))""",
            (user_id, current_time, user_id, user_id)
        )
    
    async def can_use_search_command(self, user_id: int) -> bool:
        """Check if user can use the search command (rate limiting)"""
        result = await self._execute_query(
            "SELECT last_search_command FROM users WHERE user_id = ?",
            (user_id,),
            fetch=True
        )
        
        if not result:
            return True
        
        last_search = result[0][0]
        current_time = int(time.time())
        
        # 5 minutes cooldown for search command (reduced by rum)
        return current_time - last_search >= 300
    
    async def update_search_command_cooldown(self, user_id: int):
        """Update the search command cooldown"""
        current_time = int(time.time())
        await self._execute_query(
            """INSERT OR REPLACE INTO users (user_id, last_search_command, balance, total_earned)
               VALUES (?, ?, COALESCE((SELECT balance FROM users WHERE user_id = ?), 0),
                       COALESCE((SELECT total_earned FROM users WHERE user_id = ?), 0))""",
            (user_id, current_time, user_id, user_id)
        )
    
    async def add_to_inventory(self, user_id: int, item_name: str, quantity: int = 1):
        """Add items to user's inventory"""
        await self._execute_query(
            """INSERT INTO inventory (user_id, item_name, quantity)
               VALUES (?, ?, ?)
               ON CONFLICT(user_id, item_name) 
               DO UPDATE SET quantity = quantity + ?""",
            (user_id, item_name, quantity, quantity)
        )
    
    async def remove_from_inventory(self, user_id: int, item_name: str, quantity: int = 1):
        """Remove items from user's inventory"""
        await self._execute_query(
            """UPDATE inventory 
               SET quantity = quantity - ?
               WHERE user_id = ? AND item_name = ?""",
            (quantity, user_id, item_name)
        )
        
        # Remove item if quantity reaches 0
        await self._execute_query(
            "DELETE FROM inventory WHERE user_id = ? AND item_name = ? AND quantity <= 0",
            (user_id, item_name)
        )
    
    async def get_user_inventory(self, user_id: int) -> List[Tuple[str, int]]:
        """Get user's inventory"""
        result = await self._execute_query(
            "SELECT item_name, quantity FROM inventory WHERE user_id = ? AND quantity > 0",
            (user_id,),
            fetch=True
        )
        return result
    
    async def get_crew_inventory(self, guild_id: int, crew_role_id: int) -> List[Tuple[int, str, str, int]]:
        """Get inventory for all members of a crew"""
        # Get all users with the crew role
        crew_members = await self._execute_query(
            """SELECT DISTINCT u.user_id 
               FROM users u 
               WHERE u.user_id IN (
                   SELECT user_id FROM inventory WHERE quantity > 0
               )""",
            fetch=True
        )
        
        # This is a simplified version - in practice, you'd need to track guild members
        # For now, return inventory for users who have items
        result = await self._execute_query(
            """SELECT i.user_id, 'Unknown', i.item_name, i.quantity 
               FROM inventory i 
               WHERE i.quantity > 0
               ORDER BY i.user_id, i.item_name""",
            fetch=True
        )
        return result
    
    async def get_shop_items(self, crew_required: int = None) -> List[Tuple[str, str, int, str]]:
        """Get shop items, optionally filtered by crew requirement"""
        if crew_required is not None:
            result = await self._execute_query(
                "SELECT item_name, item_type, price, description FROM shop_items WHERE crew_required = ?",
                (crew_required,),
                fetch=True
            )
        else:
            result = await self._execute_query(
                "SELECT item_name, item_type, price, description FROM shop_items",
                fetch=True
            )
        return result
    
    async def get_item_info(self, item_name: str) -> Tuple[str, int, int, str]:
        """Get information about a specific item"""
        result = await self._execute_query(
            "SELECT item_type, price, crew_required, description FROM shop_items WHERE item_name = ?",
            (item_name,),
            fetch=True
        )
        return result[0] if result else None
    
    async def set_active_consumable(self, user_id: int, consumable_type: str, durability: int = 10):
        """Set active consumable (compass or spyglass)"""
        if consumable_type == "Compass":
            await self._execute_query(
                """INSERT OR REPLACE INTO users (user_id, active_compass, compass_durability, balance, total_earned)
                   VALUES (?, 1, ?, COALESCE((SELECT balance FROM users WHERE user_id = ?), 0),
                           COALESCE((SELECT total_earned FROM users WHERE user_id = ?), 0))""",
                (user_id, durability, user_id, user_id)
            )
        elif consumable_type == "Spyglass":
            await self._execute_query(
                """INSERT OR REPLACE INTO users (user_id, active_spyglass, spyglass_durability, balance, total_earned)
                   VALUES (?, 1, ?, COALESCE((SELECT balance FROM users WHERE user_id = ?), 0),
                           COALESCE((SELECT total_earned FROM users WHERE user_id = ?), 0))""",
                (user_id, durability, user_id, user_id)
            )
    
    async def set_active_weapon(self, user_id: int, weapon_name: str):
        """Set active weapon"""
        await self._execute_query(
            """INSERT OR REPLACE INTO users (user_id, active_weapon, balance, total_earned)
               VALUES (?, ?, COALESCE((SELECT balance FROM users WHERE user_id = ?), 0),
                       COALESCE((SELECT total_earned FROM users WHERE user_id = ?), 0))""",
            (user_id, weapon_name, user_id, user_id)
        )
    
    async def get_user_effects(self, user_id: int) -> Tuple[int, int, int, int, str]:
        """Get user's active effects (compass, spyglass, durabilities, weapon)"""
        result = await self._execute_query(
            "SELECT active_compass, active_spyglass, compass_durability, spyglass_durability, active_weapon FROM users WHERE user_id = ?",
            (user_id,),
            fetch=True
        )
        if result:
            return result[0]
        return (0, 0, 0, 0, None)
    
    async def reduce_consumable_durability(self, user_id: int, consumable_type: str):
        """Reduce durability of active consumable"""
        if consumable_type == "Compass":
            await self._execute_query(
                "UPDATE users SET compass_durability = compass_durability - 1 WHERE user_id = ?",
                (user_id,)
            )
            # Check if durability reached 0
            result = await self._execute_query(
                "SELECT compass_durability FROM users WHERE user_id = ?",
                (user_id,),
                fetch=True
            )
            if result and result[0][0] <= 0:
                await self._execute_query(
                    "UPDATE users SET active_compass = 0, compass_durability = 0 WHERE user_id = ?",
                    (user_id,)
                )
        elif consumable_type == "Spyglass":
            await self._execute_query(
                "UPDATE users SET spyglass_durability = spyglass_durability - 1 WHERE user_id = ?",
                (user_id,)
            )
            # Check if durability reached 0
            result = await self._execute_query(
                "SELECT spyglass_durability FROM users WHERE user_id = ?",
                (user_id,),
                fetch=True
            )
            if result and result[0][0] <= 0:
                await self._execute_query(
                    "UPDATE users SET active_spyglass = 0, spyglass_durability = 0 WHERE user_id = ?",
                    (user_id,)
                )
    
    async def get_crew_roles(self, guild_id: int) -> List[int]:
        """Get list of crew role IDs for a guild"""
        result = await self._execute_query(
            "SELECT role_id FROM crew_roles WHERE guild_id = ?",
            (guild_id,),
            fetch=True
        )
        return [row[0] for row in result]
    
    async def add_crew_role(self, guild_id: int, role_id: int, role_name: str, captain_role_id: int = None, first_mate_role_id: int = None):
        """Add a crew role with captain and first mate roles"""
        await self._execute_query(
            "INSERT OR REPLACE INTO crew_roles (guild_id, role_id, role_name, captain_role_id, first_mate_role_id) VALUES (?, ?, ?, ?, ?)",
            (guild_id, role_id, role_name, captain_role_id, first_mate_role_id)
        )
    
    async def remove_crew_role(self, guild_id: int, role_id: int):
        """Remove a crew role"""
        await self._execute_query(
            "DELETE FROM crew_roles WHERE guild_id = ? AND role_id = ?",
            (guild_id, role_id)
        )
    
    async def get_crew_roles_with_names(self, guild_id: int) -> List[Tuple[int, str]]:
        """Get crew roles with their names"""
        result = await self._execute_query(
            "SELECT role_id, role_name FROM crew_roles WHERE guild_id = ?",
            (guild_id,),
            fetch=True
        )
        return result
    
    async def get_leaderboard(self, limit: int = 10) -> List[Tuple[int, int, int]]:
        """Get top users by balance"""
        result = await self._execute_query(
            "SELECT user_id, balance, total_earned FROM users ORDER BY balance DESC LIMIT ?",
            (limit,),
            fetch=True
        )
        return result
    
    async def get_user_stats(self, user_id: int) -> Tuple[int, int]:
        """Get user's balance and total earned"""
        result = await self._execute_query(
            "SELECT balance, total_earned FROM users WHERE user_id = ?",
            (user_id,),
            fetch=True
        )
        return result[0] if result else (0, 0)
    
    async def can_use_steal_command(self, user_id: int) -> bool:
        """Check if user can use the steal command (rate limiting)"""
        result = await self._execute_query(
            "SELECT last_steal_attempt FROM users WHERE user_id = ?",
            (user_id,),
            fetch=True
        )
        
        if not result:
            return True
        
        last_steal = result[0][0] if result[0][0] else 0
        current_time = int(time.time())
        
        # 10 minutes cooldown for steal command
        return current_time - last_steal >= 600
    
    async def update_steal_cooldown(self, user_id: int):
        """Update the steal command cooldown"""
        current_time = int(time.time())
        await self._execute_query(
            """INSERT OR REPLACE INTO users (user_id, last_steal_attempt, balance, total_earned)
               VALUES (?, ?, COALESCE((SELECT balance FROM users WHERE user_id = ?), 0),
                       COALESCE((SELECT total_earned FROM users WHERE user_id = ?), 0))""",
            (user_id, current_time, user_id, user_id)
        )
    
    async def transfer_coins(self, from_user_id: int, to_user_id: int, amount: int):
        """Transfer coins from one user to another"""
        # Ensure both users exist
        await self._execute_query(
            """INSERT OR IGNORE INTO users (user_id, balance, total_earned) 
               VALUES (?, 0, 0)""",
            (from_user_id,)
        )
        await self._execute_query(
            """INSERT OR IGNORE INTO users (user_id, balance, total_earned) 
               VALUES (?, 0, 0)""",
            (to_user_id,)
        )
        
        # Remove coins from sender
        await self._execute_query(
            """UPDATE users 
               SET balance = balance - ?
               WHERE user_id = ?""",
            (amount, from_user_id)
        )
        
        # Add coins to receiver (but don't count as earned)
        await self._execute_query(
            """UPDATE users 
               SET balance = balance + ?
               WHERE user_id = ?""",
            (amount, to_user_id)
        )
