"""
Writing Tools - Default Configuration Constants
Contains all default values for the application settings
"""

# Model options for different providers
from typing import cast

from .interfaces import ActionConfig, ProviderConfig, SystemConfig

GEMINI_MODELS = [
    (
        "Gemini 2.5 Pro (most intelligent | slow | 2 uses/min, 50 uses/day)",
        "gemini-2.5-pro",
        {"vision": True},
    ),
    (
        "Gemini 2.5 Flash Lite Preview (intelligent | fast | preview)",
        "gemini-2.5-flash-lite-preview-06-17",
        {"vision": True},
    ),
    (
        "Gemini 2.5 Flash (very intelligent | fast | 15 uses/min, 1500 uses/day)",
        "gemini-2.5-flash",
        {"vision": True},
    ),
    (
        "Gemini 2.0 Flash (very intelligent | fast | 15 uses/min)",
        "gemini-2.0-flash-001",
        {"vision": True},
    ),
    (
        "Gemini 2.0 Flash Lite (intelligent | very fast | 30 uses/min)",
        "gemini-2.0-flash-lite-preview-02-05",
        {"vision": True},
    ),
    (
        "Gemini 2.0 Pro (most intelligent | slow | 2 uses/min)",
        "gemini-2.0-pro-exp-02-05",
        {"vision": True},
    ),
    (
        "Gemini 2.0 Flash Thinking (most intelligent | slow | 10 uses/min)",
        "gemini-2.0-flash-thinking-exp-01-21",
        {"vision": True},
    ),
    (
        "Gemini 2.0 Flash Thinking Exp (experimental | slow)",
        "gemini-2.0-flash-thinking-exp-1219",
        {"vision": True},
    ),
    (
        "Gemini 2.0 Flash Exp (experimental | fast)",
        "gemini-2.0-flash-exp",
        {"vision": True},
    ),
    (
        "Gemini 1.5 Flash (intelligent | fast)",
        "gemini-1.5-flash-002",
        {"vision": True},
    ),
    (
        "Gemini 1.5 Flash Exp (experimental | fast)",
        "gemini-1.5-flash-exp-0827",
        {"vision": True},
    ),
    (
        "Gemini 1.5 Flash 8B Exp (experimental | fast)",
        "gemini-1.5-flash-8b-exp-0827",
        {"vision": True},
    ),
    (
        "Gemini 1.5 Pro (most intelligent | slow)",
        "gemini-1.5-pro-002",
        {"vision": True},
    ),
    (
        "Gemini 1.5 Pro Exp (experimental | slow)",
        "gemini-1.5-pro-exp-0827",
        {"vision": True},
    ),
    (
        "Gemini Exp 1206 (experimental | slow)",
        "gemini-exp-1206",
        {"vision": True},
    ),
]

OPENAI_MODELS = [
    ("GPT-5 (Most Advanced)", "gpt-5-2025-08-07", {"vision": True}),
    ("GPT-5 Mini (Balanced)", "gpt-5-mini-2025-08-07", {"vision": True}),
    ("GPT-5 Nano (Fast)", "gpt-5-nano-2025-08-07", {"vision": True}),
    ("GPT-5 Chat Latest (Latest)", "gpt-5-chat-latest", {"vision": True}),
    ("O3 (Reasoning)", "o3", {"vision": True}),
    ("O4 Mini (Fast Reasoning)", "o4-mini", {"vision": True}),
    ("GPT-4.1 (Advanced)", "gpt-4.1", {"vision": True}),
    ("GPT-4.1 Mini (Balanced)", "gpt-4.1-mini", {"vision": True}),
    ("GPT-4.1 Nano (Fast)", "gpt-4.1-nano", {"vision": True}),
    ("O1 (Reasoning)", "o1", {"vision": True}),
    ("O1 Preview (Reasoning Preview)", "o1-preview", {"vision": True}),
    ("O1 Mini (Fast Reasoning)", "o1-mini", {"vision": True}),
    ("GPT-4o (Optimized)", "gpt-4o", {"vision": True}),
    ("GPT-4o Mini (Lightweight)", "gpt-4o-mini", {"vision": True}),
    ("ChatGPT-4o Latest (Latest)", "chatgpt-4o-latest", {"vision": True}),
    ("GPT-4 (Most Capable)", "gpt-4", {"vision": False}),
    ("GPT-3.5 Turbo (Fast)", "gpt-3.5-turbo", {"vision": False}),
]

