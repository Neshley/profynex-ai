# Profynex AI - System Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Profynex AI Desktop App                  │
│                    (Tauri + React Frontend)                 │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
    ┌───▼────┐         ┌──────▼──────┐        ┌────▼────┐
    │ 3D     │         │   AI Core    │        │ Desktop │
    │Rendering│         │   Backend    │        │ Control │
    │(WebGL) │         │  (Python)    │        │ (Win API)│
    └────────┘         └──────────────┘        └─────────┘
         │                    │                     │
         ├────────────────────┼─────────────────────┤
         │
    ┌────▼────────────────────────────────────────────┐
    │          Multi-Agent Reasoning Engine           │
    ├────────────────────────────────────────────────┤
    │ ┌─────────┐ ┌─────────┐ ┌─────────┐          │
    │ │Conversa-│ │ Vision  │ │ Memory  │          │
    │ │tion Ag. │ │ Agent   │ │ Agent   │          │
    │ └─────────┘ └─────────┘ └─────────┘          │
    │ ┌─────────┐ ┌─────────┐ ┌─────────┐          │
    │ │Planning │ │Desktop  │ │Browser  │          │
    │ │ Agent   │ │Control  │ │ Agent   │          │
    │ └─────────┘ └─────────┘ └─────────┘          │
    │ ┌─────────┐ ┌─────────┐ ┌─────────┐          │
    │ │Programming│ │Research│ │Calendar │          │
    │ │ Agent   │ │ Agent   │ │ Agent   │          │
    │ └─────────┘ └─────────┘ └─────────┘          │
    └────────────────────────────────────────────────┘
         │
    ┌────▼────────────────────────────────────────────┐
    │              Data & Memory Layer                 │
    ├────────────────────────────────────────────────┤
    │ ┌─────────────┐ ┌──────────────┐              │
    │ │  SQLite DB  │ │  ChromaDB    │              │
    │ │ (Events)    │ │ (Embeddings) │              │
    │ └─────────────┘ └──────────────┘              │
    │ ┌─────────────┐ ┌──────────────┐              │
    │ │  File Cache │ │ Vector Index │              │
    │ └─────────────┘ └──────────────┘              │
    └────────────────────────────────────────────────┘
```

---

## Component Architecture

### 1. Frontend (Tauri + React + Three.js)

**Tauri Backend (Rust)**
- Window management (borderless, always-on-top)
- Event system (WebSocket to Python backend)
- File I/O
- System tray integration
- Hot reload in dev mode

**React Frontend**
- Character viewport (Three.js canvas)
- UI overlays (speech bubbles, panels)
- Settings interface
- Memory/history viewer
- Interaction handlers

**Three.js Character Renderer**
- 3D model loading (glTF/GLB)
- Animation state machine
- Cloth and hair physics
- Real-time lighting
- Emotion state visualization

### 2. AI Core Backend (Python)

**Main Process (FastAPI)**
- REST API for Tauri
- WebSocket for real-time communication
- Event dispatch system
- Configuration management

**Agent Framework**
- Base agent class with tool system
- Agent registry and dispatcher
- Tool execution pipeline
- Error handling and recovery

**Reasoning Engine**
- Context management (conversation history)
- Agent orchestration
- Tool availability checking
- Response generation

### 3. Vision System

**Screen Capture & Analysis**
- Real-time screenshot capture
- YOLOv8 for window/object detection
- Tesseract OCR for text extraction
- Image classification
- Video frame analysis

**Application Understanding**
- Window title parsing
- Active window tracking
- Application-specific handlers
- Code syntax highlighting detection

### 4. Desktop Automation

**Input Emulation**
- pyautogui for mouse/keyboard
- Direct Win32 API calls for advanced operations
- Clipboard management
- File operations (os + pathlib)

**System Monitoring**
- psutil for CPU/RAM/disk
- Registry access (via winreg)
- Service management
- Hardware info

### 5. Memory System

**Relational Database (SQLite)**
```sql
conversations (id, timestamp, user_message, ai_response, context)
events (id, type, timestamp, data)
user_profile (id, name, preferences, habits)
projects (id, name, description, progress)
reminders (id, content, due_date, completed)
```

**Vector Database (ChromaDB)**
- Long-term memory embeddings
- Semantic search
- Context retrieval

**Cache Layer**
- Recent conversation cache
- Application state cache
- File metadata cache

### 6. Voice System

**Speech Recognition**
- OpenAI Whisper (offline)
- Real-time streaming with pyaudio
- Noise filtering
- Language detection

**Text-to-Speech**
- Edge TTS or local models
- Emotion-aware pitch modulation
- Prosody adjustment
- Interruptible playback

### 7. Character Animation State Machine

```
Idle States:
├── Standing Idle
├── Breathing
├── Blinking
├── Thinking (head tilt)
└── Waiting

Interaction States:
├── Listening (head toward screen)
├── Speaking (lip sync + gestures)
├── Excited (celebration animation)
├── Confused (questioning animation)
└── Frustrated (concerned animation)

