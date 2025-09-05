    def on_onboarding_closed(self) -> None:
        """
        Handle onboarding window being closed.
        Instead of exiting, continue with normal app initialization.
        """
        self._logger.debug("Onboarding window closed, continuing with app initialization")

        # Initialize the current provider with default settings
        provider_name = self.settings_manager.provider

        if not provider_name.strip():
            # Default to Gemini if no provider is set
            provider_name = "gemini"
            self.settings_manager.provider = provider_name

        self.current_provider = next(
            (provider for provider in self.providers if provider.internal_name == provider_name),
            self.providers[0],  # Default to first provider
        )

        # Load provider-specific config from system settings
        if self.current_provider:
            provider_config = self._get_provider_config(provider_name)
            self.current_provider.load_config(provider_config)

        self._sync_autostart_settings()
        self._create_tray_icon_with_startup_delay()
        self.register_hotkey()

        # Set language from system settings
        lang = self.settings_manager.language or "en"
        self.change_language(lang if lang != "en" else "en")

        # Initialize update checker
        self.update_checker = UpdateChecker(self)
        self.update_checker.check_updates_async()
