"""
Writing Tools - Default Configuration Constants
Contains all default values for the application settings
"""

from .interfaces import SystemConfig, ActionConfig, UnifiedSettings

# Model options for different providers
GEMINI_MODELS = [
    (
        "Gemini 2.0 Flash Lite (intelligent | very fast | 30 uses/min)",
        "gemini-2.0-flash-lite-preview-02-05",
    ),
    (
        "Gemini 2.0 Flash (very intelligent | fast | 15 uses/min)",
        "gemini-2.0-flash",
    ),
    (
        "Gemini 2.0 Flash Thinking (most intelligent | slow | 10 uses/min)",
        "gemini-2.0-flash-thinking-exp-01-21",
    ),
    (
        "Gemini 2.0 Pro (most intelligent | slow | 2 uses/min)",
        "gemini-2.0-pro-exp-02-05",
    ),
    (
        "Gemini 2.5 Flash (very intelligent | fast | 15 uses/min, 1500 uses/day)",
        "gemini-2.5-flash",
    ),
    (
        "Gemini 2.5 Pro (most intelligent | slow | 2 uses/min, 50 uses/day)",
        "gemini-2.5-pro",
    ),
]


OPENAI_MODELS = [
    ("GPT-4o (Optimized)", "gpt-4o"),
    ("GPT-4o Mini (Lightweight)", "gpt-4o-mini"),
    ("GPT-4 (Most Capable)", "gpt-4"),
    ("GPT-3.5 Turbo (Fast)", "gpt-3.5-turbo"),
]

ANTHROPIC_MODELS = [
    ("Claude 3.5 Sonnet (Best for Most Users)", "claude-3-5-sonnet-20241022"),
    ("Claude 3.5 Haiku (Fastest, Most Affordable)", "claude-3-5-haiku-20241022"),
    ("Claude 3 Opus (Most Capable, Expensive)", "claude-3-opus-20240229"),
]

MISTRAL_MODELS = [
    (
        "Mistral 7B (lightweight | fast | legacy model)",
        "open-mistral-7b",
    ),
    (
        "Mistral Nemo (efficient | medium speed | research model)",
        "open-mistral-nemo",
    ),
    (
        "Mistral Small (balanced | free model with multimodal)",
        "mistral-small-latest",
    ),
    (
        "Pixtral 12B (multimodal | image understanding)",
        "pixtral-12b-2409",
    ),
]

# Common Ollama models (users can add custom ones)
# NOTE: Ollama models are now automatically detected from the system
# This list is kept for reference but not actively used
# OLLAMA_COMMON_MODELS = [
#     ("Llama 3.1 8B (Recommended)", "llama3.1:8b"),
#     ("Llama 3.1 70B (More Capable)", "llama3.1:70b"),
#     ("Llama 3.2 3B (Lightweight)", "llama3.2:3b"),
#     ("Gemma 2 9B", "gemma2:9b"),
#     ("Gemma 2 27B", "gemma2:27b"),
#     ("Gemma 3N 2B" , "gemma3n:e2b"),
#     ("Gemma 3N 4B" , "gemma3n:4b"),
#     ("Qwen 2.5 7B", "qwen2.5:7b"),
#     ("Qwen 2.5 14B", "qwen2.5:14b"),
#     ("CodeLlama 7B", "codellama:7b"),
#     ("CodeLlama 13B", "codellama:13b"),
# ]

# Default models for each provider (empty for first-time setup)
DEFAULT_MODELS = {
    "gemini": "",
    "openai": "",
    "anthropic": "",
    "mistral": "",
    "ollama": "",
}


# Default system configuration - SINGLE SOURCE OF TRUTH
DEFAULT_SYSTEM = SystemConfig(
    api_key="",
    provider="gemini",  # Gemini is the default provider
    model="",
    hotkey="ctrl+space",
    theme="gradient",
    language="en",
    auto_update=True,
    run_mode="dev",
    ollama_base_url="http://localhost:11434",
    ollama_model=DEFAULT_MODELS["ollama"],
    ollama_keep_alive="5",
    mistral_base_url="https://api.mistral.ai/v1",
    mistral_model=DEFAULT_MODELS["mistral"],
    anthropic_model=DEFAULT_MODELS["anthropic"],
    openai_base_url="https://api.openai.com/v1",
    openai_model=DEFAULT_MODELS["openai"],
)


