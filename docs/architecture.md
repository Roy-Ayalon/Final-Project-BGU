# Architecture Overview

## 🏗️ System Design

The Telegram Meme Classifier Bot follows a distributed architecture with clear separation of concerns:

```
┌─────────────────┐    HTTP/REST    ┌──────────────────┐
│                 │ ───────────────► │                  │
│  Telegram Bot   │                 │   AI Server      │
│ (Local Machine) │ ◄─────────────── │ (CUDA Machine)   │
│                 │                 │                  │
└─────────────────┘                 └──────────────────┘
```

## 🔄 Data Flow

### 1. User Interaction
```
User uploads image → Telegram → Bot receives update
```

### 2. Processing Pipeline
```
Bot → Downloads image → Sends to AI Server → Processes through ML models
```

### 3. Response Chain
```
AI Server → Returns results → Bot → Formats response → Sends to user
```

## 🧠 AI Processing Pipeline

### Step 1: OCR Text Extraction
- **Model**: GOT-OCR2.0
- **Input**: Meme image
- **Output**: Extracted text content
- **Time**: ~0.5 seconds

### Step 2: Offensive Content Classification  
- **Model**: IBM Granite Guardian
- **Input**: Extracted text + image features
- **Output**: Offensive/Non-offensive + confidence
- **Time**: ~0.3 seconds

### Step 3: Alternative Generation (if needed)
- **Model**: Stable Diffusion 3
- **Input**: Original image + extracted text + creativity parameters
- **Output**: Alternative meme image
- **Time**: ~3-5 seconds

## 📡 Communication Protocol

### Bot → Server Requests
```json
{
  "endpoint": "/upload",
  "method": "POST",
  "files": {"image": "binary_data"},
  "data": {"temperature": 0.7}
}
```

### Server → Bot Responses

#### Non-Offensive Response:
```json
{
  "status": "Non-Offensive",
  "message": "This meme is safe to use!",
  "explanation": "No offensive content detected",
  "confidence": 0.95
}
```

#### Offensive Response:
```json
{
  "status": "Offensive", 
  "explanation": "Contains hate speech",
  "meme": "/generated/alternative_123.png",
  "question": "Do you like this alternative?",
  "confidence": 0.87
}
```

## 🔧 Component Details

### Telegram Bot (`src/bot/`)

#### Core Components:
- **main.py**: Entry point and application setup
- **handlers.py**: Message and callback handlers
- **config.py**: Configuration management

#### Key Features:
- Async message handling
- File upload/download management
- Interactive inline keyboards
- Error handling and recovery
- Session state management

### AI Processing Server (`src/server/`)

#### Core Components:
- **app.py**: Flask application with AI models

#### Key Features:
- Model loading and initialization
- Multi-step processing pipeline
- File handling and security
- GPU memory management
- Caching and optimization

## 💾 Data Management

### Temporary Files
- User uploads stored temporarily
- Generated images cached briefly
- Automatic cleanup after processing

### Model Storage
- Models cached on first load
- Shared between requests
- GPU memory optimization

### Session Management
- User context preserved across interactions
- State tracking for multi-step workflows
- Cleanup on completion

## 🔒 Security Considerations

### File Handling
- File type validation
- Size restrictions (16MB max)
- Temporary storage only
- Automatic cleanup

### Network Security  
- Input validation and sanitization
- Rate limiting on endpoints
- Secure file serving
- Error message sanitization

### Model Security
- Token-based authentication for model access
- Resource usage monitoring
- Memory leak prevention

## ⚡ Performance Optimizations

### Caching Strategy
- Model weights cached in GPU memory
- Generated images cached temporarily
- Preprocessing results cached

### Resource Management
- GPU memory monitoring
- Automatic cleanup on errors
- Request queue management

### Scalability
- Stateless server design
- Load balancer ready
- Horizontal scaling support

## 🔄 Error Handling

### Bot Error Recovery
- Network timeout handling
- Server unavailability fallbacks
- User-friendly error messages
- Automatic retry logic

### Server Error Management
- GPU memory overflow protection
- Model loading failure recovery
- File processing error handling
- Graceful degradation

## 📊 Monitoring Points

### Key Metrics
- Processing time per request
- GPU utilization
- Memory usage
- Error rates
- User satisfaction (approval rates)

### Health Checks
- `/health` endpoint for server status
- Model loading verification
- GPU availability check
- Disk space monitoring

---

**Next**: Read the [Development Guide](development.md) to contribute to the project.
