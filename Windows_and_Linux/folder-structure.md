src
├── aiprovider/
│   ├── __init__.py
│   ├── aiprovider.py
│   ├── anthropic.py
│   ├── gemini.py
│   ├── mistral.py
│   ├── ollama.py
│   ├── openAI_compatible.py
│   ├── openAI.py
│   └── settings.py
├── config/
│   ├── backgrounds/
│   ├── icons/
│   ├── __init__.py
│   ├── api.ts
│   ├── constants.py
│   ├── data_operations.py
│   └── interfaces.py
├── core/
│   ├── __init__.py
│   ├── ai_processor.py
│   ├── clipboard_manager.py
│   ├── hotkey_manager.py
│   ├── image_processor.py
│   ├── input_manager.py
│   ├── lifecycle_manager.py
│   ├── popup_manager.py
│   ├── settings_manager.py
│   ├── text_processor.py
│   └── ui_manager.py
├── locales/
│   └── fr/
│       └── LC_MESSAGES/
├── ui/
│   ├── __init__.py
│   ├── about_window.py
│   ├── custom_popup/
│   │   ├── __init__.py
│   │   ├── button_edit_dialog.py
│   │   ├── custom_popup_window.py
│   │   ├── draggable_button.py
│   │   ├── edit_mode_controller.py
│   │   ├── toggle_switch.py
│   │   ├── top_bar_builder.py
│   │   ├── vision_support_validator.py
│   │   └── widget_visibility_manager.py
│   ├── help_window.py
│   ├── language_manager.py
│   ├── non_editable_modal.py
│   ├── progress_window.py
│   ├── response_window.py
│   ├── SettingsWindow/
│   │   ├── __init__.py
│   │   ├── general_settings.py
│   │   ├── provider_settings.py
│   │   └── settings_window.py
│   ├── theme_manager.py
│   └── ui_utils.py
├── __init__.py
├── autostart_manager.py
├── systray.py
├── update_checker.py
└── writing_tools_app.py

---

## Descriptions détaillées

### aiprovider/
Dossier regroupant tous les modules d'intégration IA (Anthropic, Gemini, etc.). Fournit abstraction commune pour appels API, gestion config, validation connexions.

- `__init__.py`: Package initializer pour aiprovider.
- `aiprovider.py`: Classe de base AIProvider (ABC) : définit interface commune. Fonctions clés: add_button (ajoute boutons UI), refresh_configuration (config mise à jour), get_response/_get_response_impl (traitement requêtes), load/save_config (gestion config), cancel (annulation), validate_connection (test connexion).
- `anthropic.py`: Provider Anthropic: implémente _get_response_impl pour appels Claude API. Hooks: after_load/before_load (setup API).
- `gemini.py`: Provider Gemini: _get_response_impl via Vertex/Google AI. _extract_response_text (parsing réponses), _contains_safety_filter_message (détection filtres). Hooks after_load/before_load.
- `mistral.py`: Provider Mistral: _get_response_impl pour Mistral API. Hooks after_load/before_load.
- `ollama.py`: Provider Ollama: gestion serveurs locaux. OllamaStateManager: exécutable Ollama, installation, modèles, états. Provider: _on_state_updated/_on_models_updated, _refresh_models, refresh_configuration, install_ollama_async, _get_response_impl.
- `openAI_compatible.py`: Provider générique OpenAI-compatible: _get_response_impl flexible pour APIs similaires. Hooks after_load/before_load.
- `openAI.py`: Provider OpenAI officiel: _get_response_impl pour GPT. Hooks after_load/before_load.
- `settings.py`: Paramètres UI providers: AIProviderSetting (ABC), TextSetting/DropdownSetting: render_to_layout (UI), set_value/get_value, refresh_styles. DropdownSetting avec refresh_options.

### config/
Configurations statiques et ressources: constantes, interfaces TypeScript, opérations données, icônes/arrière-plans.

- `__init__.py`: Package initializer pour config.
- `api.ts`: Types TypeScript pour API/config (interfaces communes côté JS).
- `constants.py`: Constantes: ProviderDefaults (configs par défaut), UIDefaults (styles UI).
- `data_operations.py`: Ops données: get_default_model_for_provider (modèles défauts), get_provider_display_name/internal_name (noms providers), create_default_*_config (configs défaut), merge_*_data (fusion user/default), get_available_languages.
- `interfaces.py`: Interfaces Python: ActionConfig, SystemConfig, ProviderConfig, UnifiedSettings (TypedDict pour types stricts).

### core/
Logique cœur app: traitement IA, gestion I/O, cycle vie, popups, paramètres.

