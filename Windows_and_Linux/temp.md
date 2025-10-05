output_ready_signal :  Émis à plusieurs endroits, ça va pas Ou défini à plusieurs endroits ? Je me rappelle plus, mais bon, à revoir




chemin
dans wriing_tools_app.WritingToolsApp.__init__()
self.hotkey_triggered_signal.connect(self.hotkey_manager.on_hotkey_pressed)

dans on_activate() dans hotkey_manager.HotkeyManager
self.app.hotkey_triggered_signal.emit()

dans hotkey_manager.HotkeyManager
on_hotkey_pressed() 
QtCore.QMetaObject.invokeMethod(
            self.app.popup_manager, "show_popup"
            ...
show_popup() dans popup_manager.PopupManager
self.image, selected_text = self._determine_content_source()
self._create_popup_window()
self.popup_window.show()

_create_popup_window() dans popup_manager.PopupManager
self.popup_window = custom_popup_window.CustomPopupWindow(self.app, selected_text, image)

-------------------------
settings window toujours présence ancienne structure provider only... ?
--------------------------
instances de provider