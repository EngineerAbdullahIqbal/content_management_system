import pathlib
import asyncio
from typing import List
import uuid
from agents import Agent
from config import model
from src.content_manager_tools import (research_education_data , 
                                            scrape_and_structure_data , 
                                            save_data ,
                                            search_database) 

# Define the script's directory (src\Agents)
script_dir = pathlib.Path(__file__).parent

# Correct the path to point to src\system_instructions
instructions_file = script_dir.parent / "src" / "ContentManagerInstructions.markdown"

# Read the file directly
system_prompt = instructions_file.read_text(encoding='utf-8')

content_manager = Agent(
    name="content_manager",
    instructions=system_prompt,
    tools=[
        research_education_data,
        scrape_and_structure_data,
        save_data,
        search_database
    ],
    model=model
)

# EXIT_CAMMANDS : List[str] = [
#     "exit",
#     "quit",
#     "stop",
#     "bye",
#     "goodbye"
# ]

# async def content_manager_runner():

#     conv_id = str(uuid.uuid4().hex[:16])

#     user_msg = input("Hi! what do you want? I can search educational content for you\n> ")
#     if user_msg.lower() in EXIT_CAMMANDS:
#         print("Goodbye 👋")
#         return

#     agent = content_manager  # whatever your starting agent is
#     inputs: list[TResponseInputItem] = [{"content": user_msg, "role": "user"}]

#     try:
#         while True:
#             with trace("Routing example", group_id=conv_id):
#                 result = Runner.run_streamed(agent, input=inputs, run_config=config)
#                 async for event in result.stream_events():
#                     if not isinstance(event, RawResponsesStreamEvent):
#                         continue
#                     data = event.data
#                     if isinstance(data, ResponseTextDeltaEvent):
#                         print(data.delta, end="", flush=True)
#                     elif isinstance(data, ResponseContentPartDoneEvent):
#                         print()

#             inputs = result.to_input_list()
#             print()

#             user_msg = input("> ")
#             if user_msg.lower() in EXIT_CAMMANDS:
#                 print("Goodbye 👋")
#                 break

#             inputs.append({"content": user_msg, "role": "user"})
#             agent = result.current_agent

#     except KeyboardInterrupt:
#         print("\nInterrupted. Exiting now. Goodbye 👋")

# if __name__ == "__main__":
#     asyncio.run(content_manager_runner())
