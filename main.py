from typing import cast
import uuid
from config import config 
from agents import Agent, RunConfig, Runner, TResponseInputItem
import chainlit as cl
from src.content_manager_agent import content_manager
from openai.types.responses import ResponseTextDeltaEvent , ResponseContentPartDoneEvent

@cl.set_starters
async def set_starters():
    """Defines the starter prompts displayed on the UI."""
    return [
        cl.Starter(
            label="Find beginner-friendly content",
            message="Can you help me find beginner-level content on machine learning?",
            icon="public\search.svg", # <-- Corrected path
        ),
        cl.Starter(
            label="Simplify quantum computing",
            message="Explain quantum computing in simple terms for high school students.",
            icon="public.explain.svg",
        ),
        cl.Starter(
            label="Generate a math PDF",
            message="Create a PDF on the basics of algebra for middle school students.",
            icon="public.pdf.svg",
        ),
        cl.Starter(
            label="Daily AI news summary",
            message="Set up a daily summary of AI news for my email.",
            icon="public.mail.svg", # <-- Corrected path for consistency
        ),
        cl.Starter(
            label="Create a lesson plan",
            message="Coordinate with TutorBot to create a lesson plan on photosynthesis.",
            icon="public.collaborate.svg",
        ),
    ]


@cl.on_chat_start
async def start():

    convo : list[TResponseInputItem] = []

    cl.user_session.set("convo", convo) or []

    # cl.user_session.set("conv_id" , str(uuid.uuid4().hex[:16]))

    cl.user_session.set("content_manager" , content_manager)
    cl.user_session.set("config" , config)

    await cl.Message(content="Hi! what do you want? I can search educational content for you").send()


@cl.on_message
async def main(message : cl.Message):

    convo = cl.user_session.get("convo") or []

    msg = cl.Message("Thinking...\n\n")

    await msg.send()

    convo.append({"role" : "user" , "content" : message.content})

    agent : Agent = cast(Agent , cl.user_session.get("content_manager"))
    config : RunConfig = cast(RunConfig , cl.user_session.get("config"))

    result = Runner.run_streamed(agent, input=convo, run_config=config)

    async for event in result.stream_events():
        if event.type == "raw_response_event" and hasattr(event.data , "delta"):
            token = event.data.delta
            await msg.stream_token(token)
        

    convo.append({"role" : "assistant" , "content" : msg.content})

    cl.user_session.set("convo" , convo)

    print(f"User message : {message.content}")
    print(f"Conversation : {convo}")

        
    


