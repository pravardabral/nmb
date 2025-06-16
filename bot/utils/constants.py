"""
Constants for No Man's Bot
"""

# Embed Colors
EMBED_COLOR = 0x8B4513  # Saddle Brown (pirate theme)
SUCCESS_COLOR = 0x00FF00  # Green
ERROR_COLOR = 0xFF0000  # Red
WARNING_COLOR = 0xFFFF00  # Yellow

# Economy Settings
BASE_PASSIVE_COINS = 1  # Base coins earned per message
MIN_EARN_COINS = 10  # Minimum coins from /earn command
MAX_EARN_COINS = 50  # Maximum coins from /earn command
CREW_BONUS_MULTIPLIER = 1.5  # 50% bonus for crew members
DAILY_REWARD = 100  # Daily reward amount

# Rate Limiting (in seconds)
PASSIVE_COOLDOWN = 60  # 1 minute between passive earnings
EARN_COMMAND_COOLDOWN = 300  # 5 minutes between /earn commands
STEAL_COMMAND_COOLDOWN = 600  # 10 minutes between /steal commands
DAILY_COOLDOWN = 86400  # 24 hours between daily rewards

# Steal Command Settings
BASE_STEAL_SUCCESS_CHANCE = 40  # Base 40% success rate
CREW_STEAL_BONUS = 10  # +10% success if thief has crew role
CREW_PROTECTION_BONUS = 10  # -10% success if victim has crew role
MIN_STEAL_AMOUNT = 10  # Minimum coins needed to be stolen from
MAX_STEAL_AMOUNT = 500  # Maximum coins that can be stolen in one attempt
STEAL_PENALTY_MIN = 5  # Minimum penalty for failed steal
STEAL_PENALTY_MAX = 15  # Maximum penalty for failed steal

# Bot Settings
BOT_PREFIX = "!"
