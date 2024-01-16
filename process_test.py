import asyncio

from viam.logging import getLogger
LOGGER = getLogger(__name__)

async def main():
    LOGGER.info('INIT MAKERFORGE PROCESS_TEST')
    LOGGER.warning('INIT MAKERFORGE PROCESS_TEST')
    LOGGER.error('INIT MAKERFORGE PROCESS_TEST')
    print("TEST MESSAGE")

asyncio.run(main())