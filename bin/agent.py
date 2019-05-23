import asyncio
from agent import Agent
from config import Config
from conductor import Conductor

if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    config = Config.from_args_file_defaults()

    agent = loop.run_until_complete(Agent.from_config(config))
    agent.conductor = Conductor.from_wallet_handle_config(agent.wallet_handle, config)

    @agent.route('testing')
    async def testing_handler(agent, msg):
        print('got testing')

    # Main loop
    try:
        loop.run_until_complete(agent.start())
    except KeyboardInterrupt:
        print("exiting")
        loop.run_until_complete(agent.shutdown())
