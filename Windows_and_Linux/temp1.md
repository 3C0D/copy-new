Voici les modifications à apporter :

## openAI_compatible.py

```python
class OpenAICompatibleProvider(AIProvider):
    """
    Provider for OpenAI-compatible APIs.

    Uses self.client.chat.completions.create() to obtain a response.
    Streaming is fully removed. Supports APIs with organization
    and project authentication.
    """

    def __init__(self, app: "WritingToolsApp"):
        self.client: Any = None
        self._fetched_models: list[str] = []  # Store fetched models

        settings = [
            TextSetting(
                app,
                name="api_key",
                display_name="API Key",
                description="API key for the OpenAI-compatible API.",
            ),
            TextSetting(
                app,
                "api_base",
                "API Base URL",
                "https://api.openai.com/v1",
                "E.g. https://api.openai.com/v1",
            ),
            TextSetting(
                app,
                "api_organisation",
                "API Organisation",
                "",
                "Leave blank if not applicable.",
            ),
            TextSetting(
                app,
                name="api_project",
                display_name="API Project",
                default_value="",
                description="Leave blank if not applicable.",
            ),
            # Will be replaced by DropdownSetting if models are fetched
            TextSetting(
                app,
                name="api_model",
                display_name="API Model",
                default_value="",
                description="Add a custom model name",
            ),
            CheckboxSetting(
                app,
                name="has_vision",
                display_name="Has Vision",
                default_value=False,
                description="Check if this model supports vision/image analysis",
            ),
        ]
        super().__init__(
            app,
            "OpenAI Compatible",
            cast(list[AIProviderSetting], settings),
            "• Connect to any OpenAI-compatible API (v1/chat/completions).\n"
            "• An API key is required for authentication.",
            "openai-compatible",
        )

    # ... (existing _get_response_impl, after_load, supports_vision, before_load methods)

    def fetch_models(self) -> list[str]:
        """
        Fetch available models from the API endpoint.
        
        Returns:
            List of model IDs if successful, empty list otherwise.
        """
        if not self.api_base or not self.api_key:
            self._logger.debug("Cannot fetch models: missing api_base or api_key")
            return []

        try:
            import requests
            
            # Normalize api_base
            api_base = self.api_base.rstrip('/')
            models_url = f"{api_base}/models"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            self._logger.debug(f"Fetching models from: {models_url}")
            response = requests.get(models_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                # Handle OpenAI-style response format
                if isinstance(data, dict) and "data" in data:
                    models = [model.get("id") for model in data["data"] if "id" in model]
                    self._logger.debug(f"Successfully fetched {len(models)} models")
                    self._fetched_models = models
                    return models
                else:
                    self._logger.warning(f"Unexpected response format: {data}")
                    return []
            else:
                self._logger.warning(f"Failed to fetch models: {response.status_code}")
                return []
                
        except Exception as e:
            self._logger.error(f"Error fetching models: {e}")
            return []

    def get_fetched_models(self) -> list[str]:
        """Get the list of fetched models."""
        return self._fetched_models
```

## provider_settings.py

```python
from .settings import AIProviderSetting, CheckboxSetting, DropdownSetting

# ... (existing imports and class definition)

class ProviderSettings(QWidget):
    # ... (existing __init__ and init_ui methods)

    def _add_provider_settings(self, provider: "AIProvider", provider_config: dict) -> None:
        """Add provider settings controls with weakref-based callback."""
        if self.current_provider_layout is None:
            return

        # ... (existing initialization code)

        # Add preset UI for openai-compatible
        if provider.internal_name == "openai-compatible":
            self._add_preset_ui(provider, provider_config)

        # Fetch models for openai-compatible if api_base and api_key are set
        if provider.internal_name == "openai-compatible":
            self._try_fetch_and_replace_model_setting(provider, provider_config)

        # Use weakref to avoid reference cycles
        provider_ref = weakref.ref(provider)
        provider_manager_ref = weakref.ref(self.provider_manager)

        for setting in provider.settings:
            saved_value = provider_config.get(setting.name, setting.default_value)
            setting.set_value(saved_value)

            # Connect api_base changes to fetch models
            if provider.internal_name == "openai-compatible" and setting.name == "api_base":
                def create_api_base_callback(p_ref, pm_ref, s):
                    def on_api_base_changed():
                        provider_obj = p_ref()
                        if provider_obj is not None:
                            s.auto_save_callback() if s.auto_save_callback else None
                            self._try_fetch_and_replace_model_setting(provider_obj, provider_config)
                    return on_api_base_changed
                
                if hasattr(setting, 'input'):
                    setting.input.editingFinished.connect(
                        create_api_base_callback(provider_ref, provider_manager_ref, setting)
                    )

            # ... (existing auto_save_callback code)
            
            setting.render_to_layout(self.current_provider_layout)

    def _try_fetch_and_replace_model_setting(
        self, provider: "AIProvider", provider_config: dict
    ) -> None:
        """
        Attempt to fetch models and replace the api_model TextSetting with a DropdownSetting.
        """
        if provider.internal_name != "openai-compatible":
            return

        # Fetch models
        from .openAI_compatible import OpenAICompatibleProvider
        
        if not isinstance(provider, OpenAICompatibleProvider):
            return

        models = provider.fetch_models()
        
        if not models:
            self._logger.debug("No models fetched, keeping TextSetting")
            return

        # Find and replace the api_model setting
        model_setting_index = None
        for i, setting in enumerate(provider.settings):
            if setting.name == "api_model":
                model_setting_index = i
                break

        if model_setting_index is None:
            return

        # Get current model value
        current_model = provider_config.get("api_model", "")
        
        # If no model is selected, select the first one
        if not current_model and models:
            current_model = models[0]
            provider_config["api_model"] = current_model

        # Create DropdownSetting with fetched models
        options = [(model, model) for model in models]
        
        dropdown_setting = DropdownSetting(
            self.app,
            name="api_model",
            display_name="API Model",
            default_value=current_model,
            description="Select a model",
            options=options,
        )

        # Replace the setting
        provider.settings[model_setting_index] = dropdown_setting
        
        self._logger.debug(f"Replaced api_model TextSetting with DropdownSetting ({len(models)} models)")

    # ... (rest of existing methods unchanged)
```

## settings.py

```python
# No changes needed - DropdownSetting already exists and supports the required functionality
```

## interfaces.py

```python
class ProviderConfig(TypedDict, total=False):
    api_key: str
    api_model: str
    api_base: str | None
    keep_alive: str | None
    api_project: str | None
    api_organisation: str | None
    has_vision: bool | None
    recorded: dict[str, dict[str, Any]]
    fetched_models: list[str] | None  # Add support for storing fetched models
```