# ("moonshotai/kimi-k2:free", "moonshotai/kimi-k2:free", {"vision": False}),
# ("x-ai/grok-4-fast:free", "x-ai/grok-4-fast:free", {"vision": False}),
# ("google/gemini-2.0-flash-exp:free", "google/gemini-2.0-flash-exp:free", {"vision": True}),

ANTHROPIC_MODELS = [
    (
        "Claude Sonnet 4.5 (Most Advanced)",
        "claude-sonnet-4-5-20250929",
        {"vision": True},
    ),
    (
        "Claude Sonnet 4.5 1M (Most Advanced, Large Context)",
        "claude-sonnet-4-5-20250929:1m",
        {"vision": True},
    ),
    (
        "Claude Sonnet 4 (Advanced)",
        "claude-sonnet-4-20250514",
        {"vision": True},
    ),
    (
        "Claude Sonnet 4 1M (Advanced, Large Context)",
        "claude-sonnet-4-20250514:1m",
        {"vision": True},
    ),
    (
        "Claude Opus 4.1 (Most Capable)",
        "claude-opus-4-1-20250805",
        {"vision": True},
    ),
    (
        "Claude Opus 4 (Most Capable)",
        "claude-opus-4-20250514",
        {"vision": True},
    ),
    (
        "Claude 3.7 Sonnet (Advanced)",
        "claude-3-7-sonnet-20250219",
        {"vision": True},
    ),
    (
        "Claude 3.5 Sonnet (Best for Most Users)",
        "claude-3-5-sonnet-20241022",
        {"vision": True},
    ),
    (
        "Claude 3 Opus (Most Capable, Expensive)",
        "claude-3-opus-20240229",
        {"vision": True},
    ),
    (
        "Claude 3 Haiku (Fast, Affordable)",
        "claude-3-haiku-20240307",
        {"vision": True},
    ),
]

MISTRAL_MODELS = [
    (
        "Mistral Large (most capable)",
        "mistral-large-2411",
        {"vision": False},
    ),
    (
        "Pixtral Large (multimodal | vision)",
        "pixtral-large-2411",
        {"vision": True},
    ),
    (
        "Mistral Small Latest (multimodal | vision)",
        "mistral-small-latest",
        {"vision": True},
    ),
    (
        "Mistral Medium Latest (multimodal | vision)",
        "mistral-medium-latest",
        {"vision": False},
    ),
    (
        "Pixtral 12B (multimodal | vision)",
        "pixtral-12b-2409",
        {"vision": True},
    ),
    (
        "Mistral Nemo (efficient | medium speed | research model)",
        "open-mistral-nemo-2407",
        {"vision": False},
    ),
    (
        "Codestral (code-focused | fast)",
        "codestral-2501",
        {"vision": False},
    ),
    (
        "Devstral Small (code-focused | multimodal)",
        "devstral-small-2505",
        {"vision": False},
    ),
    (
        "Devstral Medium Latest (code-focused | multimodal)",
        "devstral-medium-latest",
        {"vision": False},
    ),
    (
        "Mistral 7B (lightweight | fast | legacy model)",
        "open-mistral-7b",
        {"vision": False},
    ),
]

# Common Ollama models (users can add custom ones)
# NOTE: Ollama models are now automatically detected from the system
OLLAMA_COMMON_MODELS = [
    ("Llama 3.1 8B (Recommended)", "llama3.1:8b", {"vision": False}),
    ("Llama 3.1 70B (More Capable)", "llama3.1:70b", {"vision": False}),
    ("Llama 3.2 3B (Lightweight)", "llama3.2:3b", {"vision": False}),
    ("Gemma 2 9B", "gemma2:9b", {"vision": False}),
    ("Gemma 2 27B", "gemma2:27b", {"vision": False}),
    ("Gemma 3N 2B", "gemma3n:e2b", {"vision": False}),
    ("Gemma 3N 4B", "gemma3n:4b", {"vision": False}),
    ("Qwen 2.5 7B", "qwen2.5:7b", {"vision": False}),
    ("Qwen 2.5 14B", "qwen2.5:14b", {"vision": False}),
    ("CodeLlama 7B", "codellama:7b", {"vision": False}),
    ("CodeLlama 13B", "codellama:13b", {"vision": False}),
]

