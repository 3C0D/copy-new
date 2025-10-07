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
│   ├── ai/  # Nouveau dossier pour refactoriser ai_processor.py
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
└── writing_tools_app.py

---

## Descriptions détaillées

### aiprovider/

Dossier regroupant tous les modules d'intégration IA (Anthropic, Gemini, etc.). Fournit abstraction commune pour appels API, gestion config, validation connexions.

- `__init__.py`: Package initializer pour aiprovider.
- `aiprovider.py`: Classe de base AIProvider (ABC) : définit interface commune. Fonctions clés: add_button (ajoute boutons UI), refresh_configuration (config mise à jour), get_response/_get_response_impl (traitement requêtes), load/save_config (gestion config), cancel (annulation), validate_connection (test connexion).
- `anthropic.py`: Provider Anthropic: implémente _get_response_impl pour appels Claude API. Hooks: after_load/before_load (setup API).
- `gemini.py`: Provider Gemini: _get_response_impl via Vertex/Google AI._extract_response_text (parsing réponses), _contains_safety_filter_message (détection filtres). Hooks after_load/before_load.
- `mistral.py`: Provider Mistral: _get_response_impl pour Mistral API. Hooks after_load/before_load.
- `ollama.py`: Provider Ollama (compatibilité): fichier de compatibilité maintenant allégé (18 lignes) important les classes séparées depuis ollama_provider.py et ollama_state.py.
- `ollama_provider.py`: Provider Ollama: implémentation du provider IA pour serveur Ollama (_on_state_updated/_on_models_updated, _refresh_models, refresh_configuration,_get_response_impl).
- `ollama_state.py`: Gestionnaire d'état Ollama: exécutable Ollama, installation, modèles, états, cache, opérations asynchrones (OllamaStateManager).
- `openAI_compatible.py`: Provider générique OpenAI-compatible: _get_response_impl flexible pour APIs similaires. Hooks after_load/before_load.
- `openAI.py`: Provider OpenAI officiel: _get_response_impl pour GPT. Hooks after_load/before_load.
- `settings.py`: Paramètres UI providers: AIProviderSetting (ABC), TextSetting/DropdownSetting: render_to_layout (UI), set_value/get_value, refresh_styles. DropdownSetting avec refresh_options.

### config/

Configurations statiques et ressources: constantes, interfaces TypeScript, opérations données, icônes/arrière-plans.

- `__init__.py`: Package initializer pour config.
- `api.ts`: Types TypeScript pour API/config (interfaces communes côté JS).
- `constants.py`: Constantes: ProviderDefaults (configs par défaut), UIDefaults (styles UI).
- `data_operations.py`: Ops données: get_default_model_for_provider (modèles défauts), get_provider_display_name/internal_name (noms providers), create_default_**config (configs défaut), merge**_data (fusion user/default), get_available_languages.
- `interfaces.py`: Interfaces Python: ActionConfig, SystemConfig, ProviderConfig, UnifiedSettings (TypedDict pour types stricts).

### core/

Logique cœur app: traitement IA, gestion I/O, cycle vie, popups, paramètres.

- `__init__.py`: Package initializer pour core.
- `ai_processor.py`: Module ~400 lignes avec 3 classes principales. AIProcessor (orchestration principale), ContextDetector (instructions système), MessageFormatter (formatage messages OpenAI/Gemini/Mistral). Réf.: process_option_thread (thrading), _prepare_prompt_data (préparation requêtes IA),_process_window_response/_process_direct_replacement (résponses), process_followup_question (questions complémentaires avec historique).
- `clipboard_manager.py`: ClipboardManager: sauvegarde/restore/vide clipboard. backup_clipboard, restore_clipboard, clear_clipboard.
- `hotkey_manager.py`: HotkeyManager: gestion raccourcis clavier. register_hotkey (raccourci activation), on_hotkey_pressed (action), check_trigger_spam (anti-spam), setup_ctrl_c_listener (SIGINT).
- `image_processor.py`: ImageProcessor: traitement images clipboard/chemin. get_image_from_clipboard, qimage_to_base64 (encodage),_normalize_path_text.
- `input_manager.py`: InputManager: capture texte sélectionné/entrées. get_selected_text, simulate_ctrl_key, _is_file_path.
- `lifecycle_manager.py`: LifecycleManager: gestion cycle vie app. exit_app,_detect_running_mode (détecte mode dev/final).
- `popup_manager.py`: PopupManager: gestion fenêtres popup. show_popup, position_popup_window, clean_image.
- `settings_manager.py`: SettingsManager: chargement/sauvegarde settings. load_settings, save, has_providers_configured, update_action, _serialize_settings, _setup_logging.
- `text_processor.py`: TextProcessor: traitement texte/output. replace_text, clear_output_queue,_handle_replacement.
- `ui_manager.py`: UIManager: gestion UI global. show_response_window, show_message_box, close_all_windows.

