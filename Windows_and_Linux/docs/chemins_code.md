
+++++++++++++++++++++++++++++++++++++++

OPEN RESPONSE WINDOW

# dans CustomPopupWindow.py

def _create_custom_input(...)
    self.custom_input = QLineEdit()
    self.custom_input.returnPressed.connect(self.on_custom_change)


def build_buttons_list(...)
    b.clicked.connect(partial(self.on_generic_instruction, name))
or 
    def _create_custom_input(...)
        self.custom_input.returnPressed.connect(self.on_custom_change)
    or
    def _create_send_button(...)
        send_btn.clicked.connect(self.on_custom_change)    
    

def on_custom_change(...) 
or 
def on_generic_instruction(...)
    self.app.process_option(...)
    self.close()


# dans writingtoolapp.py
def process_option(...)
    if should_setup_response_window:
        self._setup_response_window(...)
        
    def threading.Thread(
            target=self.process_option_thread,
            args=(...),
            daemon=True,
        ).start()
    
    
def process_option_thread(...)
    if should_open_window:
        self._process_window_response(...)
    else:
        self._process_direct_replacement(...)


def _process_window_response(...) # WTA
    self._update_chat_history_if_needed(...)
    self._update_response_window(response)
        
        
        
+++++++++++++++++++++++++++++++++++++++

OPEN NON-EDITABLE MODAL

DEBUG - Selected text: """"Update chat history for custom prompts without text.""""
DEBUG - Creating new popup window ============
Processing option: Custom ← ← process_option()
DEBUG - should_setup_response_window: False
DEBUG - Starting processing thread for option: Custom ← ← process_option_thread()
DEBUG - Getting response for direct replacement ← ← get_response(return_response=True)

Described change: Traduit en français ← ← _handle_text_selected() 
&& logging.info(f"🔥 return_response: {return_response}")
Text: """Update chat history for custom prompts without text."""...


# dans writingtoolapp.py
... same as above

def process_option(...)
    if should_setup_response_window:
        self._setup_response_window(...)
        
    def threading.Thread(
            target=self.process_option_thread,
            args=(...),
            daemon=True,
        ).start()

def process_option_thread(...)
    prompt_data = self._prepare_prompt_data(option, selected_text, custom_change) ← ← BELOW
    if should_open_window:
        self._process_window_response(...)
    else:
        self._process_direct_replacement(...) ← ← THIS

↓ ↓
def _prepare_prompt_data(...)
    if not has_selected_text:
        return self._handle_no_text_selected(...)
    else:
        return self._handle_text_selected(...) ← ← THIS
↓
def _handle_text_selected(...)
    if is_custom_option:
        prompt = f"{prompt_prefix}Described change: {custom_change}\nText: {selected_text}\n "
    else:
        prompt = f"{prompt_prefix}{selected_text}\n "

    return {
        "prompt": prompt,
        "system_instruction": system_instruction,
        "action_config": action_config,
    }

↓ ↓        
def _process_direct_replacement(...)
    self.current_provider.get_response(prompt_data["system_instruction"], prompt_str) ← ← BELOW
    self._logger.debug("Response processed") ← ← ← Fin du processus de remplacement directe
        
# dans aiprovider.py
def get_response(...)
    logging.info(f"🔥 return_response: {return_response}")
    response = self.model.generate_content(contents=contents, stream=False)
    response_text = response.text.rstrip("\n")
    logging.info(f"🔥 Gemini response_text length: {len(response_text)}")
    # Direct replacement
        self.app.output_ready_signal.emit(response_text) ← ← !output_ready_signal!
        logging.info("🔥 Gemini signal emitted, returning empty string") ← ← text remplacement
        return ""

↓ ↓ 
output_ready_signal = Signal(str)
self.output_ready_signal.connect(self.replace_text)

↓ ↓
def replace_text(...)
    if hasattr(self, "current_response_window") and self.current_response_window:
        self._handle_response_window_output(new_text)
    else:
        # Handle other options - try clipboard-based replacement with fallback
        self._handle_clipboard_paste() ← ← THIS

    # Clear output queue if not using response window
    if not hasattr(self, "current_response_window"):
        self.output_queue = ""

↑ ↑
@Slot()
def _show_popup(...)
    if self.image is None:
        selected_text = self.get_selected_text(sleep_duration=0.2) ← ← THIS

    self.popup_window = ui.CustomPopupWindow.CustomPopupWindow(...)

↑ ↑
def on_hotkey_pressed(...)
    # Close existing non-editable modal if open
    # Close existing popup window if open
    # Close existing response window if open

    # Original hotkey handling continues...
    if self.current_provider:
        self._logger.debug("Cancelling current provider's request")
        self.current_provider.cancel()
        self.output_queue = ""

    # noinspection PyTypeChecker
    QtCore.QMetaObject.invokeMethod(
        self, "_show_popup", QtCore.Qt.ConnectionType.QueuedConnection ← ← THIS
    )


    # Ancienne version
    def replace_text(self, new_text: str) -> None:
        self.output_queue += new_text
        current_output = self.output_queue.strip()  # Strip whitespace for comparison

        # For Summary and Key Points, show in response window
        if (
            hasattr(self, "current_response_window")
            and self.current_response_window
        ):
            # Use chat_area.add_message instead of append_text
            if (
                hasattr(self.current_response_window, "chat_area")
                and self.current_response_window.chat_area
            ):
                self.current_response_window.chat_area.add_message(new_text)

            # If this is the initial response, add it to chat history
            if (
                len(self.current_response_window.chat_history) == 1
            ):  # Only original text exists
                self.current_response_window.chat_history.append(
                    {
                        "role": "assistant",
                        "content": self.output_queue.rstrip("\n"),
                    },
                )
        else:
            # For other options, try clipboard-based replacement with fallback
            clipboard_backup = pyperclip.paste()
            cleaned_text = self.output_queue.rstrip("\n")

            # Get current selection before attempting paste
            original_selection = self.get_selected_text(sleep_duration=0.1)

            pyperclip.copy(cleaned_text)

            kbrd = pykeyboard.Controller()

            def press_ctrl_v():
                kbrd.press(pykeyboard.Key.ctrl.value)
                kbrd.press("v")
                kbrd.release("v")
                kbrd.release(pykeyboard.Key.ctrl.value)

            press_ctrl_v()
            time.sleep(0.2)

            # Check if selection changed (indicating successful paste)
            new_selection = self.get_selected_text(sleep_duration=0.1)

            # If selection is the same, paste failed (non-editable page)
            if original_selection == new_selection and original_selection.strip():
                logging.debug(
                    "Paste failed - showing modal window for non-editable page"
                )
                # noinspection PyTypeChecker
                QtCore.QMetaObject.invokeMethod(
                    self,
                    "_show_non_editable_modal",
                    QtCore.Qt.ConnectionType.QueuedConnection,
                    QtCore.Q_ARG(str, cleaned_text),
                )

            pyperclip.copy(clipboard_backup)

        if not hasattr(self, "current_response_window"):
            self.output_queue = ""

