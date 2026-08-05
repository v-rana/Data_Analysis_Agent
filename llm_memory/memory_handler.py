from config import settings

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.chat_history import InMemoryChatMessageHistory


from prompt_manager.prompt_component import read_prompt
from llm.llm_obj import llm

class HybridChatMessageHistory(InMemoryChatMessageHistory):
    """Summarizes the messages and preserve latest messages"""
    def __init__(self,llm,buffer_size=2,max_size=4):
        super().__init__()
        self._llm = llm
        self._buffer_size = buffer_size
        self._max_size = max_size
        self._summary = ""
    
    def add_messages(self,message):
        super().add_messages(message)

        if  len(self.messages) < self._max_size:
            return 

        print("summarization....")
        messages_to_summarize = self.messages[:-self._buffer_size]
        summary_prompt = f"""Previous summary: {self._summary}New messages to add to summary:
{self._format_messages(messages_to_summarize)} Create a concise summary preserving key technical details and decisions."""
        
        # Get summary
        summary_response = self._llm.invoke(summary_prompt)
        self._summary = summary_response.content
        # Keep summary + recent buffer
        self.messages = [
            SystemMessage(content=f"Previous conversation summary: {self._summary}")
        ] + self.messages[-self._buffer_size:]
        
    def _summarize_last_messages(self,summary_prompt_name:str = "summary_prompt")->str:
        prompt = read_prompt(summary_prompt_name)
        print("summarization starting...")
        messages = [('system',prompt)]
        template = ChatPromptTemplate.from_messages(messages)
        formatted_messages = self._format_messages(self.messages[:-self._buffer_size])
        params = {"summary":self._summary,"messages_to_summarize":formatted_messages}

        chain = template | self._llm

        llm_result = chain.invoke(params)
        
        summary = llm_result.content

        return summary

    def _format_messages(self, messages):
        """Format messages for summarization"""
        formatted = []
        print("formatting started...")
        for msg in messages:
            role = "Human" if isinstance(msg, HumanMessage) else "AI"
            formatted.append(f"{role}: {msg.content}")

        return "\n".join(formatted)
    

store = {}

def get_hybrid_session_history(session_id: str) -> HybridChatMessageHistory:
    if session_id not in store:
        store[session_id] = HybridChatMessageHistory(llm, buffer_size=4, max_size=6)
    return store[session_id]
