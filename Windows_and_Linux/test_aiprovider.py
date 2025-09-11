import asyncio
import logging
import sys
from aiprovider import AIProvider, GeminiProvider, OpenAICompatibleProvider, OllamaProvider, AnthropicProvider, MistralProvider
from config.constants import GEMINI_MODELS, OPENAI_MODELS, ANTHROPIC_MODELS, MISTRAL_MODELS
from PySide6.QtCore import Signal

class MockApp:
    def __init__(self):
        self.settings_manager = MockSettingsManager()
        self.output_ready_signal = MockSignal()
        self.show_message_signal = MockSignal()
        self.current_response_window = None
        self.current_provider = None
        self.providers = []
        self._logger = logging.getLogger(__name__)
        self._setup_core_attributes()
        self._setup_signals()

    def _setup_core_attributes(self):
        self.current_response_window = None
        self.current_provider = None
        self.output_queue = ""
        self.original_selection = None
        self.image = None
        self.has_image = bool(self.image is not None)

    def _setup_signals(self):
        self.output_ready_signal.connect(self.replace_text)
        self.show_message_signal.connect(self.show_message_box)

    def replace_text(self, new_text):
        print(f"Replace text called with: {new_text}")

    def show_message_box(self, title, message):
        print(f"Show message box: {title} - {message}")

class MockSettingsManager:
    def __init__(self):
        self.color_mode = "light"
        self.providers = {}
        self.actions = {}
        self.provider = "gemini"
        self.language = "en"

    def save(self):
        return True

    def has_providers_configured(self):
        return True

    def get(self, key, default=None):
        return self.actions.get(key, default)

class MockSignal:
    def __init__(self):
        self.emitted = False
        self.message = None

    def emit(self, *args):
        self.emitted = True
        self.message = args

    def connect(self, slot):
        pass

async def test_gemini_provider():
    app = MockApp()
    provider = GeminiProvider(app)
    provider.api_key = "test_api_key"
    provider.api_model = GEMINI_MODELS[0][1]

    response = await provider.get_response("Test system instruction", "Test prompt")
    print(f"Gemini response: {response}")

async def test_openai_provider():
    app = MockApp()
    provider = OpenAICompatibleProvider(app)
    provider.api_key = "test_api_key"
    provider.api_model = OPENAI_MODELS[0][1]

    response = await provider.get_response("Test system instruction", "Test prompt")
    print(f"OpenAI response: {response}")

async def test_anthropic_provider():
    app = MockApp()
    provider = AnthropicProvider(app)
    provider.api_key = "test_api_key"
    provider.api_model = ANTHROPIC_MODELS[0][1]

    response = await provider.get_response("Test system instruction", "Test prompt")
    print(f"Anthropic response: {response}")

async def test_mistral_provider():
    app = MockApp()
    provider = MistralProvider(app)
    provider.api_key = "test_api_key"
    provider.api_model = MISTRAL_MODELS[0][1]

    response = await provider.get_response("Test system instruction", "Test prompt")
    print(f"Mistral response: {response}")

if __name__ == "__main__":
    asyncio.run(test_gemini_provider())
    asyncio.run(test_openai_provider())
    asyncio.run(test_anthropic_provider())
    asyncio.run(test_mistral_provider())
