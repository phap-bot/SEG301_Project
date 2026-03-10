import asyncio
import logging
from main import app, lifespan

logging.basicConfig(level=logging.INFO)

async def test():
    try:
        async with lifespan(app):
            print("Lifespan executed successfully.")
    except Exception as e:
        print("Error during lifespan:", e)

if __name__ == "__main__":
    asyncio.run(test())
