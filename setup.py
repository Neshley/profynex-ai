"""Setup configuration for Profynex AI.

This file enables installation via 'pip install -e .'
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = (
    requirements_file.read_text(encoding="utf-8").strip().split("\n")
    if requirements_file.exists()
    else []
)

setup(
    name="profynex-ai",
    version="0.1.0",
    description="Advanced AI Desktop Companion - Holographic Assistant",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Profynex Team",
    url="https://github.com/Neshley/profynex-ai",
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.11",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "pytest-cov>=4.1.0",
            "black>=23.12.0",
            "flake8>=6.1.0",
            "mypy>=1.7.1",
            "isort>=5.13.2",
        ],
    },
    entry_points={
        "console_scripts": [
            "profynex=src.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries",
        "Topic :: Desktop Environment",
    ],
)
