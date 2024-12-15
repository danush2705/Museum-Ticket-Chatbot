from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.memory import ConversationBufferMemory
from langchain.chains.llm import LLMChain
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage
from langchain_core.prompts.chat import MessagesPlaceholder
from langchain_core.prompts.chat import HumanMessagePromptTemplate

# Initialize the Groq chat model
groq_chat = ChatGroq(
    temperature=0.7,
    groq_api_key="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",
    model="llama3-70b-8192"
)

# Persistent system prompt to set the context for the chatbot
system_prompt = """
You are a helpful assistant. You can assist the user with booking, canceling, or viewing ticket details for the museum. 
If the user greets you or asks how you are doing, respond politely and then guide them on how you can assist.
"""

# Initialize conversational memory
# memory = ConversationBufferMemory()

def chat_bot(user_question):

    if user_question:
        # Construct the chat prompt template
        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=system_prompt),
                # MessagesPlaceholder(variable_name="chat_history"),
                HumanMessagePromptTemplate.from_template("{human_input}")
            ]
        )

        # Create a conversation chain
        conversation = LLMChain(
            llm=groq_chat,
            prompt=prompt,
            verbose=False
        )

        # Generate the chatbot's response
        response = conversation.predict(human_input=user_question)
        return response