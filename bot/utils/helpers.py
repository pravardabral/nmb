"""
Helper functions for No Man's Bot
"""

import discord
from typing import List, Optional

def get_user_crew(user: discord.Member, crew_role_ids: List[int]) -> Optional[str]:
    """
    Get the crew name for a user based on their roles
    
    Args:
        user: Discord member
        crew_role_ids: List of crew role IDs
    
    Returns:
        Crew name if user has a crew role, None otherwise
    """
    for role in user.roles:
        if role.id in crew_role_ids:
            return role.name
    return None

def format_coins(amount: int) -> str:
    """
    Format coin amount with commas and doubloon emoji
    
    Args:
        amount: Number of coins
    
    Returns:
        Formatted string with emoji
    """
    return f"🪙 {amount:,} doubloons"

def get_pirate_greeting() -> str:
    """Get a random pirate greeting"""
    greetings = [
        "Ahoy there, matey!",
        "Avast, ye scallywag!",
        "Shiver me timbers!",
        "Batten down the hatches!",
        "Yo ho ho!",
        "Arrr, me hearty!",
        "Land ho!",
        "All hands on deck!"
    ]
    import random
    return random.choice(greetings)

def get_pirate_farewell() -> str:
    """Get a random pirate farewell"""
    farewells = [
        "Fair winds and following seas!",
        "May yer compass always point true!",
        "Until we meet again on the high seas!",
        "Safe travels, ye savvy sailor!",
        "Keep yer powder dry!",
        "Smooth sailing, matey!",
        "May the tides be in yer favor!",
        "Anchors aweigh!"
    ]
    import random
    return random.choice(farewells)

def format_time_remaining(seconds: int) -> str:
    """
    Format time remaining in a human-readable way
    
    Args:
        seconds: Seconds remaining
    
    Returns:
        Formatted time string
    """
    if seconds <= 0:
        return "Ready now!"
    
    minutes = seconds // 60
    seconds = seconds % 60
    
    if minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

def is_valid_coin_amount(amount: int, max_amount: int = 1000000) -> bool:
    """
    Check if a coin amount is valid
    
    Args:
        amount: Amount to check
        max_amount: Maximum allowed amount
    
    Returns:
        True if valid, False otherwise
    """
    return 0 < amount <= max_amount
