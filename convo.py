from simple_llm.clients.openai import OpenAIAgent
from simple_llm.agents.delegator import DelegatorClient
from simple_llm.embeddings.openai import openai_embedding
from qdrant_client import QdrantClient
from simple_llm.agent import Agent
from typing import Generator

from agents import PersonaDelegator, HelperAgent

client = QdrantClient(path="prompt_db-qdrant")
db = DelegatorClient(client, "persona-delegation", openai_embedding)

DELEGATION_ERROR_MSG = "Sorry, I am unsure who sent this message. Could you please provide your name, or provide more context?"

class Conversation:
    def __init__(self, personas: list[str]):
        self.delegator = PersonaDelegator(
            agent_cls=OpenAIAgent,
            model="gpt-4o-mini",
            personas=personas,
            delegator_client=db
        )

        default_agent = OpenAIAgent(name="assistant", model="gpt-4o-mini", system_message="You are a helpful assistant", stream=True)
        self.agents: list[Agent] = [default_agent]+[HelperAgent(persona) for persona in personas]

    def run(self, query: str):
        user_index = self.delegator.delegate(query)
        if user_index == 0:
            raise Exception("Unsure which user sent the message.")
        agent: Agent = self.agents[int(user_index)]
        print("we're here")
        agent.start_chat(query, stream=True)

    def stream_reply(self, query: str) -> str | Generator:
        try:
            user_index = int(self.delegator.delegate(query))
            #print(f"Delegated to user index: {user_index}")
        except ValueError:
            #print("ValueError in delegation")
            yield DELEGATION_ERROR_MSG
            return
        if user_index == 0:
            #print("Delegator unsure of user")
            yield DELEGATION_ERROR_MSG
            return
        agent: Agent = self.agents[int(user_index)]
        #print(f"Using agent: {agent.name}")
        
        # stream the agent's reply
        for chunk in agent.stream_reply(query):
            #print(f"Chunk from agent: {chunk}")
            yield chunk
    
    def nostream_reply(self, query: str) -> str:
        try:
            user_index = int(self.delegator.delegate(query))
        except ValueError:
            return DELEGATION_ERROR_MSG
        if user_index == 0:
            return DELEGATION_ERROR_MSG
        agent: Agent = self.agents[int(user_index)]
        return agent.nostream_reply(query)