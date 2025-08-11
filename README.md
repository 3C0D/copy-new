# ✍️ Writing Tools

A powerful AI-powered writing assistant that integrates seamlessly with your workflow through system tray access and global hotkeys.

## 🚀 Quick Start

### **Run from Source** (Fastest for development)
```bash
python Windows_and_Linux/scripts/dev_script.py
```

### **Build and Test** (Recommended for testing)
```bash
python Windows_and_Linux/scripts/dev_build.py
```

### **Debug Mode** (When things go wrong)
```bash
python Windows_and_Linux/scripts/dev_build.py --console
```

## ✨ Features

- **🤖 Multiple AI Providers**: OpenAI, Gemini, Ollama, Anthropic, Mistral
- **⚡ Global Hotkeys**: Quick access from anywhere
- **🎨 Smart Theming**: Auto dark/light mode detection
- **📋 System Tray**: Unobtrusive background operation
- **🔧 Flexible Configuration**: Per-provider settings and customization
- **🌍 Cross-Platform**: Windows and Linux support

## 🛠️ Development

### **Prerequisites**
- Python 3.8+
- Virtual environment (automatically created)
- Windows 10/11 or Linux

### **Development Workflow**
1. **Quick Testing**: `python Windows_and_Linux/scripts/dev_script.py`
2. **Build Testing**: `python Windows_and_Linux/scripts/dev_build.py`
3. **Debug Issues**: `python Windows_and_Linux/scripts/dev_build.py --console`
4. **Production Build**: `python Windows_and_Linux/scripts/final_build.py`

### **VS Code Integration**
All scripts work perfectly with Code Runner:
1. Open any script file
2. Press `Ctrl+F5`
3. Script runs with proper environment setup

## 🐛 Troubleshooting

### **Systray Icon Missing**
```bash
# Debug startup issues
python Windows_and_Linux/scripts/startup_debug.py

# For boot-time issues
python Windows_and_Linux/scripts/install_startup_debug.py
```

### **Build Failures**
```bash
# Update dependencies first
python Windows_and_Linux/scripts/update_deps.py

# Then try console mode for detailed output
python Windows_and_Linux/scripts/dev_build.py --console
```

### **Provider Issues**
- Check API keys in Settings
- Verify internet connection
- Try different provider in Settings window

## 📚 Documentation

- **[Development Setup](README's%20Linked%20Content/Development%20Strategy%20and%20Setup.md)** - Detailed development guide
- **[Building Guide](README's%20Linked%20Content/To%20Compile%20the%20Application%20Yourself.md)** - Complete build instructions
- **[Running from Source](README's%20Linked%20Content/To%20Run%20Writing%20Tools%20Directly%20from%20the%20Source%20Code.md)** - Source execution guide
- **[Scripts Documentation](Windows_and_Linux/scripts/README.md)** - All available scripts explained
- **[Major Changes](README's%20Linked%20Content/Major%20Changes%20from%20Original%20Fork.md)** - What's new in this version

## 🎯 Usage

1. **Launch** the application using any of the methods above
2. **Configure** your AI provider in the system tray settings
3. **Set up hotkeys** for quick access
4. **Select text** anywhere and use your hotkey
5. **Choose** from predefined prompts or create custom ones
6. **Get AI-powered** writing assistance instantly

## 🔧 Architecture

This version features a complete architectural overhaul with:
- **Multi-mode system** (dev/build-dev/build-final)
- **Robust settings management** with automatic migration
- **Enhanced debugging tools** for development
- **Improved build system** with console mode support
- **Better error handling** and logging

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Use the development scripts for testing
4. Submit a pull request

## 📄 License

[Add your license information here]

## 🙏 Acknowledgments

Based on the original Writing Tools project, enhanced with modern development practices and improved reliability.

---

**Need help?** Check the [troubleshooting section](#-troubleshooting) or review the [documentation](#-documentation) for detailed guides.