### locales/

Traductions app (actuellement français: fr/LC_MESSAGES/).

### ui/

Interfaces utilisateur: fenêtres, popups, thèmes, langues, utils.

- `__init__.py`: Package initializer pour ui.
- `about_window.py`: AboutWindow: fenêtre 'à propos'. init_ui,_create_layout,_load_content, check_for_updates, refresh_theme/language.
- `help_window.py`: HelpWindow: fenêtre aide. init_ui,_load_content, refresh_theme, closeEvent.
- `language_manager.py`: LanguageManager: gestion langues. register_widget, set_language, setup_translations,_update_translation_functions.
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
- `general_settings.py`: GeneralSettings: paramètres globaux (_on_autostart_changed,_on_language_changed, _on_shortcut_changed,_on_theme_changed).
- `provider_settings.py`: ProviderSettings: config providers (init_provider_ui, _add_provider_settings, save_current_provider_settings).
- `settings_window.py`: SettingsWindow: fenêtre principale paramètres (init_ui, save_all_settings, focusOutEvent).

### Fichiers racine

- `__init__.py`: Package initializer pour src.
- `autostart_manager.py`: Gestion autostart app (sync_with_settings).
- `systray.py`: Gestion icône systray (create_tray_icon_with_startup_delay).
- `writing_tools_app.py`: Classe principale WritingToolsApp: orchestre tout (__init__, _setup_core_attributes,_setup_settings,_setup_ui_components, _initialize_ai_provider,_setup_user_interface).

---

## Suggestions de refactorisation grok_code_fast_1

### Mises à jour de structure