# Provider internal names to display names mapping
PROVIDER_DISPLAY_NAMES = {
    "gemini": "Gemini (Recommended)",
    "openai": "OpenAI",
    "openai-compatible": "OpenAI Compatible",
    "anthropic": "Anthropic (Claude)",
    "mistral": "Mistral AI",
    "ollama": "Ollama",
}

# Default models for each provider
DEFAULT_MODELS = {
    "gemini": "gemini-2.5-flash",
    "openai": "gpt-4o-mini",
    "anthropic": "claude-3-5-haiku-20241022",
    "mistral": "mistral-small-2503",
    "ollama": "",  # Empty because dynamically generated from ollama list
}

DEFAULT_BASE_URLS = {
    "gemini": "https://generativelanguage.googleapis.com/v1beta",
    "ollama": "http://localhost:11434",
    "mistral": "https://api.mistral.ai/v1",
    "anthropic": "https://api.anthropic.com/v1",
    "openai": "https://api.openai.com/v1",
    "openai-compatible": "https://api.openai.com/v1",
}

DEFAULT_PROVIDER = "gemini"

# Supported languages for UI and AI prompts
SUPPORTED_LANGUAGES = [
    ("English", "en"),
    ("Français", "fr"),
    ("Español", "es"),
    ("Deutsch", "de"),
    ("Italiano", "it"),
    ("Português", "pt"),
    ("Русский", "ru"),
    ("日本語", "ja"),
    ("한국어", "ko"),
    ("中文", "zh"),
    ("العربية", "ar"),
    ("हिन्दी", "hi"),
]

# Language code to full name mapping for AI prompts
LANGUAGE_NAMES = {code: name for name, code in SUPPORTED_LANGUAGES}


def get_available_languages() -> list[tuple[str, str]]:
    """
    Get list of available languages by reading locales directory.
    Returns list of (display_name, code) tuples for languages that have translations.
    """
    from pathlib import Path

    # Get the locales directory path (relative to this file, up to Windows_and_Linux root)
    locales_dir = Path(__file__).parent.parent.parent / "locales"

    available_languages = []

    if locales_dir.exists() and locales_dir.is_dir():
        # Read all subdirectories in locales (each represents a language code)
        for item in locales_dir.iterdir():
            if item.is_dir():
                lang_code = item.name
                # Get display name from our mapping, fallback to capitalized code
                display_name = LANGUAGE_NAMES.get(lang_code, lang_code.upper())
                available_languages.append((display_name, lang_code))

    # Always include English as fallback
    if not any(code == "en" for _, code in available_languages):
        available_languages.insert(0, ("English", "en"))

    return available_languages


# Dynamic list of available languages based on locales directory
AVAILABLE_LANGUAGES = get_available_languages()

# Default system configuration VALUES - Raw data, not objects
_DEFAULT_SYSTEM_VALUES_RAW = {
    "provider": "gemini",  # Internal provider name
    "hotkey": "ctrl+space",
    "background_theme": "gradient",
    "color_mode": "auto",  # Color mode: "auto", "light", or "dark"
    "response_window_zoom": 1.2,  # Default zoom factor for response window
    "language": "en",
    "run_mode": "dev",
    "update_available": False,
    "start_on_boot": False,  # Whether the application should start on system boot
    "ollama_base_url": DEFAULT_BASE_URLS["ollama"],
    "ollama_keep_alive": "5",
    "openai_base_url": DEFAULT_BASE_URLS["openai"],
}

