# Overview

No Man's Bot is a pirate-themed Discord economy bot built with Python and discord.py. The bot allows Discord users to earn virtual currency ("doubloons"), participate in crew-based activities, and compete on leaderboards. The application features a simple SQLite database for data persistence and uses Discord's slash command system for user interactions.

# System Architecture

## Backend Architecture
- **Framework**: Python 3.11 with discord.py library
- **Database**: SQLite for local data persistence
- **Architecture Pattern**: Cog-based command structure with modular components
- **Async Programming**: Full async/await implementation for Discord API interactions

## Bot Structure
- **Main Bot Class**: `NoMansBot` extends `commands.Bot` with custom initialization
- **Command Organization**: Commands grouped into cogs (Economy, Admin, Leaderboard)
- **Database Layer**: Centralized `Database` class with connection pooling via asyncio locks
- **Utilities**: Helper functions and constants for consistent theming and formatting

# Key Components

## Database Layer (`bot/database.py`)
- **Purpose**: Manages all data persistence operations
- **Technology**: SQLite with async wrapper using asyncio locks
- **Tables**: 
  - `users`: Stores user balances, cooldowns, and earnings
  - `crew_roles`: Maps Discord roles to crew memberships
- **Key Features**: Thread-safe operations, automatic table creation

## Command Modules
- **Economy Commands** (`bot/commands/economy.py`): Core earning mechanics with cooldowns and crew bonuses
- **Admin Commands** (`bot/commands/admin.py`): Server administration for crew role management
- **Leaderboard Commands** (`bot/commands/leaderboard.py`): Displays top users and crew statistics

## Utility Systems
- **Constants** (`bot/utils/constants.py`): Centralized configuration for colors, rates, and cooldowns
- **Helpers** (`bot/utils/helpers.py`): Common formatting and utility functions

# Data Flow

## User Interaction Flow
1. User invokes slash command via Discord
2. Bot validates permissions and cooldowns
3. Database operations execute with proper locking
4. Response formatted with pirate theme and sent back
5. Cooldowns and user data updated

## Economy System Flow
1. Users earn coins through `/earn` command (5-minute cooldown)
2. Passive earning disabled (infrastructure present but not implemented)
3. Crew members receive 50% bonus on earnings
4. All transactions logged for leaderboard compilation

## Admin Configuration Flow
1. Administrators configure crew roles via `/add_crew_role`
2. Role mappings stored in database per guild
3. Crew bonuses automatically applied based on user roles

# External Dependencies

## Core Dependencies
- **discord.py**: Primary Discord API wrapper for bot functionality
- **aiohttp**: HTTP client library (dependency of discord.py)
- **Python 3.11**: Runtime environment with async support

## Infrastructure Dependencies
- **SQLite**: Embedded database (no external database server required)
- **Replit Environment**: Cloud hosting with automatic deployment

# Deployment Strategy

## Replit Deployment
- **Environment**: Python 3.11 with Nix package management
- **Startup**: Automatic pip install of discord.py followed by bot execution
- **Configuration**: Token management through environment variables (assumed)
- **Persistence**: SQLite database files persist across deployments

## Bot Registration
- Discord bot token required for authentication
- Slash commands automatically synced on startup
- Required intents: message_content, guilds, members

# Changelog

Changelog:
- June 15, 2025. Initial setup with core economy system
- June 15, 2025. Added steal command with random chance mechanics, crew bonuses, and cooldown system

# User Preferences

Preferred communication style: Simple, everyday language.