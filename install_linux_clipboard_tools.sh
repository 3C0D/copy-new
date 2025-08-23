#!/bin/bash

# Script to install Linux clipboard tools for better image support
# This script installs xclip and xsel which are commonly used clipboard managers on Linux

echo "Installing Linux clipboard tools for better image support..."
echo "=========================================================="

# Detect package manager
if command -v apt-get &> /dev/null; then
    echo "Detected apt package manager (Debian/Ubuntu)"
    PACKAGE_MANAGER="apt-get"
    UPDATE_CMD="apt-get update"
    INSTALL_CMD="apt-get install -y"
elif command -v dnf &> /dev/null; then
    echo "Detected dnf package manager (Fedora/RHEL 8+)"
    PACKAGE_MANAGER="dnf"
    UPDATE_CMD="dnf update -y"
    INSTALL_CMD="dnf install -y"
elif command -v yum &> /dev/null; then
    echo "Detected yum package manager (RHEL/CentOS 7)"
    PACKAGE_MANAGER="yum"
    UPDATE_CMD="yum update -y"
    INSTALL_CMD="yum install -y"
elif command -v pacman &> /dev/null; then
    echo "Detected pacman package manager (Arch Linux)"
    PACKAGE_MANAGER="pacman"
    UPDATE_CMD="pacman -Sy"
    INSTALL_CMD="pacman -S --noconfirm"
elif command -v zypper &> /dev/null; then
    echo "Detected zypper package manager (openSUSE)"
    PACKAGE_MANAGER="zypper"
    UPDATE_CMD="zypper refresh"
    INSTALL_CMD="zypper install -y"
else
    echo "Could not detect package manager. Please install xclip and xsel manually."
    echo "You can usually find them in your distribution's package repository."
    exit 1
fi

# Update package lists
echo "Updating package lists..."
sudo $UPDATE_CMD

# Install xclip (primary clipboard tool)
echo "Installing xclip..."
if sudo $INSTALL_CMD xclip; then
    echo "✓ xclip installed successfully"
else
    echo "✗ Failed to install xclip"
fi

# Install xsel (alternative clipboard tool)
echo "Installing xsel..."
if sudo $INSTALL_CMD xsel; then
    echo "✓ xsel installed successfully"
else
    echo "✗ Failed to install xsel"
fi

# Check if tools are available
echo ""
echo "Checking installed tools..."
echo "=========================="

if command -v xclip &> /dev/null; then
    echo "✓ xclip is available: $(xclip -version 2>&1 | head -n1)"
else
    echo "✗ xclip is not available"
fi

if command -v xsel &> /dev/null; then
    echo "✓ xsel is available: $(xsel --version 2>&1 | head -n1)"
else
    echo "✗ xsel is not available"
fi

# Test clipboard functionality
echo ""
echo "Testing clipboard functionality..."
echo "================================"

# Test xclip
if command -v xclip &> /dev/null; then
    echo "Testing xclip..."
    if xclip -selection clipboard -t TARGETS 2>/dev/null; then
        echo "✓ xclip clipboard access working"
    else
        echo "✗ xclip clipboard access failed"
    fi
fi

# Test xsel
if command -v xsel &> /dev/null; then
    echo "Testing xsel..."
    if xsel --clipboard --type TARGETS 2>/dev/null; then
        echo "✓ xsel clipboard access working"
    else
        echo "✗ xsel clipboard access failed"
    fi
fi

echo ""
echo "Installation complete!"
echo "====================="
echo "These tools will help the application better detect images in your clipboard."
echo ""
echo "If you're still having issues with image detection, you can:"
echo "1. Make sure you're copying images (not just text or URLs)"
echo "2. Try different methods to copy images (right-click > Copy Image)"
echo "3. Check if your desktop environment supports image clipboard"
echo "4. Restart the application after installation"
echo ""
echo "You can test the clipboard functionality by running:"
echo "python3 test_clipboard_image.py"