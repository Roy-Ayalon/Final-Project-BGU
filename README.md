# Telegram Meme Classifier Bot

A sophisticated AI-powered Telegram bot that analyzes memes for offensive content and generates alternative versions when needed. The system uses advanced machine learning models for OCR, text classification, and image generation.

## 🏗️ Architecture

This project consists of two main components:

### 1. Telegram Bot (Local Machine)
- **Location**: `src/bot/`
- **Purpose**: Handles user interactions on Telegram
- **Requirements**: Minimal - just needs internet connection

### 2. AI Processing Server (CUDA Machine)
- **Location**: `src/server/`
- **Purpose**: Performs heavy AI computations
- **Requirements**: CUDA-enabled GPU, high RAM

## 🚀 Features

- **🔍 Meme Analysis**: Advanced OCR text extraction from images
- **🚫 Offensive Content Detection**: AI-powered classification using IBM Granite Guardian
- **✨ Alternative Generation**: Creates safer versions using Stable Diffusion
- **🎛️ Creativity Control**: Adjustable temperature settings for generation
- **💬 Interactive UI**: Intuitive Telegram interface with inline keyboards
- **⚡ Real-time Processing**: Fast response times with optimized workflows

## 📋 Prerequisites

### For Bot (Local Machine):
- Python 3.8+
- Internet connection
- Telegram Bot Token

### For Server (CUDA Machine):
- Python 3.8+
- CUDA-enabled GPU (8GB+ VRAM recommended)
- 16GB+ RAM
- 50GB+ storage for models

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone https://github.com/Roy-Ayalon/telegram_bot.git
cd telegram_bot
```

### 2. Set Up Python Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables
```bash
# Copy the template
cp config/.env.template .env

# Edit .env with your actual values
nano .env
```

Required environment variables:
- `TELEGRAM_BOT_TOKEN`: Your bot token from [@BotFather](https://t.me/BotFather)
- `FLASK_SERVER_URL`: URL of your AI processing server
- `HUGGINGFACE_TOKEN`: Token for Hugging Face model access

## 🎯 Usage

### Running the AI Processing Server (CUDA Machine)

```bash
# Navigate to server directory
cd src/server

# Start the Flask server
python app.py
```

The server will start on `http://0.0.0.0:5002` by default.

### Running the Telegram Bot (Local Machine)

```bash
# Navigate to bot directory  
cd src/bot

# Start the Telegram bot
python main.py
```

### Using the Bot

1. **Start**: Send `/start` to the bot
2. **Upload**: Send any meme image
3. **Analysis**: Bot analyzes the meme automatically
4. **Results**: 
   - ✅ **Safe memes**: Returned with approval
   - 🚫 **Offensive memes**: Alternative generated automatically
5. **Feedback**: Approve or reject generated alternatives
6. **Regeneration**: Choose different creativity levels if unsatisfied

## 🔧 Configuration

### Bot Configuration (`src/bot/config.py`)
- Bot token and server URL settings
- File handling preferences
- Webhook configuration for production

### Server Configuration (`src/server/app.py`)
- Model loading and initialization
- Processing pipeline settings
- File size and type restrictions

## 📊 AI Models Used

### 1. OCR: GOT-OCR2.0
- **Purpose**: Text extraction from memes
- **Model**: `ucaslcl/GOT-OCR2_0`
- **Features**: High accuracy, multilingual support

### 2. Classification: IBM Granite Guardian
- **Purpose**: Offensive content detection  
- **Model**: `ibm-granite/granite-guardian-hap-125m`
- **Features**: Hate speech and toxicity detection

### 3. Generation: Stable Diffusion 3
- **Purpose**: Alternative meme generation
- **Model**: `stabilityai/stable-diffusion-3-medium-diffusers`
- **Features**: High-quality image synthesis

## 📁 Project Structure

