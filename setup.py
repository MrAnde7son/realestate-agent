from setuptools import setup, find_packages

setup(
    name="realestate-agent",
    version="0.1.0",
    description="Real estate data collection and analysis tools",
    author="Your Name",
    packages=find_packages(),
    install_requires=[
        "requests",
        "beautifulsoup4",
        "lxml",
        "pdfplumber",
        "fastmcp",
        "pytest",
        "SQLAlchemy",
        "psycopg2-binary",
        "APScheduler",
        "celery",
        "twilio",
    ],
    python_requires=">=3.8",
)