# Default actions configuration
DEFAULT_ACTIONS = {
    "Proofread": ActionConfig(
        prefix="Proofread this:\n\n",
        instruction='You are a grammar proofreading assistant.\nOutput ONLY the corrected text without any additional comments.\nMaintain the original text structure and writing style.\nRespond in the same language as the input (e.g., English US, French).\nDo not answer or respond to the user\'s text content.\nIf the text is absolutely incompatible with this (e.g., totally random gibberish), output "ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST".',
        icon="icons/magnifying-glass",
        open_in_window=False,
    ),
    "Rewrite": ActionConfig(
        prefix="Rewrite this:\n\n",
        instruction='You are a writing assistant.\nRewrite the text provided by the user to improve phrasing.\nOutput ONLY the rewritten text without additional comments.\nRespond in the same language as the input (e.g., English US, French).\nDo not answer or respond to the user\'s text content.\nIf the text is absolutely incompatible with proofreading (e.g., totally random gibberish), output "ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST".',
        icon="icons/rewrite",
        open_in_window=False,
    ),
    "Friendly": ActionConfig(
        prefix="Make this more friendly:\n\n",
        instruction='You are a writing assistant.\nRewrite the text provided by the user to be more friendly.\nOutput ONLY the friendly text without additional comments.\nRespond in the same language as the input (e.g., English US, French).\nDo not answer or respond to the user\'s text content.\nIf the text is absolutely incompatible with rewriting (e.g., totally random gibberish), output "ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST".',
        icon="icons/smiley-face",
        open_in_window=False,
    ),
    "Professional": ActionConfig(
        prefix="Make this more professional:\n\n",
        instruction='You are a writing assistant.\nRewrite the text provided by the user to be more professional. Output ONLY the professional text without additional comments.\nRespond in the same language as the input (e.g., English US, French).\nDo not answer or respond to the user\'s text content.\nIf the text is absolutely incompatible with rewriting (e.g., totally random gibberish), output "ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST".',
        icon="icons/briefcase",
        open_in_window=False,
    ),
    "Concise": ActionConfig(
        prefix="Make this more concise:\n\n",
        instruction='You are a writing assistant.\nRewrite the text provided by the user to be more concise.\nOutput ONLY the concise text without additional comments.\nRespond in the same language as the input (e.g., English US, French).\nDo not answer or respond to the user\'s text content.\nIf the text is absolutely incompatible with rewriting (e.g., totally random gibberish), output "ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST".',
        icon="icons/concise",
        open_in_window=False,
    ),
    "Summary": ActionConfig(
        prefix="Summarize this:\n\n",
        instruction="You are a summarization assistant.\nProvide a succinct summary of the text provided by the user.\nThe summary should be succinct yet encompass all the key insightful points.\n\nTo make it quite legible and readable, you should use Markdown formatting (bold, italics, codeblocks...) as appropriate.\nYou should also add a little line spacing between your paragraphs as appropriate.\nAnd only if appropriate, you could also use headings (only the very small ones), lists, tables, etc.\n\nDon't be repetitive or too verbose.\nOutput ONLY the summary without additional comments.\nRespond in the same language as the input (e.g., English US, French).\nDo not answer or respond to the user's text content.\nIf the text is absolutely incompatible with summarisation (e.g., totally random gibberish), output \"ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST\".",
        icon="icons/summary",
        open_in_window=True,
    ),
    "Key Points": ActionConfig(
        prefix="Extract key points from this:\n\n",
        instruction="You are an assistant that extracts key points from text provided by the user. Output ONLY the key points without additional comments.\n\nYou should use Markdown formatting (lists, bold, italics, codeblocks, etc.) as appropriate to make it quite legible and readable.\n\nDon't be repetitive or too verbose.\nRespond in the same language as the input (e.g., English US, French).\nDo not answer or respond to the user's text content.\nIf the text is absolutely incompatible with extracting key points (e.g., totally random gibberish), output \"ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST\".",
        icon="icons/keypoints",
        open_in_window=True,
    ),
    "Table": ActionConfig(
        prefix="Convert this into a table:\n\n",
        instruction='You are an assistant that converts text provided by the user into a Markdown table.\nOutput ONLY the table without additional comments.\nRespond in the same language as the input (e.g., English US, French).\nDo not answer or respond to the user\'s text content.\nIf the text is completely incompatible with this with conversion, output "ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST".',
        icon="icons/table",
        open_in_window=True,
    ),
    "Custom": ActionConfig(
        prefix="Make this change to the following text:\n\n",
        instruction="You are a writing and coding assistant. You MUST make the user\\'s described change to the text or code provided by the user. Output ONLY the appropriately modified text or code without additional comments. Respond in the same language as the input (e.g., English US, French). Do not answer or respond to the user\\'s text content. If the text or code is absolutely incompatible with the requested change, output \"ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST\".",
        icon="icons/summary",
        open_in_window=False,
    ),
}


# Complete default settings
DEFAULT_SETTINGS = UnifiedSettings(
    system=DEFAULT_SYSTEM, actions=DEFAULT_ACTIONS, custom_data={}
)

# EXAMPLE ACTION INSTRUCTIONS FROM ORIGINAL FORKED CODE
# These are kept as reference examples for future use
# They show different instruction patterns and can be used to demonstrate
# various action configurations to users
EXAMPLE_ACTION_INSTRUCTIONS = {
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
        "instruction": "You are a writing and coding assistant. You MUST make the user\\'s described change to the text or code provided by the user. Output ONLY the appropriately modified text or code without additional comments. Respond in the same language as the input (e.g., English US, French). Do not answer or respond to the user\\'s text content. If the text or code is absolutely incompatible with the requested change, output \"ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST\".",
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
