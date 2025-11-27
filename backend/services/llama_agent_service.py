"""
LlamaStack Agent Service for EchoNote AI Actions.

Provides a reusable wrapper around LlamaStack async client for executing
AI-powered actions on transcriptions.
"""

import uuid
from typing import Optional
import asyncio

from llama_stack_client import Agent, LlamaStackClient

from backend.config import settings
from backend.logging_config import get_logger

logger = get_logger(__name__)


class LlamaAgentService:
    """
    Service for executing AI actions using LlamaStack async client.

    Each instance is created per-request for proper auditing and isolation.
    This ensures clean audit trails and prevents session mixing.
    """

    def __init__(
        self,
        user_id: int,
        transcription_id: int,
        action_type: str,
        server_url: Optional[str] = None,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """
        Initialize the LlamaAgent service for a specific AI action.

        Args:
            user_id: ID of the user making the request (for auditing)
            transcription_id: ID of the transcription being processed (for auditing)
            action_type: Type of AI action being performed (for auditing)
            server_url: The URL of the Llama Stack server. If None, uses config setting.
            model_name: The name of the model to use. If None, uses config setting.
            api_key: The API key for LlamaStack client. If None, uses config setting.

        Raises:
            ValueError: If server_url or model_name is not provided and not in config.
        """
        self.user_id = user_id
        self.transcription_id = transcription_id
        self.action_type = action_type
        self.server_url = server_url or settings.LLAMA_SERVER_URL
        self.model_name = model_name or settings.LLAMA_MODEL_NAME
        self.api_key = api_key or settings.LLAMA_STACK_CLIENT_API_KEY

        if not self.server_url:
            raise ValueError(
                "LLAMA_SERVER_URL must be provided or set in configuration. "
                "Set the LLAMA_SERVER_URL environment variable."
            )

        if not self.model_name:
            raise ValueError(
                "LLAMA_MODEL_NAME must be provided or set in configuration. "
                "Set the LLAMA_MODEL_NAME environment variable."
            )

        logger.info(
            f"LlamaAgentService created for user_id={user_id}, "
            f"transcription_id={transcription_id}, action={action_type}, "
            f"model={self.model_name}"
        )

    def _run_sync(self, system_prompt: str, user_prompt: str) -> str:
        """
        Synchronous method to run the agent.
        This is called by run() wrapped in asyncio.to_thread().
        """
        session_id = None

        try:
            # Create LlamaStack client (synchronous)
            client = LlamaStackClient(
                base_url=self.server_url,
                api_key=self.api_key
            )

            # Create a new Agent instance for this specific action
            agent = Agent(
                client,
                model=self.model_name,
                instructions=system_prompt,
                tools=[],  # No tools for this simple agent
            )

            # Create a unique session for this interaction
            session_name = f"user{self.user_id}-t{self.transcription_id}-{self.action_type}-{uuid.uuid4()}"
            session_id = agent.create_session(session_name=session_name)

            logger.info(
                f"Created agent session: {session_id} for user_id={self.user_id}, "
                f"transcription_id={self.transcription_id}, action={self.action_type}"
            )

            # Create a turn with the user message
            message = {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": user_prompt}],
            }

            # Call create_turn with stream=False to get direct response
            logger.info("About to call agent.create_turn() with stream=False")
            response = agent.create_turn(
                [message],
                session_id=session_id,
                stream=False
            )

            logger.info(f"create_turn() returned: {type(response)}")

            # Extract text from response
            result_text = response.output_text
            logger.info(f"Extracted output_text: {len(result_text)} chars")

            logger.info(
                f"Agent completed successfully: session={session_id}, "
                f"response_length={len(result_text)} chars"
            )

            return result_text

        except AttributeError as e:
            logger.error(
                f"Failed to parse agent response for user_id={self.user_id}, "
                f"transcription_id={self.transcription_id}, action={self.action_type}: {e}"
            )
            raise Exception(f"Invalid response format from LlamaStack: {e}")
        except Exception as e:
            logger.error(
                f"Agent execution failed for user_id={self.user_id}, "
                f"transcription_id={self.transcription_id}, action={self.action_type}, "
                f"session={session_id}: {e}"
            )
            raise Exception(f"AI action failed: {str(e)}")

    async def run(self, system_prompt: str, user_prompt: str) -> str:
        """
        Run the agent with the given prompts using the synchronous Agent API.

        This async method wraps the synchronous Agent in asyncio.to_thread()
        to avoid blocking the event loop.

        Args:
            system_prompt: The system instruction for the agent.
            user_prompt: The user's input (typically the transcription text).

        Returns:
            The agent's response as a string.

        Raises:
            Exception: If the agent fails to execute or return a response.
        """
        # Run the synchronous agent in a thread pool to avoid blocking
        return await asyncio.to_thread(self._run_sync, system_prompt, user_prompt)