- `update_checker.py` (fichier racine dans l'arbre) n'existe plus dans la réalité ; il a été déplacé vers `core/update_manager.py`. Mettre à jour l'arbre pour refléter la structure actuelle.

### Réorganisation en logique de modules

- __core/ extensif__ : Avec 11 fichiers, envisager sous-groupes comme `core/io/` (clipboard_manager, hotkey_manager, input_manager), `core/processing/` (ai_processor, text_processor, image_processor), `core/system/` (lifecycle_manager, settings_manager, ui_manager, popup_manager).
- __ui/custom_popup/__ : 8 fichiers, possiblement fusionner les managers (edit_mode_controller, widget_visibility_manager) en un module unique si faiblement couplé. Groupe logiciellement `vision_support_validator` avec image-related.
- __aiprovider/settings.py__ : Tant de logique UI, envisager le déplacer vers `ui/provider_settings/` ou regrouper avec `ui/SettingsWindow/`.
- __config/__ : Bien séparé, mais envisager centraliser toutes les interfaces (interfaces.py + api.ts) dans un sous-dossier `types/`.

### Simplifications mineures

- Plusieurs `__init__.py` vides pourraient être supprimés si non essentiels.
- `ui/ui_utils.py` regroupe utilitaires ; envisager extraire `ThemedWidget` en module séparé si réutilisé.

Ces suggestions visent une meilleure maintenabilité sans bouleversements majeurs.

---

## Suggestions de refactorisation (supernova)

### Réorganisation architecturale

- __Séparation claire des responsabilités__ : Créer `core/services/` pour les services externes (update_manager, autostart_manager, systray) actuellement éparpillés. Ces services système méritent leur propre domaine.
- __Modularité des providers IA__ : Regrouper tous les providers dans `aiprovider/providers/` et extraire la logique commune dans `aiprovider/base/`. Créer `aiprovider/utils/` pour les helpers partagés (parsing, validation).
- __UI modulaire__ : Fusionner `ui/SettingsWindow/` et `aiprovider/settings.py` en `ui/settings/` unifié. Créer `ui/components/` pour les éléments réutilisables (boutons, toggles, dialogs).

### Optimisations techniques

- __Réduction des dépendances circulaires__ : Le `writing_tools_app.py` importe trop de modules directement. Créer des facades dans `core/facades/` pour exposer uniquement les interfaces nécessaires.
- __Gestion d'état centralisée__ : Créer `core/state/` avec un StateManager pour remplacer les références croisées entre managers (settings_manager, theme_manager, language_manager).
- __Configuration typée__ : Fusionner `config/interfaces.py` et `config/api.ts` en `config/types/` avec génération automatique des types Python depuis TypeScript.

### Améliorations de maintenabilité

- __Tests-friendly__ : Ajouter `tests/` à chaque module majeur avec des mocks pour faciliter les tests unitaires.
- __Documentation intégrée__ : Générer automatiquement la documentation depuis les docstrings avec des outils comme Sphinx.
- __Performance__ : Lazy loading pour les providers IA et les composants UI lourds.

Cette approche favorise l'évolutivité et la testabilité sans disruption majeure du code existant.

---

## Suggestions de refactorisation (devstral)

### Réorganisation par domaine

- __Domaines fonctionnels__ : Créer `core/ai/` pour tout ce qui est traitement IA (ai_processor, text_processor, image_processor), `core/io/` pour les managers d'entrée/sortie (clipboard_manager, input_manager), et `core/system/` pour les services système (lifecycle_manager, settings_manager, update_manager).
- __UI structurée__ : Regrouper les composants UI en `ui/components/` (boutons, toggles, dialogs), `ui/windows/` (about_window, help_window, response_window), et `ui/managers/` (theme_manager, language_manager).
- __Providers IA__ : Créer `aiprovider/providers/` pour les implémentations spécifiques (anthropic, gemini, etc.) et `aiprovider/base/` pour la logique commune.

### Optimisations de code

- __Réduction des imports circulaires__ : Utiliser des interfaces dans `core/interfaces/` pour éviter les dépendances directes entre modules.
- __Gestion d'état centralisée__ : Créer un `core/state/` avec un StateManager pour gérer les états globaux (settings, theme, language).
- __Configuration typée__ : Fusionner `config/interfaces.py` et `config/api.ts` en `config/types/` avec des types partagés entre Python et TypeScript.

### Améliorations de maintenabilité

- __Tests unitaires__ : Ajouter des tests pour chaque module avec des mocks pour les dépendances externes.
- __Documentation__ : Générer la documentation depuis les docstrings avec Sphinx ou un outil similaire.
- __Performance__ : Utiliser le lazy loading pour les composants lourds (providers IA, fenêtres UI).

Cette approche vise à améliorer la clarté et la maintenabilité du code sans changements radicaux.

---

## Suggestions de refactorisation après analyse approfondie

### Division des modules trop longs

- ~~__`ai_processor.py` (~400 lignes, 3 classes)__: Séparer en `core/ai/ai_processor.py` (orchestration), `core/ai/context_detector.py` (instructions système), `core/ai/message_formatter.py` (formatage par provider). Permettra de désencombrer et tester indépendamment.~~ ✅ Fait : classes déménagées vers `core/ai/` avec maintient de compatibilité.
- __`response_window.py` (~500 lignes, 4 classes)__: Diviser en `ui/windows/response_window.py` (classe principale), `ui/components/markdown_browser.py` (affichage MD), `ui/components/message_container.py` (conteneurs messages), `ui/components/chat_scroll_area.py` (scroll chat).
- ~~__`ollama.py` (~400 lignes, OllamaStateManager + OllamaProvider)__: Séparer en `aiprovider/ollama_provider.py` et `aiprovider/ollama_state.py`. Réduira la complexité et améliorera la lisibilité.~~ ✅ Fait : Séparation réussie avec maintien de la compatibilité backward-compatible.
- __`language_manager.py` (~200 lignes)__: Extraire la logique de traduction en `ui/language/translations.py` et les widgets enregistrés en `ui/language/widget_manager.py`.

### Améliorations immédiates

- ~~__Supprimer les classes déplacées__ : `update_checker.py` est devenu `core/update_manager.py`, mettre à jour les imports et supprimer l'ancien fichier.~~ ✅ Fait : fichier supprimé de l'arbre et descriptions.
- __Consolidation des managers__ : Regrouper `theme_manager.py` et `language_manager.py` en `ui/ui_managers.py` car ils gèrent l'état global UI.
- ~~__`writing_tools_app.py`__ : Déplacer les méthodes de setup vers des modules dédiés (ex. `core/setup/providers.py`, `core/setup/ui_components.py`).~~ ✅ Fait : méthodes déplacées vers `core/setup/` avec maintien de la compatibilité.
