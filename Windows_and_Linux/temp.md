En analysant le code restant, je vois plusieurs opportunités de refactorisation. Voici les plus pertinentes :

## 1. **Hotkey Management** (le plus logique à extraire ensuite)

Créer `core/hotkey_manager.py` pour regrouper :
- `setup_ctrl_c_listener()`
- `start_hotkey_listener()`
- `register_hotkey()`
- `on_hotkey_pressed()` 
- `handle_sigint()`
- `check_trigger_spam()`
- Variables : `hotkey_listener`, `ctrl_c_timer`, `recent_triggers`, etc.

C'est cohérent car tout ce qui touche aux raccourcis clavier forme un ensemble logique.

## 2. **Settings & Configuration Management**

Créer `core/config_manager.py` pour :
- `load_settings()`
- `setup_translations()` et méthodes de traduction
- `change_language()`
- `retranslate_ui()`
- `_detect_running_mode()`
- Gestion des langues et thèmes

## 3. **UI Lifecycle Management**

Créer `core/ui_manager.py` pour :
- `show_onboarding()`
- `on_onboarding_closed()`
- `show_settings()`
- `show_response_window()`
- `show_message_box()` 
- `_show_non_editable_modal()`
- Gestion des fenêtres et modales

## 4. **Text Processing & Clipboard**

Créer `core/text_processor.py` pour :
- `replace_text()`
- `_handle_response_window_output()`
- `_handle_clipboard_paste()`
- Logique de remplacement de texte

**Je recommande de commencer par le HotkeyManager** car :
- C'est un module bien délimité avec des responsabilités claires
- Il a peu de dépendances avec le reste du code
- Il simplifiera significativement la classe principale
- C'est relativement autonome

Veux-tu que je crée le module `HotkeyManager` ?