<p align="center">
  <img src="docs/assets/logo.svg" width="120" alt="mentask logo">
</p>

<h1 align="center">mentask</h1>

<p align="center">
  <strong>Universal AI Coding Agent with Multi-Provider Intelligence</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-6366F1?style=for-the-badge" alt="MIT License">
  <img src="https://img.shields.io/badge/Security-Audit_Passed-10B981?style=for-the-badge" alt="Security">
</p>

---

## 🧠 What is mentask?
**mentask** is a professional, modular AI agent designed for advanced coding tasks. It combines multi-provider support (Gemini, etc.) with a robust security model and terminal-native performance.

> *"Thinking in modules, executing with precision."*

## ✨ Key Features
- 🧩 **Modular Intelligence**: Seamlessly switch between models and providers.
- 🛡️ **Zero-Trust File Ops**: Every file modification is validated and backed up.
- 🚀 **Asynchronous Performance**: Smooth TUI experience optimized for Windows/Linux.
- 📂 **Context Management**: Persistent session history with intelligent summarization.
- 🛠️ **Tool-Rich Architecture**: Integrated web search, filesystem tools, and MCP support.

## 🚀 Quick Start
```bash
# Install via pip
pip install mentask

# Launch the dashboard
mentask
```

## 📐 Architecture
```text
[ User Input ] → [ CommandHandler ] → [ SessionManager ]
                                            ↓
[ Provider (Gemini/etc) ] ← [ Tools Registry ] ← [ Security Policy ]
```

## 🛠️ Configuration
Mentask stores its heart in `~/.mentask/`. You can customize your experience in `settings.json`:
- **Theme**: `indigo`, `emerald`, `cyberpunk`, `crimson`.
- **Edit Mode**: `manual` (default) or `auto` (power user).

## 📄 License
This project is licensed under the **MIT License**. See [LICENSE](LICENSE) for details.

---

<p align="center">
  <img src="https://img.shields.io/badge/Made_with_❤️_by-julesklord-6366F1?style=flat-square" alt="Footer">
</p>
