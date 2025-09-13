"""
Setup script for the Real Estate API Python client.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="realestate-api",
    version="1.0.0",
    author="Real Estate API Team",
    author_email="team@realestate-api.com",
    description="Python client for the Real Estate API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/realestate-agent",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.25.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-cov>=4.0.0",
            "black>=21.0.0",
            "flake8>=3.8.0",
        ],
    },
)