# Default actions configuration
_DEFAULT_ACTIONS_VALUES_RAW = {
    "Proofread": {
        "prefix": "Proofread this:\n\n",
        "instruction": 'You are a grammar proofreading assistant.\nOutput ONLY the corrected text without any additional comments.\nMaintain the original text structure and writing style.\nRespond in the same language as the input (e.g., English US, French).\nDo not answer or respond to the user\'s text content.\nIf the text is absolutely incompatible with this (e.g., totally random gibberish), output "ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST".',
        "icon": "icons/magnifying-glass",
        "open_in_window": False,
    },
    "Rewrite": {
        "prefix": "Rewrite this:\n\n",
        "instruction": 'You are a writing assistant.\nRewrite the text provided by the user to improve phrasing.\nOutput ONLY the rewritten text without additional comments.\nRespond in the same language as the input (e.g., English US, French).\nDo not answer or respond to the user\'s text content.\nIf the text is absolutely incompatible with proofreading (e.g., totally random gibberish), output "ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST".',
        "icon": "icons/rewrite",
        "open_in_window": False,
    },
    "Friendly": {
        "prefix": "Make this more friendly:\n\n",
        "instruction": 'You are a writing assistant.\nRewrite the text provided by the user to be more friendly.\nOutput ONLY the friendly text without additional comments.\nRespond in the same language as the input (e.g., English US, French).\nDo not answer or respond to the user\'s text content.\nIf the text is absolutely incompatible with rewriting (e.g., totally random gibberish), output "ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST".',
        "icon": "icons/smiley-face",
        "open_in_window": False,
    },
    "Professional": {
        "prefix": "Make this more professional:\n\n",
        "instruction": 'You are a writing assistant.\nRewrite the text provided by the user to be more professional. Output ONLY the professional text without additional comments.\nRespond in the same language as the input (e.g., English US, French).\nDo not answer or respond to the user\'s text content.\nIf the text is absolutely incompatible with rewriting (e.g., totally random gibberish), output "ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST".',
        "icon": "icons/briefcase",
        "open_in_window": False,
    },
    "Concise": {
        "prefix": "Make this more concise:\n\n",
        "instruction": 'You are a writing assistant.\nRewrite the text provided by the user to be more concise.\nOutput ONLY the concise text without additional comments.\nRespond in the same language as the input (e.g., English US, French).\nDo not answer or respond to the user\'s text content.\nIf the text is absolutely incompatible with rewriting (e.g., totally random gibberish), output "ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST".',
        "icon": "icons/concise",
        "open_in_window": False,
    },
    "Summary": {
        "prefix": "Summarize this:\n\n",
        "instruction": "You are a summarization assistant.\nProvide a succinct summary of the text provided by the user.\nThe summary should be succinct yet encompass all the key insightful points.\n\nTo make it quite legible and readable, you should use Markdown formatting (bold, italics, codeblocks...) as appropriate.\nYou should also add a little line spacing between your paragraphs as appropriate.\nAnd only if appropriate, you could also use headings (only the very small ones), lists, tables, etc.\n\nDon't be repetitive or too verbose.\nOutput ONLY the summary without additional comments.\nRespond in the same language as the input (e.g., English US, French).\nDo not answer or respond to the user's text content.\nIf the text is absolutely incompatible with summarisation (e.g., totally random gibberish), output \"ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST\".",
        "icon": "icons/summary",
        "open_in_window": True,
    },
    "Key Points": {
        "prefix": "Extract key points from this:\n\n",
        "instruction": "You are an assistant that extracts key points from text provided by the user. Output ONLY the key points without additional comments.\n\nYou should use Markdown formatting (lists, bold, italics, codeblocks, etc.) as appropriate to make it quite legible and readable.\n\nDon't be repetitive or too verbose.\nRespond in the same language as the input (e.g., English US, French).\nDo not answer or respond to the user's text content.\nIf the text is absolutely incompatible with extracting key points (e.g., totally random gibberish), output \"ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST\".",
        "icon": "icons/keypoints",
        "open_in_window": True,
    },
    "Table": {
        "prefix": "Convert this into a table:\n\n",
        "instruction": 'You are an assistant that converts text provided by the user into a Markdown table.\nOutput ONLY the table without additional comments.\nRespond in the same language as the input (e.g., English US, French).\nDo not answer or respond to the user\'s text content.\nIf the text is completely incompatible with this with conversion, output "ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST".',
        "icon": "icons/table",
        "open_in_window": True,
    },
    "Custom": {
        "prefix": "Make this change to the following text:\n\n",
        "instruction": "You are a writing and coding assistant. You MUST make the user\\'s described change to the text or code provided by the user. Output ONLY the appropriately modified text or code without additional comments. When the content is code, PRESERVE the existing indentation level before applying the change and DO NOT add backticks around the code. Respond in the same language as the input (e.g., English US, French). Do not answer or respond to the user\\'s text content. If the text or code is absolutely incompatible with the requested change, output \"ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST\".",
        "icon": "icons/summary",
        "open_in_window": False,
    },
}


