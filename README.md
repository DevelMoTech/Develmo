# Enterprise RAG-Powered Chatbot 🚀

![System Overview]("Back-end/image.png")

A production-ready chatbot solution with Retrieval-Augmented Generation (RAG) capabilities, designed for enterprise environments. Combines React.js frontend, Python backend, and Ollama AI integration for powerful, context-aware conversations.

## ✨ Key Features

- **Intelligent RAG Conversations** - Context-aware responses sourced from your knowledge base
- **Self-Learning Capability** - Stores information via natural language commands (e.g., "remember that our Q4 target is $1.5M")
- **Comprehensive Admin Console** - Full control over knowledge base and system settings
- **Enterprise Security** - JWT authentication with granular role-based permissions
- **Multi-Model AI Support** - Compatible with llama3.2-vision and nomic-embed-text models
- **Scalable Architecture** - Designed for high availability and performance

## 🖥️ System Requirements

### Minimum Specifications
- **Processor**: Intel i7 (9th gen+) or AMD Ryzen 7 3700X
- **Memory**: 16GB DDR4 RAM
- **Graphics**: NVIDIA GPU with 8GB VRAM (GTX 1080 Ti or equivalent)
- **Storage**: 50GB available space (HDD acceptable)
- **OS**: Ubuntu 20.04 LTS / Windows 10 Pro / macOS Monterey (12.0+)

### Recommended Specifications (Production Environment)
- **Processor**: Intel i9-13900K or AMD Ryzen 9 7950X
- **Memory**: 32GB DDR5 RAM
- **Graphics**: NVIDIA RTX 3080 (16GB) or better
- **Storage**: NVMe SSD with 100GB+ available space
- **OS**: Ubuntu 22.04 LTS / Windows 11 Pro / macOS Ventura (13.0+)

> **Note:** For optimal LLM performance, NVIDIA GPUs with CUDA support are strongly recommended.

## 🏗️ System Architecture



The system follows a modular 3-tier architecture:
1. **Frontend**: React.js with Vite.js build system
2. **Backend**: Python FastAPI server
3. **AI Layer**: Ollama with configured LLM models
4. **Database**: SQLite (default) with PostgreSQL support

## 🛠️ Installation Guide

### Prerequisites
- [Ollama](https://ollama.com/) installed and running
- [Python 3.13.3+](https://www.python.org/downloads/)
- [Node.js 18+](https://nodejs.org/)
- [Git](https://git-scm.com/)

### 1. Backend Installation

## Install required AI models
ollama pull nomic-embed-text
ollama pull llama3.2-vision:11b

# Verify installation
ollama list
# Clone repository
git clone https://github.com/your-repo/enterprise-chatbot.git
cd enterprise-chatbot/backend

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
nano .env  # Edit with your settings

# Run backend server
uvicorn app:app --reload --host 0.0.0.0 --port 8000

### 2. Frontend Installation
cd ../frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local
nano .env.local  # Set your API endpoints

# Development mode
npm run dev

# Production build
npm run build
npm run preview

## Admin Dashboard
            Access /admin after setup to:

            Upload/manage knowledge documents (PDF, DOCX, TXT)

            Monitor system performance

            Manage user permissions

            View conversation logs