```
telegram_bot/
├── src/
│   ├── bot/                    # Telegram bot components
│   │   ├── __init__.py
│   │   ├── main.py            # Bot entry point
│   │   ├── config.py          # Configuration settings
│   │   └── handlers.py        # Message and callback handlers
│   └── server/                # AI processing server
│       ├── __init__.py
│       └── app.py             # Flask server with AI models
├── notebooks/                 # Development notebooks
│   ├── classification.ipynb   # Classification model testing
│   ├── meme_generation.ipynb  # Generation model testing
│   ├── main.ipynb            # Main application notebook
│   └── meme_manipulation.ipynb
├── assets/
│   ├── demo/                  # Demo images and videos
│   └── sample_memes/         # Example memes
├── config/
│   └── .env.template         # Environment variables template
├── docs/                     # Additional documentation
├── requirements.txt          # Python dependencies
└── README.md                # This file
```

## 🖼️ Demo

### Bot Interface
![Bot Demo](assets/demo/bot_screenshot.png)

### Processing Workflow
![Workflow](assets/demo/workflow_diagram.png)

### Sample Results
| Original (Offensive) | Generated Alternative |
|---------------------|----------------------|
| ![Original](assets/demo/original_meme.jpg) | ![Alternative](assets/demo/alternative_meme.jpg) |

### Video Demo
🎥 [Watch Full Demo](assets/demo/demo_video.mp4)

## 🔧 Development

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/
```

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run linting
flake8 src/

# Format code
black src/
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📈 Performance

### Processing Times (RTX 4090)
- **OCR Extraction**: ~0.5 seconds
- **Classification**: ~0.3 seconds  
- **Image Generation**: ~3-5 seconds
- **Total Pipeline**: ~4-6 seconds

### Resource Usage
- **VRAM**: 6-8GB during generation
- **RAM**: 8-12GB for model loading
- **Storage**: ~30GB for all models

## 🚀 Deployment

### Production Deployment

#### Option 1: Docker (Recommended)
```bash
# Build and run with Docker Compose
docker-compose up -d
```

#### Option 2: Manual Deployment
```bash
# Set up systemd service for the server
sudo cp deploy/meme-server.service /etc/systemd/system/
sudo systemctl enable meme-server
sudo systemctl start meme-server

# Set up systemd service for the bot
sudo cp deploy/meme-bot.service /etc/systemd/system/
sudo systemctl enable meme-bot
sudo systemctl start meme-bot
```

### Scaling
- Use load balancers for multiple server instances
- Implement Redis for caching processed results
- Set up monitoring with Prometheus/Grafana

## 🛡️ Security

- Bot token should be kept secret
- Server should run behind firewall
- File uploads are validated and sanitized
- Temporary files are cleaned up automatically
- Rate limiting implemented for API endpoints

## 🐛 Troubleshooting

### Common Issues

#### "CUDA out of memory"
- Reduce batch size in model loading
- Use smaller model variants
- Clear GPU cache between requests

#### "Bot not responding"
- Check bot token validity
- Verify server connectivity
- Check firewall settings

#### "Models not loading"
- Verify Hugging Face token
- Check internet connection
- Ensure sufficient disk space

### Logs
```bash
# Bot logs
tail -f logs/bot.log

# Server logs  
tail -f logs/server.log
```

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) for the excellent Telegram API wrapper
- [Hugging Face](https://huggingface.co/) for providing access to state-of-the-art AI models
- [Stability AI](https://stability.ai/) for Stable Diffusion models
- [IBM Research](https://www.ibm.com/research) for the Granite Guardian model

## 📞 Support

For support and questions:
- 📧 Email: [roy.ayalon@example.com](mailto:roy.ayalon@example.com)
- 💬 Telegram: [@your_username](https://t.me/your_username)
- 🐛 Issues: [GitHub Issues](https://github.com/Roy-Ayalon/telegram_bot/issues)

## 🔮 Roadmap

- [ ] Multi-language support
- [ ] Batch processing capabilities
- [ ] Advanced meme templates
- [ ] User preference learning
- [ ] API rate limiting and quotas
- [ ] Web dashboard for analytics
- [ ] Mobile app companion

---

⭐ **Like this project? Give it a star on GitHub!** ⭐