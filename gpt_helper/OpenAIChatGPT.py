#import os
#import sys
from typing import Any, Dict, List, Union
from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import AgentAction, AgentFinish, LLMResult
#from langchain.agents import AgentType
from langchain.chat_models import ChatOpenAI
#from langchain.agents import initialize_agent, AgentExecutor
#from langchain.tools import BaseTool
#from pydantic import BaseModel, Field
#from langchain.agents.tools import Tool
#from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

#from langchain import PromptTemplate, LLMChain
#from langchain.prompts.chat import (
#    ChatPromptTemplate,
#    SystemMessagePromptTemplate,
#    AIMessagePromptTemplate,
#    HumanMessagePromptTemplate,
#)
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)
from eleven_labs.eleven_labs import ElevenLabs
from ..bark_tts.BarkHelper import BarkHelper
import re

class ChatAgent:
    def __init__(self):
        self._chat = ChatOpenAI(
            streaming=True, 
            callbacks=[AudioOutCallbackHandler()], 
            temperature=0
        )

        """
        self.count = 0
        self.fileName = "tts/generated_audio/raw/bark_generation"
        self.pcmFileName = "tts/generated_audio/pcm/bark_generation"
        self.ext = ".wav"
        """
        
    def chat(self, text):
        #originalFilename = f"{self.fileName}_{self.count}{self.ext}"
        #pcmFilename = f"{self.pcmFileName}_{self.count}{self.ext}"
        self._chat([HumanMessage(content = text)])
        #return pcmFilename

class SentenceChunks:
    def __init__(self, sentence_end_detected_callback):
        self._sentence_end_re = r'(\b(?:Mr|Ms|Dr|Prof|Mrs)\.|\d+)?\s*([.?!])\s*(?!\d)'
        self._sentences = []
        self._last_sentence = []
        self._sentence_end_detected_callback = sentence_end_detected_callback

    # https://chat.openai.com/c/137c936a-acb4-4cb7-9e69-198ef6592f99
    def is_sentence_end(self, token: str) -> bool:
        matches = re.findall(self._sentence_end_re, token)
        for match in matches:
            abbreviation, punctuation = match
            if not abbreviation:
                return True
        return False
    
    def process(self, text):
        self._last_sentence.append(text)
        #sys.stdout.write(f"{text}\n")
        #sys.stdout.flush()
        if self.is_sentence_end(text):
            self._sentences.append("".join(self._last_sentence))
            self._last_sentence = []
            self._sentence_end_detected_callback(self._sentences[-1])

class SentenceProcessor:
    def __init__(self):
        self._sentence_chunks = SentenceChunks(self._sentence_end_detected_callback)
        self._eleven_labs_helper = ElevenLabs()
        #self.bark_helper = BarkHelper()

    def _eleven_labs_audio_stream_callback(self, chunk: bytes):
        print(f"Audio stream callback: {chunk}")

    def _eleven_labs_audio_finished_callback(self, sentence: str):
        print(f"Audio stream finished callback. {sentence}")

    def process(self, text):
        self._sentence_chunks.process(text)

    def _sentence_end_detected_callback(self, sentence):
        print(f"Detected sentence: {sentence} \n<END>")
        #self.bark_helper.generate_audio(sentence)
        self._eleven_labs_helper.generate(sentence)


class AudioOutCallbackHandler(BaseCallbackHandler):
    """Callback handler for streaming. Only works with LLMs that support streaming."""

    _sentence_processor = SentenceProcessor()    

    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        """Run when LLM starts running."""

    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """Run on new LLM token. Only available when streaming is enabled."""
        self._sentence_processor.process(token)

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Run when LLM ends running."""

    def on_llm_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> None:
        """Run when LLM errors."""

    def on_chain_start(
        self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any
    ) -> None:
        """Run when chain starts running."""

    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        """Run when chain ends running."""

    def on_chain_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> None:
        """Run when chain errors."""

    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> None:
        """Run when tool starts running."""

    def on_agent_action(self, action: AgentAction, **kwargs: Any) -> Any:
        """Run on agent action."""
        pass

    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """Run when tool ends running."""

    def on_tool_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> None:
        """Run when tool errors."""

    def on_text(self, text: str, **kwargs: Any) -> None:
        """Run on arbitrary text."""

    def on_agent_finish(self, finish: AgentFinish, **kwargs: Any) -> None:
        """Run on agent end."""
