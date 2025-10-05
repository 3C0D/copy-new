import io
import webbrowser
from typing import TYPE_CHECKING, Any, Union

from PIL import Image as PILImage

from ..config.constants import GEMINI_MODELS
from . import AIProvider, DropdownSetting, TextSetting

# Disable Pylance reportPrivateImportUsage for google.generativeai
# pyright: reportPrivateImportUsage=false

# Google Generative AI imports (with fallbacks)
try:
    import google.generativeai as genai
    from google.generativeai.types import HarmBlockThreshold, HarmCategory
except ImportError:
    # Fallback for type checking
    genai = None  # type: ignore
    HarmBlockThreshold = None  # type: ignore
    HarmCategory = None  # type: ignore

# Local imports
from ..config.data_operations import get_default_model_for_provider

# Type checking imports
if TYPE_CHECKING:
    from ..writing_tools_app import WritingToolsApp


class GeminiProvider(AIProvider):
    """
    Provider for Google's Gemini API.

    Uses google.generativeai.GenerativeModel.generate_content() to generate text.
    Streaming is no longer offered so we always do a single-shot call.
    Handles safety settings to allow less restricted content.
    """

    def __init__(self, app: "WritingToolsApp"):
        self.model: Any = None

        settings = [
            TextSetting(
                app,
                name="api_key",
                display_name="API Key",
                description="Paste your Gemini API key here",
            ),
            DropdownSetting(
                app,
                name="api_model",
                display_name="Model",
                default_value=get_default_model_for_provider("gemini"),
                description="Select Gemini model to use",
                options=GEMINI_MODELS,
            ),
        ]
        super().__init__(
            app,
            "Gemini (Recommended)",
            settings,
            "• Google's Gemini is a powerful AI model available for free!\n"
            "• An API key is required to connect to Gemini on your behalf.\n"
            "• Safety filters are set to 'Block Only High' (most permissive setting available).\n"
            "• If content is still blocked, try rephrasing your request more neutrally.\n"
            "• Click the button below to get your API key.",
            "gemini",
            "Get API Key",
            lambda: webbrowser.open("https://aistudio.google.com/app/apikey"),
            "gemini",
        )

    def _get_response_impl(
        self,
        system_instruction: str,
        prompt: Union[str, list],
        return_response: bool = False,
        **kwargs,
    ) -> str:
        """
        Generate content using Gemini.
        Includes retry logic for safety filter blocks.
        """
        image_data: str | None = kwargs.get("image_data")
        # DEBUG: Log the incoming request
        self._logger.debug("🔥 GeminiProvider.get_response called")
        self._logger.debug(f"🔥 system_instruction length: {len(system_instruction)}")
        self._logger.debug(f"🔥 prompt length: {len(prompt)}")
        self._logger.debug(f"🔥 prompt preview:\n{prompt[:200]}...")
        self._logger.debug(f"🔥 return_response: {return_response}")
        self._logger.debug(f"🔥 image_data present: {image_data is not None}")

        # Check if model is configured
        if not self.model:
            error_msg = "Your Gemini API key is not configured or invalid. Please go to Settings and add a valid API key."
            if not return_response:
                self.app.ui_manager.show_message_signal.emit(
                    "API Key Missing",
                    error_msg,
                )
                return ""
            return error_msg

        # Retry logic for safety filters - up to 3 attempts
        max_retries = 3
        for attempt in range(max_retries):
            attempt_num = attempt + 1
            self._logger.debug(f"Gemini API call - Attempt {attempt_num}/{max_retries}")

            try:
                # Prepare content for Gemini
                if image_data:
                    # Convert base64 to PIL Image like in gemini_integration.py
                    self._logger.debug(
                        f"🖼️\u00a0 GeminiProvider: Converting base64 to PIL Image - length: {len(image_data)}"
                    )
                    if PILImage is not None and io is not None:
                        try:
                            import base64

                            # Decode base64 to bytes
                            image_bytes = base64.b64decode(image_data)
                            # Create PIL Image from bytes
                            pil_image = PILImage.open(io.BytesIO(image_bytes))
                            self._logger.debug(
                                f" 🖼️\u00a0 GeminiProvider: PIL Image created - size: {pil_image.size}, mode: {pil_image.mode}"
                            )

                            # For image analysis, create content with PIL Image and text
                            contents = [system_instruction, pil_image, prompt]
                        except Exception as img_error:
                            self._logger.error(
                                f" 🖼️\u00a0 GeminiProvider: Failed to convert base64 to PIL Image: {img_error}"
                            )
                            # Fallback to inline_data format
                            contents = [
                                system_instruction,
                                {"inline_data": {"mime_type": "image/png", "data": image_data}},
                                prompt,
                            ]
                    else:
                        self._logger.warning(
                            " 🖼️\u00a0 GeminiProvider: PIL not available, using inline_data format"
                        )
                        # Fallback to inline_data format when PIL is not available
                        contents = [
                            system_instruction,
                            {"inline_data": {"mime_type": "image/png", "data": image_data}},
                            prompt,
                        ]
                else:
                    # For text-only requests
                    contents = [system_instruction, prompt]

                # Single-shot call with streaming disabled
                response = self.model.generate_content(contents=contents, stream=False)

                # Check if response was blocked by safety filters
                if not response.candidates:
                    error_detail = "🔥 No candidates in response - empty response"
                    self._logger.warning(f"🔥 Attempt {attempt_num}: {error_detail}")
                    if attempt < max_retries - 1:
                        self._logger.warning(f"🔥 Attempt {attempt_num} failed, retrying...")
                        continue
                    else:
                        self._logger.warning(
                            f"🔥 Final failure after {max_retries} attempts: {error_detail}"
                        )
                        error_msg = "Gemini blocked the request due to safety concerns. Try rephrasing your request."
                        self._logger.error("Gemini response blocked - no candidates returned")
                        self.app.ui_manager.show_message_signal.emit(
                            "Content Blocked",
                            "Your request has been blocked by Gemini's safety filters. Please try rephrasing your request to be more neutral.",
                        )
                        return ""
                # Check the finish reason of the first candidate
                candidate = response.candidates[0]

                # Finish reason meanings:
                # 1: STOP (normal completion)
                # 2: SAFETY (blocked by safety filters)
                # 3: RECITATION (blocked due to recitation)
                # 4: OTHER (other reason)
                if candidate.finish_reason == 2:  # SAFETY
                    error_detail = f"🔥 Safety filter activated (code {candidate.finish_reason})"
                    self._logger.warning(f"🔥 Attempt {attempt_num}: {error_detail}")
                    if attempt < max_retries - 1:
                        self._logger.warning(f"🔥 Attempt {attempt_num} failed, retrying...")
                        continue
                    else:
                        self._logger.warning(
                            f"🔥 Final failure after {max_retries} attempts: {error_detail}"
                        )
                        error_msg = "Gemini blocked the response due to safety filters. Try rephrasing your request to be more neutral."
                        self._logger.warning(
                            f"Gemini safety filter triggered. Finish reason: {candidate.finish_reason}"
                        )
                        self.app.ui_manager.show_message_signal.emit(
                            "Content Blocked by Safety Filters",
                            error_msg,
                        )
                        return ""
                elif candidate.finish_reason == 3:  # RECITATION - No retry for copyright issues
                    error_detail = f"🔥 Copyright filter activated (code {candidate.finish_reason})"
                    self._logger.warning(
                        f"🔥 Attempt {attempt_num}: {error_detail} - No retry for copyright issues"
                    )
                    error_msg = "Gemini blocked the response due to potential copyright concerns. Try a more original request."
                    self._logger.warning(
                        f"Gemini recitation filter triggered. Finish reason: {candidate.finish_reason}"
                    )
                    self.app.ui_manager.show_message_signal.emit(
                        "Content Blocked - Copyright Concern",
                        error_msg,
                    )
                    return ""
                elif candidate.finish_reason not in [
                    1,
                    None,
                ]:  # Not STOP or unset - No retry for other issues
                    error_detail = f"🔥 Unexpected error code (code {candidate.finish_reason})"
                    self._logger.warning(f"🔥 Attempt {attempt_num}: {error_detail} - No retry")
                    error_msg = f"Gemini could not complete the response (reason code: {candidate.finish_reason}). Please try again."
                    self.app.ui_manager.show_message_signal.emit(
                        f"Gemini unusual finish reason: {candidate.finish_reason}",
                        error_msg,
                    )
                    return ""

                # Check if response has content parts
                if not candidate.content or not candidate.content.parts:
                    error_detail = "🔥 Empty response - no content parts"
                    self._logger.warning(f"🔥 Attempt {attempt_num}: {error_detail}")
                    if attempt < max_retries - 1:
                        self._logger.warning(f"🔥 Attempt {attempt_num} failed, retrying...")
                        continue
                    else:
                        self._logger.warning(
                            f"🔥 Final failure after {max_retries} attempts: {error_detail}"
                        )
                        self.app.ui_manager.show_message_signal.emit(
                            "Empty Response",
                            "Gemini returned an empty response. Please try rephrasing your request.",
                        )
                        return ""

                # Extract response text with proper error handling
                response_text = self._extract_response_text(response, candidate)
                self._logger.debug(f"Response text: {response_text}")

                if not response_text:
                    error_detail = "🔥 Could not extract text from response"
                    self._logger.warning(f"🔥 Attempt {attempt_num}: {error_detail}")
                    if attempt < max_retries - 1:
                        self._logger.warning(f"🔥 Attempt {attempt_num} failed, retrying...")
                        continue
                    else:
                        self._logger.warning(
                            f"🔥 Final failure after {max_retries} attempts: {error_detail}"
                        )
                        self.app.ui_manager.show_message_signal.emit(
                            "Response Processing Error",
                            "Could not process the response from Gemini. Please try again.",
                        )
                        return ""

                # Check if response text indicates safety filter (in case finish_reason doesn't show it)
                if self._contains_safety_filter_message(response_text):
                    error_detail = f"🔥 Safety filter message detected: {response_text[:100]}..."
                    self._logger.warning(f"🔥 Attempt {attempt_num}: {error_detail}")
                    if attempt < max_retries - 1:
                        self._logger.warning(f"🔥 Attempt {attempt_num} failed, retrying...")
                        continue
                    else:
                        self._logger.warning(
                            f"🔥 Final failure after {max_retries} attempts: {error_detail}"
                        )
                        self.app.ui_manager.show_message_signal.emit(
                            "Content Blocked by Safety Filters",
                            response_text,
                        )
                        return ""

                # If we get here, we have a valid response - log success and return it
                if attempt > 0:
                    self._logger.debug(f"Gemini response obtained after {attempt_num} attempt(s)")

                self._logger.debug(f"Gemini response length: {len(response_text)}")

                # Direct replacement
                if not return_response and not hasattr(self.app, "current_response_window"):
                    self._logger.debug(
                        f"🔥 Gemini emitting signal with response_text length: {len(response_text)}"
                    )
                    self._logger.debug(
                        f"🔥 Gemini response_text preview: '{response_text[:200]}...'"
                    )
                    self.app.text_processor.output_ready_signal.emit(response_text)
                    self._logger.debug("🔥 Gemini signal emitted, returning empty string")
                    return ""
                # Response window
                return response_text

            except Exception as e:
                error_str = str(e)
                self._logger.exception(f"Error processing Gemini response: {error_str}")

                # Handle specific Gemini API errors with user-friendly messages
                if "API_KEY_INVALID" in error_str or "invalid API key" in error_str.lower():
                    self.app.ui_manager.show_message_signal.emit(
                        "Invalid API Key",
                        "Your Gemini API key is invalid. Please check your API key in Settings and make sure it's correct.",
                    )
                    return ""
                elif (
                    "quota exceeded" in error_str.lower()
                    or "resource exhausted" in error_str.lower()
                ):
                    self.app.ui_manager.show_message_signal.emit(
                        "Quota Exceeded",
                        "You've exceeded your Gemini API quota. Please check your usage limits or try again later.",
                    )
                    return ""
                elif "rate limit" in error_str.lower():
                    self.app.ui_manager.show_message_signal.emit(
                        "Rate Limit Hit",
                        "You're sending requests too quickly. Please wait a moment and try again.",
                    )
                    return ""
                elif "finish_reason" in error_str.lower() and "safety" in error_str.lower():
                    self.app.ui_manager.show_message_signal.emit(
                        "Content Blocked",
                        "Gemini blocked the request due to safety concerns. Try rephrasing your request to be more neutral.",
                    )
                    return ""
                else:
                    # For other errors, if we have retries left, continue
                    if attempt < max_retries - 1:
                        self._logger.warning(
                            f"Gemini API error on attempt {attempt + 1}/{max_retries}: {error_str}, retrying..."
                        )
                        continue
                    else:
                        # Generic error with option to check settings
                        self.app.ui_manager.show_message_signal.emit(
                            "API Error",
                            f"An error occurred with the Gemini API:\n\n{error_str}\n\nPlease check your API key and settings.",
                        )
                        return ""

        return ""

    def _extract_response_text(self, response, candidate) -> str:
        """Extract text from Gemini response with fallback."""
        try:
            return response.text.rstrip("\n")
        except ValueError as text_error:
            # Fallback: manually extract text from parts
            self._logger.warning(f"🔥 Gemini ValueError in response.text: {text_error}")
            text_parts = []
            for part in candidate.content.parts:
                if hasattr(part, "text") and part.text:
                    text_parts.append(part.text)

            if text_parts:
                response_text = "".join(text_parts).rstrip("\n")
                self._logger.debug(f"🔥 Gemini fallback response_text: '{response_text}'")
                return response_text
            else:
                self._logger.warning(f"🔥 Unable to extract text: {str(text_error)}")
                return ""

    def _contains_safety_filter_message(self, text: str) -> bool:
        """Check if text contains safety filter messages."""
        safety_filter_messages = [
            "Content Blocked by Safety Filters",
            "Gemini blocked the response due to safety filters",
        ]
        return any(msg.lower() in text.lower() for msg in safety_filter_messages)

    def after_load(self) -> None:
        """
        Configure the google.generativeai client and create the generative model.

        Only initialize model if API key is provided and genai is available.
        Uses BLOCK_ONLY_HIGH instead of BLOCK_NONE due to 2025 API restrictions.
        """
        # Only configure if API key is provided and genai is available
        if (
            hasattr(self, "api_key")
            and self.api_key
            and self.api_key.strip()
            and genai is not None
            and HarmCategory is not None
            and HarmBlockThreshold is not None
        ):
            # Use try-except to handle the configure method
            try:
                genai.configure(api_key=self.api_key)

                # Updated safety settings for 2025 - BLOCK_NONE is now restricted
                # Use BLOCK_ONLY_HIGH for maximum permissiveness without special access
                safety_settings = {
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                }

                # Check if CIVIC_INTEGRITY category exists (may vary by API version)
                try:
                    civic_integrity_category = getattr(
                        HarmCategory, "HARM_CATEGORY_CIVIC_INTEGRITY", None
                    )
                    if civic_integrity_category is not None:
                        safety_settings[civic_integrity_category] = (
                            HarmBlockThreshold.BLOCK_ONLY_HIGH
                        )
                except (AttributeError, TypeError):
                    # Handle cases where HarmCategory might be None or attribute doesn't exist
                    pass

                self.model = genai.GenerativeModel(
                    model_name=self.api_model,
                    generation_config=genai.types.GenerationConfig(
                        candidate_count=1,
                        max_output_tokens=1000,
                        temperature=0.5,
                    ),
                    safety_settings=safety_settings,
                )

                # Log the safety configuration for debugging
                self._logger.debug(
                    f"Gemini model initialized with BLOCK_ONLY_HIGH safety settings for model: {self.api_model}"
                )

            except AttributeError as e:
                self._logger.error(f"Error configuring Google Generative AI: {e}")
                self.model = None
            except Exception as e:
                # Handle potential API key or configuration errors
                self._logger.error(f"Failed to initialize Gemini model: {e}")
                self.model = None
        else:
            self.model = None

    def before_load(self) -> None:
        """Clean up model instance before reloading."""
        self.model = None
