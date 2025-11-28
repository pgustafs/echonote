"""
LlamaStack Agent Service for EchoNote AI Actions.

Provides a reusable wrapper around LlamaStack async client for executing
AI-powered actions on transcriptions.
"""

import uuid
from typing import Optional, Tuple
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
        session_id: Optional[str] = None,
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
            session_id: Optional LlamaStack session ID to reuse for multi-turn conversation
            server_url: The URL of the Llama Stack server. If None, uses config setting.
            model_name: The name of the model to use. If None, uses config setting.
            api_key: The API key for LlamaStack client. If None, uses config setting.

        Raises:
            ValueError: If server_url or model_name is not provided and not in config.
        """
        self.user_id = user_id
        self.transcription_id = transcription_id
        self.action_type = action_type
        self.session_id = session_id
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

        if session_id:
            logger.info(
                f"LlamaAgentService created for session reuse: session_id={session_id}, "
                f"user_id={user_id}, transcription_id={transcription_id}, action={action_type}"
            )
        else:
            logger.info(
                f"LlamaAgentService created for new session: user_id={user_id}, "
                f"transcription_id={transcription_id}, action={action_type}, model={self.model_name}"
            )

    def _run_sync(self, system_prompt: str, user_prompt: str) -> Tuple[str, str]:
        """
        Synchronous method to run the agent.
        This is called by run() wrapped in asyncio.to_thread().

        Returns:
            Tuple of (result_text, session_id)
        """
        session_id = self.session_id  # May be None for new session, or existing session_id

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

            # Create or reuse session
            if not session_id:
                # Create a new session
                session_name = f"user{self.user_id}-t{self.transcription_id}-{self.action_type}-{uuid.uuid4()}"
                session_id = agent.create_session(session_name=session_name)

                logger.info(
                    f"Created new agent session: {session_id} for user_id={self.user_id}, "
                    f"transcription_id={self.transcription_id}, action={self.action_type}"
                )
            else:
                # Reusing existing session
                logger.info(
                    f"Reusing existing session: {session_id} for user_id={self.user_id}, "
                    f"transcription_id={self.transcription_id}, action={self.action_type}"
                )

            # Create a turn with the user message
            message = {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": user_prompt}],
            }

            # Call create_turn with stream=False to get direct response
            logger.debug(f"Calling agent.create_turn() with stream=False, session_id={session_id}")
            response = agent.create_turn(
                [message],
                session_id=session_id,
                stream=False
            )

            logger.debug(f"create_turn() returned: {type(response)}")

            # Extract text from response and strip leading/trailing whitespace
            result_text = response.output_text.strip()
            logger.info(
                f"Agent completed successfully: session={session_id}, "
                f"response_length={len(result_text)} chars, reused_session={self.session_id is not None}"
            )

            # Return both result and session_id
            return result_text, session_id

        except AttributeError as e:
            logger.error(
                f"Failed to parse agent response for user_id={self.user_id}, "
                f"transcription_id={self.transcription_id}, action={self.action_type}, "
                f"session={session_id}: {e}"
            )
            raise Exception(f"Invalid response format from LlamaStack: {e}")
        except Exception as e:
            logger.error(
                f"Agent execution failed for user_id={self.user_id}, "
                f"transcription_id={self.transcription_id}, action={self.action_type}, "
                f"session={session_id}: {e}"
            )
            raise Exception(f"AI action failed: {str(e)}")

    async def run(self, system_prompt: str, user_prompt: str) -> Tuple[str, str]:
        """
        Run the agent with the given prompts using the synchronous Agent API.

        This async method wraps the synchronous Agent in asyncio.to_thread()
        to avoid blocking the event loop.

        Args:
            system_prompt: The system instruction for the agent.
            user_prompt: The user's input (typically the transcription text).

        Returns:
            Tuple of (result_text, session_id) for potential session reuse

        Raises:
            Exception: If the agent fails to execute or return a response.
        """
        # Run the synchronous agent in a thread pool to avoid blocking
        return await asyncio.to_thread(self._run_sync, system_prompt, user_prompt)

    async def cleanup_session(self, session_id: str) -> None:
        """
        Cleanup a LlamaStack session when no longer needed.

        This should be called when:
        - User closes the AI action modal
        - User navigates away
        - Session is no longer needed

        Args:
            session_id: The session ID to cleanup

        Note:
            This method runs in a thread pool to avoid blocking.
            Errors are logged but don't raise exceptions (cleanup is best-effort).
        """
        def _cleanup_sync(sid: str) -> None:
            """Synchronous cleanup method."""
            try:
                client = LlamaStackClient(
                    base_url=self.server_url,
                    api_key=self.api_key
                )

                agent = Agent(
                    client,
                    model=self.model_name,
                    instructions="",  # Not used for cleanup
                    tools=[],
                )

                # Attempt to delete the session
                agent.delete_session(sid)

                logger.info(
                    f"Successfully cleaned up session: {sid}, user_id={self.user_id}"
                )

            except AttributeError:
                # delete_session method might not exist in all LlamaStack versions
                logger.debug(
                    f"Session cleanup not available (delete_session method missing): {sid}"
                )
            except Exception as cleanup_error:
                # Log cleanup errors but don't fail
                logger.warning(
                    f"Failed to cleanup session {sid} for user_id={self.user_id}: {cleanup_error}"
                )

        # Run cleanup in thread pool (best-effort, don't block)
        try:
            await asyncio.to_thread(_cleanup_sync, session_id)
        except Exception as e:
            logger.warning(f"Cleanup thread execution failed for session {session_id}: {e}")
