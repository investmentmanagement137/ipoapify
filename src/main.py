from apify import Actor
import asyncio
import os
import sys

# Import bot engine
from bot_engine import main as run_bot

async def main():
    async with Actor:
        # Get input
        actor_input = await Actor.get_input() or {}
        
        # Environment variable is now set in Dockerfile
        
        print("Starting IPO Bot on Apify...")
        
        # Inject accounts from input if present
        if actor_input.get("accounts"):
            print(f"Loaded {len(actor_input['accounts'])} accounts from Input.")
            import config_and_utils
            config_and_utils.ACCOUNTS = actor_input['accounts']
        
        # Run the bot in headless mode (enforced on Apify)
        await run_bot(headless=True)

if __name__ == "__main__":
    asyncio.run(main())