# Default image actions configuration
_DEFAULT_IMAGE_ACTIONS_VALUES_RAW = {
    "Img_txt→En": {
        "prefix": "Extract and translate all visible text from this image to English:\n\n",
        "instruction": "You are an image text extraction and translation assistant. Extract all visible text from the provided image and translate it completely to English. Provide ONLY the English translation without any explanations, descriptions, or additional text. Do not describe the image or add any commentary.",
        "icon": "icons/magnifying-glass",
    },
}

DEFAULT_SYSTEM_VALUES: SystemConfig = cast("SystemConfig", _DEFAULT_SYSTEM_VALUES_RAW)

DEFAULT_ACTIONS_VALUES: dict[str, ActionConfig] = {
    name: cast("ActionConfig", values) for name, values in _DEFAULT_ACTIONS_VALUES_RAW.items()
}

DEFAULT_IMAGE_ACTIONS_VALUES: dict[str, ActionConfig] = {
    name: cast("ActionConfig", values) for name, values in _DEFAULT_IMAGE_ACTIONS_VALUES_RAW.items()
}

# Default provider configurations
DEFAULT_PROVIDER_CONFIGS: dict[tuple[str, ...], ProviderConfig] = {
    ("Gemini", "Gemini (Recommended)"): {
        "api_key": "",
        "api_model": DEFAULT_MODELS["gemini"],
        "api_base": DEFAULT_BASE_URLS["gemini"],
    },
    ("Ollama", "Ollama (Local)", "Ollama"): {
        "api_key": "",
        "api_model": DEFAULT_MODELS["ollama"],  # ""
        "api_base": DEFAULT_BASE_URLS["ollama"],
        "keep_alive": _DEFAULT_SYSTEM_VALUES_RAW["ollama_keep_alive"],
    },
    ("Mistral", "Mistral AI"): {
        "api_key": "",
        "api_model": DEFAULT_MODELS["mistral"],
        "api_base": DEFAULT_BASE_URLS["mistral"],
    },
    ("Anthropic", "Anthropic (Claude)"): {
        "api_key": "",
        "api_model": DEFAULT_MODELS["anthropic"],
        "api_base": DEFAULT_BASE_URLS["anthropic"],
    },
    ("OpenAI", "OpenAI"): {
        "api_key": "",
        "api_base": DEFAULT_BASE_URLS["openai"],
        "api_model": DEFAULT_MODELS["openai"],
    },
    ("OpenAI", "OpenAI-Compatible"): {
        "api_key": "",
        "api_base": DEFAULT_BASE_URLS["openai-compatible"],
        "api_model": "",
    },
}