Transition Logic:
- Based on conversation context
- Voice tone analysis
- User interaction
- Time elapsed in state
```

---

## Data Flow Diagrams

### User Input Flow

```
User speaks → Whisper API → Text parsing → Agent selection
                                                 │
                                        ┌────────┼────────┐
                                        │                 │
                                   Requires         Requires
                                   Vision?          Desktop?
                                        │                 │
                          ┌─────────────▼──┐  ┌──────────▼────┐
                          │ Vision Agent   │  │Desktop Control│
                          │ (Screenshot)   │  │    Agent       │
                          └────────────────┘  └────────────────┘
                                        │                 │
                                   Result ← Merged →  Result
                                        │
                                   Response Generation
                                        │
                                   TTS + Animation
                                        │
                                   Character speaks
```

### Memory Retrieval Flow

```
Context needed → Embedding generated → Vector DB search
                                             │
                                    Similar memories found
                                             │
                                    Ranked by relevance
                                             │
                                    Context injected
                                             │
                                    Response enhanced
```

---

## Agent System

### Base Agent Interface

```python
class Agent(ABC):
    name: str
    description: str
    tools: List[Tool]
    
    async def process(self, context: Context) -> AgentResult
    async def execute_tool(self, tool_name: str, **kwargs)
    def can_handle(self, task: str) -> bool
```

### Agent Types

1. **Conversation Agent** - Natural dialogue, personality, empathy
2. **Vision Agent** - Screen analysis, understanding context
3. **Memory Agent** - Storing and retrieving memories
4. **Planning Agent** - Multi-step task planning
5. **Desktop Control Agent** - System automation
6. **Browser Agent** - Web browsing automation
7. **Programming Agent** - Code analysis and suggestions
8. **Research Agent** - Information gathering
9. **Calendar Agent** - Schedule management
10. **Notification Agent** - Alerts and reminders
11. **Automation Agent** - Workflow orchestration
12. **Trading Agent** - Market data and trading (optional)

---

## Technology Stack Details

### Backend
- **Framework**: FastAPI (async HTTP + WebSocket)
- **Task Queue**: Celery (optional, for heavy processing)
- **Database**: SQLite + ChromaDB
- **Vision**: PyTorch + YOLOv8 + Tesseract
- **NLP**: Transformers + LLaMA (local)
- **Acceleration**: ONNX Runtime + CUDA
- **System Control**: pyautogui + Win32 API

### Frontend
- **Desktop**: Tauri (Rust core)
- **UI**: React 18 + TypeScript
- **3D**: Three.js + Babylon.js
- **Styling**: Tailwind CSS
- **State**: Redux Toolkit
- **Communication**: WebSocket + REST

### DevOps
- **Version Control**: Git
- **CI/CD**: GitHub Actions
- **Packaging**: PyInstaller + Tauri bundler
- **Monitoring**: Custom telemetry (optional)

---

## Performance Considerations

### Optimization Strategies

1. **GPU Acceleration**
   - CUDA for vision models
   - WebGL for 3D rendering
   - ONNX Runtime for inference

2. **Caching**
   - Screenshot cache (only process deltas)
   - Application state cache
   - Memory search cache

3. **Async Processing**
   - Non-blocking I/O
   - Background agent processing
   - Priority-based task queuing

4. **Resource Management**
   - Memory pooling
   - Model quantization
   - Lazy loading of agents

### Target Metrics
- Response latency: < 500ms
- Memory footprint: < 2GB (base) + model size
- GPU VRAM: 4-6GB recommended
- CPU usage (idle): < 5%

---

## Security & Privacy

1. **Local Processing First**
   - Offline models for vision and speech
   - Local memory storage
   - Minimal cloud dependencies

2. **Data Encryption**
   - SQLite encryption (SQLCipher)
   - Vector DB encryption
   - File cache encryption

3. **User Consent**
   - Permission system for actions
   - Confirmation dialogs for destructive operations
   - Privacy mode (disable screen capture)

4. **Audit Trail**
   - All actions logged
   - Reversible operations
   - Manual review capability

---

## Scalability

1. **Multi-Monitor Support**
   - Character can float on any screen
   - Context awareness across monitors

2. **Plugin System**
   - Custom agents
   - Custom tools
   - Custom animations

3. **Team Features (Future)**
   - Multi-user profiles
   - Shared workspaces
   - Collaborative agents

---

## Development Phases

### Phase 1: MVP (4 weeks)
- Basic character rendering
- Voice input/output
- Simple memory system
- Desktop window detection
- Conversation agent only

### Phase 2: Full Featured (8 weeks)
- All agents implemented
- Advanced vision
- Desktop automation
- Emotion visualization
- Advanced animations

### Phase 3: Polish (4 weeks)
- Performance optimization
- Visual polish
- UX refinement
- Testing & debugging
- Documentation

---

For detailed module implementation, see individual component documentation.
