#!/usr/bin/env python
"""Installation and setup script for Profynex AI.

This script handles:
- Virtual environment setup
- Dependency installation
- Database initialization
- Configuration setup
- Download link generation
"""

import os
import sys
import subprocess
import platform
import shutil
import zipfile
from pathlib import Path
from typing import Optional


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}\n")


def print_success(text: str) -> None:
    """Print success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_info(text: str) -> None:
    """Print info message."""
    print(f"{Colors.BLUE}ℹ {text}{Colors.RESET}")


def print_warning(text: str) -> None:
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")


def print_error(text: str) -> None:
    """Print error message."""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")


def get_python_version() -> str:
    """Get Python version."""
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def check_python_version(required: str = "3.11") -> bool:
    """Check if Python version meets requirements."""
    required_parts = list(map(int, required.split(".")))
    current_parts = [sys.version_info.major, sys.version_info.minor]
    return current_parts >= required_parts[:2]


def get_venv_path() -> Path:
    """Get virtual environment path."""
    return Path.cwd() / "venv"


def get_python_executable() -> Path:
    """Get path to Python executable in venv."""
    venv_path = get_venv_path()
    if platform.system() == "Windows":
        return venv_path / "Scripts" / "python.exe"
    return venv_path / "bin" / "python"


def get_pip_executable() -> Path:
    """Get path to pip executable in venv."""
    venv_path = get_venv_path()
    if platform.system() == "Windows":
        return venv_path / "Scripts" / "pip.exe"
    return venv_path / "bin" / "pip"


def create_virtual_environment() -> bool:
    """Create Python virtual environment."""
    print_info("Creating virtual environment...")
    venv_path = get_venv_path()
    
    if venv_path.exists():
        print_warning(f"Virtual environment already exists at {venv_path}")
        return True
    
    try:
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_path)],
            check=True,
            capture_output=True,
        )
        print_success(f"Virtual environment created at {venv_path}")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to create virtual environment: {e}")
        return False


def upgrade_pip() -> bool:
    """Upgrade pip to latest version."""
    print_info("Upgrading pip...")
    pip_path = get_pip_executable()
    
    try:
        subprocess.run(
            [str(pip_path), "install", "--upgrade", "pip"],
            check=True,
            capture_output=True,
        )
        print_success("Pip upgraded successfully")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to upgrade pip: {e}")
        return False


def install_requirements() -> bool:
    """Install Python dependencies from requirements.txt."""
    print_info("Installing Python dependencies...")
    pip_path = get_pip_executable()
    requirements_file = Path.cwd() / "requirements.txt"
    
    if not requirements_file.exists():
        print_error(f"requirements.txt not found at {requirements_file}")
        return False
    
    try:
        subprocess.run(
            [str(pip_path), "install", "-r", str(requirements_file)],
            check=True,
        )
        print_success("Python dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install dependencies: {e}")
        return False


def setup_directories() -> bool:
    """Create necessary directories."""
    print_info("Setting up directories...")
    
    directories = [
        Path.cwd() / "user_data",
        Path.cwd() / "logs",
        Path.cwd() / "cache",
        Path.cwd() / "models",
    ]
    
    try:
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print_success(f"Created directory: {directory}")
        return True
    except Exception as e:
        print_error(f"Failed to create directories: {e}")
        return False


def setup_environment_file() -> bool:
    """Create .env file from template."""
    print_info("Setting up environment file...")
    
    env_file = Path.cwd() / ".env"
    env_example = Path.cwd() / ".env.example"
    
    if env_file.exists():
        print_warning(".env file already exists")
        return True
    
    if not env_example.exists():
        print_error(".env.example not found")
        return False
    
    try:
        shutil.copy(env_example, env_file)
        print_success(f".env file created from .env.example")
        return True
    except Exception as e:
        print_error(f"Failed to create .env file: {e}")
        return False


def initialize_database() -> bool:
    """Initialize SQLite database."""
    print_info("Initializing database...")
    
    db_path = Path.cwd() / "user_data" / "profynex.db"
    
    if db_path.exists():
        print_warning(f"Database already exists at {db_path}")
        return True
    
    try:
        import sqlite3
        
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                timestamp REAL,
                user_message TEXT,
                ai_response TEXT,
                context TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_profile (
                id TEXT PRIMARY KEY,
                user_id TEXT UNIQUE,
                name TEXT,
                preferences TEXT,
                habits TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                type TEXT,
                timestamp REAL,
                data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory (
                id TEXT PRIMARY KEY,
                key TEXT,
                value TEXT,
                embedding TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        
        print_success(f"Database initialized at {db_path}")
        return True
    except Exception as e:
        print_error(f"Failed to initialize database: {e}")
        return False


def run_tests() -> bool:
    """Run test suite."""
    print_info("Running tests...")
    
    python_path = get_python_executable()
    
    try:
        result = subprocess.run(
            [str(python_path), "-m", "pytest", "tests/test_core_infrastructure.py", "-v"],
            capture_output=True,
            text=True,
        )
        
        if result.returncode == 0:
            print_success("All tests passed")
            # Print test output
            print(result.stdout)
            return True
        else:
            print_warning("Some tests failed")
            print(result.stdout)
            print(result.stderr)
            return False
    except Exception as e:
        print_error(f"Failed to run tests: {e}")
        return False


def create_project_zip(output_dir: Optional[Path] = None) -> Optional[Path]:
    """Create a downloadable ZIP file of the project."""
    print_info("Creating project archive...")
    
    if output_dir is None:
        output_dir = Path.home() / "Downloads"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    zip_path = output_dir / "profynex-ai.zip"
    project_root = Path.cwd()
    
    # Files and directories to include
    include_items = [
        "src/",
        "docs/",
        "tests/",
        "config/",
        "README.md",
        "requirements.txt",
        "package.json",
        "tsconfig.json",
        ".env.example",
        ".gitignore",
        "LICENSE",
        "CONTRIBUTING.md",
        "setup.py",
        "install.py",
    ]
    
    # Directories to exclude
    exclude_dirs = {"venv", "node_modules", ".git", "__pycache__", ".pytest_cache", "build", "dist"}
    
    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for item in include_items:
                item_path = project_root / item
                
                if item_path.is_file():
                    arcname = f"profynex-ai/{item}"
                    zipf.write(item_path, arcname)
                    print_success(f"Added {item}")
                
                elif item_path.is_dir():
                    for file_path in item_path.rglob("*"):
                        # Skip excluded directories
                        if any(part in exclude_dirs for part in file_path.parts):
                            continue
                        if file_path.is_file():
                            rel_path = file_path.relative_to(project_root)
                            arcname = f"profynex-ai/{rel_path}"
                            zipf.write(file_path, arcname)
        
        print_success(f"Project archive created: {zip_path}")
        return zip_path
    except Exception as e:
        print_error(f"Failed to create archive: {e}")
        return None


def print_installation_summary() -> None:
    """Print installation summary and next steps."""
    print_header("Installation Complete")
    
    print(f"{Colors.GREEN}{Colors.BOLD}Profynex AI has been successfully installed!{Colors.RESET}\n")
    
    print(f"{Colors.BOLD}Next Steps:{Colors.RESET}")
    print(f"1. Review the .env file and update configuration if needed")
    print(f"   Location: {Path.cwd() / '.env'}")
    print()
    print(f"2. Activate the virtual environment:")
    if platform.system() == "Windows":
        print(f"   {Colors.YELLOW}venv\\Scripts\\activate{Colors.RESET}")
    else:
        print(f"   {Colors.YELLOW}source venv/bin/activate{Colors.RESET}")
    print()
    print(f"3. Run the development server:")
    print(f"   {Colors.YELLOW}python src/main.py{Colors.RESET}")
    print()
    print(f"4. Access the application:")
    print(f"   {Colors.YELLOW}http://localhost:8000{Colors.RESET}")
    print()
    print(f"5. View the documentation:")
    print(f"   {Colors.YELLOW}docs/CORE_INFRASTRUCTURE_GUIDE.md{Colors.RESET}")
    print()
    print(f"{Colors.BOLD}Useful Commands:{Colors.RESET}")
    print(f"  pytest tests/                   # Run tests")
    print(f"  black src/                      # Format code")
    print(f"  pytest --cov=src/               # Run tests with coverage")
    print()
    print(f"{Colors.BOLD}Project Structure:{Colors.RESET}")
    print(f"  src/core/                       # Core infrastructure")
    print(f"  tests/                          # Test suite")
    print(f"  docs/                           # Documentation")
    print(f"  user_data/                      # User data and database")
    print(f"  logs/                           # Application logs")
    print()
    print(f"{Colors.BOLD}Support:{Colors.RESET}")
    print(f"  Documentation: {Colors.YELLOW}docs/CORE_INFRASTRUCTURE_GUIDE.md{Colors.RESET}")
    print(f"  GitHub: {Colors.YELLOW}https://github.com/Neshley/profynex-ai{Colors.RESET}")
    print()


def main() -> int:
    """Main installation function."""
    print_header("Profynex AI - Installation Setup")
    
    # Check Python version
    print_info(f"Python version: {get_python_version()}")
    if not check_python_version("3.11"):
        print_error("Python 3.11 or higher is required")
        return 1
    print_success("Python version is compatible")
    print()
    
    # Check platform
    print_info(f"Operating System: {platform.system()}")
    print_success(f"Detected {platform.system()} platform")
    print()
    
    # Create virtual environment
    if not create_virtual_environment():
        return 1
    print()
    
    # Upgrade pip
    if not upgrade_pip():
        print_warning("Failed to upgrade pip, continuing anyway...")
    print()
    
    # Install dependencies
    if not install_requirements():
        return 1
    print()
    
    # Setup directories
    if not setup_directories():
        return 1
    print()
    
    # Setup environment file
    if not setup_environment_file():
        print_warning("Failed to setup .env file, continuing anyway...")
    print()
    
    # Initialize database
    if not initialize_database():
        print_warning("Failed to initialize database, continuing anyway...")
    print()
    
    # Run tests
    print_header("Running Tests")
    if not run_tests():
        print_warning("Some tests failed, but installation is complete")
    print()
    
    # Create project ZIP
    print_header("Creating Project Archive")
    zip_path = create_project_zip()
    if zip_path:
        print_info(f"Download your project: {zip_path}")
    print()
    
    # Print summary
    print_installation_summary()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
