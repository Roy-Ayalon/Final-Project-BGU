# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### 1. Prerequisites Check
- ✅ Python 3.8+ installed
- ✅ CUDA GPU available (for server)
- ✅ Telegram bot token ready

### 2. Installation
```bash
git clone https://github.com/Roy-Ayalon/telegram_bot.git
cd telegram_bot
python -m venv venv
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

### 3. Configuration
```bash
cp config/.env.template .env
# Edit .env with your values:
# - TELEGRAM_BOT_TOKEN=your_token_here
# - FLASK_SERVER_URL=http://your_server:5002/upload
# - HUGGINGFACE_TOKEN=your_hf_token
```

### 4. Run the System

#### Start AI Server (CUDA Machine):
```bash
cd src/server
python app.py
```

#### Start Telegram Bot (Local Machine):
```bash
cd src/bot  
python main.py
```

### 5. Test the Bot
1. Open Telegram
2. Find your bot
3. Send `/start`
4. Upload a meme image
5. Get results!

## 🔧 Troubleshooting

### Common Issues:
- **"Module not found"**: Ensure virtual environment is activated
- **"Bot not responding"**: Check bot token and internet connection  
- **"CUDA error"**: Verify GPU availability and drivers
- **"Connection refused"**: Ensure server is running and accessible

### Getting Help:
- 📖 Check the [full README](../README.md)
- 🐛 [Report issues](https://github.com/Roy-Ayalon/telegram_bot/issues)
- 💬 Contact: roy.ayalon@example.com

---
**Next**: Read the [Architecture Guide](architecture.md) to understand the system better.