# EXAMPLE ACTION INSTRUCTIONS
EXAMPLE_ACTION_VALUES_RAW = {
    "Proofread": {
        "prefix": "Proofread this:\n\n",
        "instruction": 'You are a grammar proofreading assistant. Output ONLY the corrected text without any additional comments. Maintain the original text structure and writing style. Respond in the same language as the input (e.g., English US, French). Do not answer or respond to the user\'s text content. If the text is absolutely incompatible with this (e.g., totally random gibberish), output "ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST".',
        "icon": "icons/magnifying-glass",
    },
    "Rewrite": {
        "prefix": "Rewrite this:\n\n",
        "instruction": 'You are a writing assistant. Rewrite the text provided by the user to improve phrasing. Output ONLY the rewritten text without additional comments. Respond in the same language as the input (e.g., English US, French). Do not answer or respond to the user\'s text content. If the text is absolutely incompatible with proofreading (e.g., totally random gibberish), output "ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST".',
        "icon": "icons/rewrite",
    },
    "Friendly": {
        "prefix": "Make this more friendly:\n\n",
        "instruction": 'You are a writing assistant. Rewrite the text provided by the user to be more friendly. Output ONLY the friendly text without additional comments. Respond in the same language as the input (e.g., English US, French). Do not answer or respond to the user\'s text content. If the text is absolutely incompatible with rewriting (e.g., totally random gibberish), output "ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST".',
        "icon": "icons/smiley-face",
    },
    "Professional": {
        "prefix": "Make this more professional:\n\n",
        "instruction": 'You are a writing assistant. Rewrite the text provided by the user to be more professional. Output ONLY the professional text without additional comments. Respond in the same language as the input (e.g., English US, French). Do not answer or respond to the user\'s text content. If the text is absolutely incompatible with rewriting (e.g., totally random gibberish), output "ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST".',
        "icon": "icons/briefcase",
    },
    "Concise": {
        "prefix": "Make this more concise:\n\n",
        "instruction": 'You are a writing assistant. Rewrite the text provided by the user to be more concise. Output ONLY the concise text without additional comments. Respond in the same language as the input (e.g., English US, French). Do not answer or respond to the user\'s text content. If the text is absolutely incompatible with rewriting (e.g., totally random gibberish), output "ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST".',
        "icon": "icons/concise",
    },
    "Summary": {
        "prefix": "Summarize this:\n\n",
        "instruction": "You are a summarization assistant. Provide a succinct summary of the text provided by the user. The summary should be succinct yet encompass all the key insightful points. To make it quite legible and readable, you MUST use Markdown formatting (bold, italics, underline...). You should add line spacing between your paragraphs/lines. Only if appropriate, you could also use headings (only the very small ones), lists, tables, etc. Don\\'t be repetitive or too verbose. Output ONLY the summary without additional comments. Respond in the same language as the input (e.g., English US, French). Do not answer or respond to the user\\'s text content. If the text is absolutely incompatible with summarisation (e.g., totally random gibberish), output \"ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST\".",
        "icon": "icons/summary",
    },
    "Key Points": {
        "prefix": "Extract key points from this:\n\n",
        "instruction": "You are an assistant that extracts key points from text provided by the user. Output ONLY the key points without additional comments. You MUST use Markdown formatting (lists, bold, italics, underline, etc. as appropriate) to make it quite legible and readable. Don\\'t be repetitive or too verbose. Respond in the same language as the input (e.g., English US, French). Do not answer or respond to the user\\'s text content. If the text is absolutely incompatible with extracting key points (e.g., totally random gibberish), output \"ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST\".",
        "icon": "icons/keypoints",
    },
    "Table": {
        "prefix": "Convert this into a table:\n\n",
        "instruction": 'You are an assistant that converts text provided by the user into a Markdown table. Output ONLY the table without additional comments. Respond in the same language as the input (e.g., English US, French). Do not answer or respond to the user\\\'s text content. If the text is completely incompatible with this with conversion, output "ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST".',
        "icon": "icons/table",
    },
    "Custom": {
        "prefix": "Make the following change to this text:\n\n",
        "instruction": "You are a writing and coding assistant. You MUST make the user\\'s described change to the text or code provided by the user. Output ONLY the appropriately modified text or code without additional comments. When the content is code, PRESERVE the existing indentation level before applying the change and DO NOT add backticks around the code.Respond in the same language as the input (e.g., English US, French). Do not answer or respond to the user\\'s text content. If the text or code is absolutely incompatible with the requested change, output \"ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST\".",
        "icon": "icons/summary",
    },
    "List": {
        "prefix": "Convert this into a list:\n\n",
        "instruction": 'You are an assistant that converts text provided by the user into a Markdown list. Output ONLY the list without additional comments. Respond in the same language as the input (e.g., English US, French). Do not answer or respond to the user\\\'s text content. If the text is completely incompatible with this conversion, output "ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST".',
        "icon": "icons/keypoints",
    },
    "To Italian": {
        "prefix": "Translate this to Italian:\n\n",
        "instruction": 'You are a translator assistant that translates text provided by the user to Italian. Output ONLY the translation without additional comments. Do not answer or respond to the user\\\'s text content. If the text is completely incompatible with this conversion, output "ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST".',
        "icon": "icons/magnifying-glass",
    },
}