- `__init__.py`: Package initializer pour core.
- `ai_processor.py`: AIProcessor: traitement requêtes IA. ContextDetector (instructions système), MessageFormatter (format messages pour providers), process_option (orchestration requêtes), _setup_response_window, process_option_thread, _prepare_prompt_data, _handle_no_text_selected.
- `clipboard_manager.py`: ClipboardManager: sauvegarde/restore/vide clipboard. backup_clipboard, restore_clipboard, clear_clipboard.
- `hotkey_manager.py`: HotkeyManager: gestion raccourcis clavier. register_hotkey (raccourci activation), on_hotkey_pressed (action), check_trigger_spam (anti-spam), setup_ctrl_c_listener (SIGINT).
- `image_processor.py`: ImageProcessor: traitement images clipboard/chemin. get_image_from_clipboard, qimage_to_base64 (encodage), _normalize_path_text.
- `input_manager.py`: InputManager: capture texte sélectionné/entrées. get_selected_text, simulate_ctrl_key, _is_file_path.
- `lifecycle_manager.py`: LifecycleManager: gestion cycle vie app. exit_app, _detect_running_mode (détecte mode dev/final).
- `popup_manager.py`: PopupManager: gestion fenêtres popup. show_popup, position_popup_window, clean_image.
- `settings_manager.py`: SettingsManager: chargement/sauvegarde settings. load_settings, save, has_providers_configured, update_action, _serialize_settings, _setup_logging.
- `text_processor.py`: TextProcessor: traitement texte/output. replace_text, clear_output_queue, _handle_replacement.
- `ui_manager.py`: UIManager: gestion UI global. show_response_window, show_message_box, close_all_windows.

### locales/
Traductions app (actuellement français: fr/LC_MESSAGES/).

### ui/
Interfaces utilisateur: fenêtres, popups, thèmes, langues, utils.

- `__init__.py`: Package initializer pour ui.
- `about_window.py`: AboutWindow: fenêtre 'à propos'. init_ui, _create_layout, _load_content, check_for_updates, refresh_theme/language.
- `help_window.py`: HelpWindow: fenêtre aide. init_ui, _load_content, refresh_theme, closeEvent.
- `language_manager.py`: LanguageManager: gestion langues. register_widget, set_language, setup_translations, _update_translation_functions.
- `non_editable_modal.py`: NonEditableModal: modal texte non-éditable. setup_ui, refresh_theme, copy_text, keyPressEvent.
- `progress_window.py`: ProgressWindow: fenêtres progression. _setup_ui, start_animation/stop_animation, OllamaInstallProgressWindow pour install Ollama.
- `response_window.py`: ResponseWindow: fenêtre réponses IA/chat. init_ui, send_message, copy_as_markdown, MarkdownTextBrowser (affichage MD), MessageContainer, ChatContentScrollArea (scroll chat).
- `theme_manager.py`: ThemeManager: gestion thèmes. change_color_mode, change_background_theme, register_widget, get_styles.
- `ui_utils.py`: Classes utilitaires UI: ui_utils (clear_layout, resize_and_round_image, show_confirmation_dialog), ThemedWidget (base widgets themés), ThemeBackground.

#### custom_popup/
Composants popup personnalisable: boutons drag, toggle, édition.

- `__init__.py`: Package initializer.
- `button_edit_dialog.py`: Dialog édition boutons popup.
- `custom_popup_window.py`: Fenêtre popup principale.
- `draggable_button.py`: Boutons déplaçables popup.
- `edit_mode_controller.py`: Contrôle mode édition popup.
- `toggle_switch.py`: Interrupteurs on/off popup.
- `top_bar_builder.py`: Construction barre supérieure popup.
- `vision_support_validator.py`: Validation support vision.
- `widget_visibility_manager.py`: Gestion visibilité widgets popup.

#### SettingsWindow/
Interface paramètres: général, providers.

- `__init__.py`: Package initializer.
- `general_settings.py`: GeneralSettings: paramètres globaux (_on_autostart_changed, _on_language_changed, _on_shortcut_changed, _on_theme_changed).
- `provider_settings.py`: ProviderSettings: config providers (init_provider_ui, _add_provider_settings, save_current_provider_settings).
- `settings_window.py`: SettingsWindow: fenêtre principale paramètres (init_ui, save_all_settings, focusOutEvent).

### Fichiers racine
- `__init__.py`: Package initializer pour src.
- `autostart_manager.py`: Gestion autostart app (sync_with_settings).
- `systray.py`: Gestion icône systray (create_tray_icon_with_startup_delay).
- `update_checker.py`: Vérification mises à jour (fonctions non listées, probablement vérif version/MAJ async).
- `writing_tools_app.py`: Classe principale WritingToolsApp: orchestre tout (__init__, _setup_core_attributes, _setup_settings, _setup_ui_components, _initialize_ai_provider, _setup_user_interface).
