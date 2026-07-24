# Installation Guide for Profynex AI

## Quick Start (Automated)

### Option 1: Automated Installation Script

The easiest way to install Profynex AI is using the automated installation script.

#### Requirements
- Python 3.11 or higher
- pip (Python package manager)
- 2GB free disk space minimum
- 4GB RAM recommended

#### Step 1: Download and Extract

1. Download `profynex-ai.zip` from the releases page
2. Extract the ZIP file
3. Open terminal/command prompt in the extracted directory

#### Step 2: Run Installation Script

**On Windows:**
```bash
python install.py
```

**On macOS/Linux:**
```bash
python3 install.py
```

The script will:
- ✓ Check Python version compatibility
- ✓ Create a virtual environment
- ✓ Install all dependencies
- ✓ Set up necessary directories
- ✓ Initialize the database
- ✓ Run tests
- ✓ Generate a downloadable project archive

### Option 2: Manual Installation

If you prefer to install manually:

#### Step 1: Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### Step 2: Upgrade pip

```bash
pip install --upgrade pip
```

#### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

#### Step 4: Set Up Environment

```bash
# Copy environment template
cp .env.example .env

# Create directories
mkdir -p user_data logs cache models
```

#### Step 5: Initialize Database

```bash
python -c "from src.core import *; print('✓ Core module imported successfully')"
```

#### Step 6: Run Tests

```bash
pytest tests/test_core_infrastructure.py -v
```

---

## Configuration

### Environment Variables (.env)

Edit the `.env` file to configure Profynex AI:

```bash
# Application
DEBUG=True
LOG_LEVEL=INFO

# API
API_HOST=127.0.0.1
API_PORT=8000

# AI Models
WHISPER_MODEL=base
LLM_MODEL=gpt-3.5-turbo
VISION_MODEL=yolov8m

# API Keys (get these from respective services)
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here

# Performance
USE_GPU=True
CUDA_DEVICE=0
```

### API Keys

You'll need to set up API keys for:

1. **OpenAI** (for Whisper and GPT models)
   - Get key from: https://platform.openai.com/api-keys
   - Add to `.env`: `OPENAI_API_KEY=sk-...`

2. **Anthropic** (optional, for Claude)
   - Get key from: https://console.anthropic.com
   - Add to `.env`: `ANTHROPIC_API_KEY=...`

---

## Verification

### Test the Installation

```bash
# Activate virtual environment
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

# Run tests
pytest tests/ -v

# Import the core module
python -c "from src.core import EventBus, Container, OperationContext; print('✓ All imports successful')"
```

### Check Project Structure

```
profynex-ai/
├── src/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── exceptions.py
│   │   ├── types.py
│   │   ├── events.py
│   │   ├── container.py
│   │   ├── context.py
│   │   └── health.py
│   └── main.py
├── tests/
│   ├── conftest.py
│   └── test_core_infrastructure.py
├── docs/
│   ├── CORE_INFRASTRUCTURE_GUIDE.md
│   └── ...
├── user_data/
├── logs/
├── venv/
├── .env
├── requirements.txt
├── install.py
└── setup.py
```

---

## Running the Application

### Start the Development Server

```bash
# Activate virtual environment first
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

# Run the server
python src/main.py
```

The server will start at `http://localhost:8000`

### API Health Check

```bash
# In another terminal
curl http://localhost:8000/health

# Response:
# {
#   "status": "healthy",
#   "app": "Profynex AI",
#   "version": "0.1.0"
# }
```

---

## Development Workflow

### Code Formatting

```bash
# Format code with black
black src/ tests/

# Sort imports
isort src/ tests/

# Check code quality
flake8 src/ tests/

# Type checking
mypy src/
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_core_infrastructure.py

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test class
pytest tests/test_core_infrastructure.py::TestEventBus -v

# Run with verbose output
pytest -v

# Run and stop on first failure
pytest -x
```

### View Test Coverage

```bash
# Generate coverage report
pytest --cov=src --cov-report=html

# Open coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

---

## Documentation

### View Documentation

- **Core Infrastructure Guide**: `docs/CORE_INFRASTRUCTURE_GUIDE.md`
- **Architecture**: `docs/ARCHITECTURE.md`
- **Development Roadmap**: `docs/ROADMAP.md`
- **Contributing**: `CONTRIBUTING.md`

---

## Troubleshooting

### Python Version Issues

```bash
# Check Python version
python --version

# Should be 3.11 or higher
# If not, install from https://www.python.org
```

### Virtual Environment Issues

```bash
# Recreate virtual environment
rm -rf venv  # macOS/Linux
rmdir /s venv  # Windows

python -m venv venv
```

### Dependency Issues

```bash
# Reinstall dependencies
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt --force-reinstall
```

### Database Issues

```bash
# Reset database
rm user_data/profynex.db

# Reinitialize
python -c "from src.core import *; print('Database reinitialized')"
```

### Tests Failing

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run tests with verbose output
pytest tests/ -v -s

# Run specific test for debugging
pytest tests/test_core_infrastructure.py::TestEventBus::test_subscribe_to_event -v -s
```

---

## System Requirements

### Minimum Requirements
- Python 3.11+
- 2GB RAM
- 500MB disk space
- Windows 10, macOS 10.14+, or Linux

### Recommended Requirements
- Python 3.12+
- 8GB+ RAM
- 5GB+ disk space
- GPU (NVIDIA RTX 3060+) for ML models
- SSD storage

---

## Updating Profynex AI

### Update Dependencies

```bash
# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# Update pip
pip install --upgrade pip

# Update all dependencies
pip install --upgrade -r requirements.txt
```

### Update Code

```bash
# Pull latest changes
git pull origin main

# Install any new dependencies
pip install -r requirements.txt

# Run migrations/updates
python install.py  # Rerun installation script
```

---

## Getting Help

1. **Check Documentation**: `docs/CORE_INFRASTRUCTURE_GUIDE.md`
2. **Review Examples**: Code examples in documentation
3. **Run Tests**: Tests contain usage examples
4. **GitHub Issues**: https://github.com/Neshley/profynex-ai/issues
5. **Community**: Discussions and support

---

## Next Steps

After installation:

1. Read the [Core Infrastructure Guide](docs/CORE_INFRASTRUCTURE_GUIDE.md)
2. Run the example code in the guide
3. Explore the test suite for usage patterns
4. Start building your first module

---

## License

Profynex AI is licensed under the MIT License. See `LICENSE` file for details.

---

**Happy building! 🚀**
