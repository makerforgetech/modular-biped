import asyncio
import os

from speech_service_api import SpeechService

from viam.logging import getLogger
from viam.robot.client import RobotClient

LOGGER = getLogger(__name__)

# these must be set, you can get them from your robot's 'CODE SAMPLE' tab
robot_api_key_id = os.getenv('ROBOT_API_KEY_ID') or ''
robot_api_key = os.getenv('ROBOT_API_KEY','0') or ''
robot_address = os.getenv('ROBOT_ADDRESS') or ''

async def connect():
    opts = RobotClient.Options.with_api_key(
      api_key=robot_api_key,
      api_key_id=robot_api_key_id,
    )
    return await RobotClient.at_address(robot_address, opts)


async def main():
    robot = await connect()

    LOGGER.info("Resources:")
    LOGGER.info(robot.resource_names)

    speech = SpeechService.from_robot(robot, name="speech-1")

    text = await speech.say("Good day, friend!", True)
    LOGGER.info(f"The robot said '{text}'")

    # note: this will fail unless you have a completion provider configured
    #text = await speech.completion("Give me a quote one might say if they were saying 'Good day, friend!'", False)
    #LOGGER.info(f"The robot said '{text}'")

    # note: this will fail unless you have a completion provider configured
    #text = await speech.completion("Give me a quote one might say regarding this robots resources: " 
    #                               + str(robot.resource_names) + " using documentation at https://docs.viam.com as reference")
    #LOGGER.info(f"The robot said '{text}'")

    is_speaking = await speech.is_speaking()
    LOGGER.info(is_speaking)

    commands = await speech.get_commands(2)
    LOGGER.info(str(commands))
    
    await robot.close()


if __name__ == "__main__":
    asyncio.run(main())