import bot as Discord
import mongodb as MongoDB
import mqtt_broker as Mosquito
import asyncio

async def main():
    try:
        # await Discord.start()
        MongoDB.run()
        Mosquito.run()
    except Exception as e:
        print(f"Error during setup: {e}")

if __name__ == "__main__":
    asyncio.run(main())