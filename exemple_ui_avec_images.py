import base64
import json
import os

from ia_integration.gemini_integration import GeminiIntegration
from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Basic window setup
        self.setWindowTitle("AI Interface")
        self.resize(800, 600)

        # Load API key from config.json
        self.api_key = self._load_api_key()
        if not self.api_key:
            print("API Key not found in config.json. Please ensure it's present.")
            # Handle error or exit gracefully
            return

        # Initialize gemini_client here so model_options are available for setup_ui
        default_model_name = self._load_default_model_name()
        self.gemini_client = GeminiIntegration(self.api_key, default_model_name)

        # Create central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.chat_history = []  # Initialize chat history
        self.current_image_path = None
        self.current_image_base64 = None
        self.setup_ui()

    def _load_api_key(self):
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "config.json"
        )
        if os.path.exists(config_path):
            with open(config_path) as f:
                config = json.load(f)
                return (
                    config.get("providers", {})
                    .get("Gemini (Recommended)", {})
                    .get("api_key")
                )
        return None

    def _load_default_model_name(self):
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "config.json"
        )
        if os.path.exists(config_path):
            with open(config_path) as f:
                config = json.load(f)
                return (
                    config.get("providers", {})
                    .get("Gemini (Recommended)", {})
                    .get("model_name")
                )
        return None

    def setup_ui(self):
        """Initialize all UI components"""
        # Input text area
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("Enter your prompt here...")
        self.input_text.installEventFilter(self)
        self.layout.addWidget(self.input_text)

        # Image selection
        self.image_layout = QHBoxLayout()
        self.layout.addLayout(self.image_layout)

        self.select_image_button = QPushButton("Select Image (or Paste above)")
        self.select_image_button.clicked.connect(self.select_image)
        self.image_layout.addWidget(self.select_image_button)

        self.clear_image_button = QPushButton("Clear Image")
        self.clear_image_button.clicked.connect(self.clear_image)
        self.clear_image_button.setEnabled(False)
        self.clear_image_button.setVisible(False)
        self.image_layout.addWidget(self.clear_image_button)

        self.image_label = QLabel()
        self.image_label.setFixedHeight(150)
        self.image_label.setMaximumWidth(400)
        self.image_label.setStyleSheet("border: 1px solid #ccc; padding: 5px;")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setScaledContents(False)
        self.image_label.setVisible(False)
        self.layout.addWidget(self.image_label)

        # Dropdown for model selection
        self.model_dropdown = QComboBox()
        # Populate dropdown with models from GeminiIntegration
        if self.gemini_client:
            for model_name, details in self.gemini_client.model_options.items():
                display_text = f"{model_name} ({details.get('rpm', 'N/A')} rpm, {details.get('rpd', 'N/A')} rpd)"
                self.model_dropdown.addItem(display_text, model_name)
            # Set the default selected model
            default_index = self.model_dropdown.findData(self.gemini_client.model_name)
            if default_index != -1:
                self.model_dropdown.setCurrentIndex(default_index)
        self.model_dropdown.currentIndexChanged.connect(self.save_model_selection)
        self.layout.addWidget(self.model_dropdown)

        # Buttons layout
        self.buttons_layout = QHBoxLayout()
        self.layout.addLayout(self.buttons_layout)

        # Send button
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_prompt)
        self.buttons_layout.addWidget(self.send_button)

        # Output text area
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setPlaceholderText("AI response will appear here...")
        self.layout.addWidget(self.output_text)

    def send_prompt(self):
        prompt = self.input_text.toPlainText()

        # Require either text or image or both
        if not prompt and not self.current_image_base64:
            self.output_text.setText("Please enter a prompt or select an image.")
            return

        selected_model = self.model_dropdown.currentData()
        if not self.gemini_client or self.gemini_client.model_name != selected_model:
            self.gemini_client = GeminiIntegration(self.api_key, selected_model)

        self.output_text.setText("Generating response...")

        # Prepare the full prompt with image
        full_prompt_content = [prompt] if prompt else []
        if self.current_image_base64:
            full_prompt_content.append(
                {"mime_type": "image/jpeg", "data": self.current_image_base64}
            )
            # Try to detect actual MIME type based on extension
            if self.current_image_path:
                ext = self.current_image_path.lower().split(".")[-1]
                mime_types = {
                    "jpg": "image/jpeg",
                    "jpeg": "image/jpeg",
                    "png": "image/png",
                    "gif": "image/gif",
                    "bmp": "image/bmp",
                }
                mime_type = mime_types.get(ext, "image/jpeg")
                full_prompt_content.append(
                    {"mime_type": mime_type, "data": self.current_image_base64}
                )

        # Add user prompt with image to chat history
        user_content_parts = []
        if prompt:
            user_content_parts.append({"text": prompt})
        if self.current_image_base64:
            mime_type = "image/jpeg"
            if self.current_image_path:
                ext = self.current_image_path.lower().split(".")[-1]
                mime_types = {
                    "jpg": "image/jpeg",
                    "jpeg": "image/jpeg",
                    "png": "image/png",
                    "gif": "image/gif",
                    "bmp": "image/bmp",
                }
                mime_type = mime_types.get(ext, "image/jpeg")
            user_content_parts.append(
                {
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": self.current_image_base64,
                    }
                }
            )

        self.chat_history.append({"role": "user", "parts": user_content_parts})

        response = self.gemini_client.generate_content(
            full_prompt_content, chat_history=self.chat_history
        )
        self.output_text.setText(response)

        # Add AI response to chat history
        self.chat_history.append({"role": "model", "parts": [{"text": response}]})

    def select_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "", "Image Files (*.png *.jpg *.jpeg *.gif *.bmp)"
        )

        if file_path:
            self.current_image_path = file_path
            self.current_image_base64 = self._encode_image_to_base64(file_path)

            # Show preview
            pixmap = QPixmap(file_path)
            scaled_pixmap = pixmap.scaled(
                self.image_label.width(),
                self.image_label.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.image_label.setPixmap(scaled_pixmap)

            # Update UI
            self.select_image_button.setText("Change Image")
            self.clear_image_button.setEnabled(True)
            self.clear_image_button.setVisible(True)
            self.image_label.setVisible(True)

    def clear_image(self):
        """Clear the selected image"""
        self.current_image_path = None
        self.current_image_base64 = None
        self.image_label.clear()
        self.image_label.setVisible(False)

        # Update UI
        self.select_image_button.setText("Select Image")
        self.clear_image_button.setEnabled(False)
        self.clear_image_button.setVisible(False)

    def _encode_image_to_base64(self, image_path):
        """Convert image file to base64 string"""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")
        except Exception as e:
            print(f"Error encoding image: {e}")
            return None

    def eventFilter(self, obj, event):
        """Handle paste events for image pasting with Ctrl+V"""
        if obj == self.input_text and event.type() == QEvent.Type.KeyPress:
            if (
                event.modifiers() == Qt.KeyboardModifier.ControlModifier
                and event.key() == Qt.Key.Key_V
            ):
                # Handle image paste
                clipboard = QApplication.clipboard()
                if clipboard.mimeData().hasImage():
                    pixmap = clipboard.pixmap()
                    if not pixmap.isNull():
                        # Convert QPixmap to QImage and save temporarily
                        image = pixmap.toImage()
                        temp_path = os.path.join(
                            os.path.dirname(os.path.dirname(__file__)),
                            "temp_clipboard.jpg",
                        )
                        image.save(temp_path, "JPG")

                        # Load and set the image
                        self.current_image_path = temp_path
                        self.current_image_base64 = self._encode_image_to_base64(
                            temp_path
                        )
                        self._display_image_from_pixmap(pixmap)
                        self.clear_image_button.setEnabled(True)
                        self.clear_image_button.setVisible(True)
                        self.image_label.setVisible(True)

                        return True  # Event handled
                # If not image, let default paste handler process it

        return super().eventFilter(obj, event)

    def _display_image_from_pixmap(self, pixmap):
        """Display image from QPixmap object"""
        scaled_pixmap = pixmap.scaled(
            self.image_label.width(),
            self.image_label.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.image_label.setPixmap(scaled_pixmap)
        self.select_image_button.setText("Change Image")

    def save_model_selection(self):
        selected_model_text = self.model_dropdown.currentText()
        selected_model_name = selected_model_text.split(" ")[
            0
        ]  # Extract model name from text

        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "config.json"
        )
        if os.path.exists(config_path):
            with open(config_path, "r+") as f:
                config = json.load(f)
                config["providers"]["Gemini (Recommended)"]["model_name"] = (
                    selected_model_name
                )
                f.seek(0)
                json.dump(config, f, indent=4)
                f.truncate()
        else:
            print("config.json not found, cannot save model selection.")
