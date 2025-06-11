from setuptools import find_packages, setup

setup(
    name="lib2docscrape",
    packages=find_packages(),
    install_requires=[
        "beautifulsoup4>=4.12.2",
        "aiohttp>=3.9.1",
        "asyncio>=3.4.3",
        "pydantic>=2.5.2",
        "markdownify>=0.11.6",
        "bleach>=6.0.0",
        "certifi>=2024.2.2",
        "requests>=2.31.0",
        "tldextract>=3.1.0",
        "scrapy>=2.11.0",
        "duckduckgo-search>=4.4.1",
    ],
    extras_require={
        "test": [
            "pytest>=7.0.0",
            "pytest-cov>=4.1.0",
            "pytest-html>=4.1.1",
            "pytest-asyncio>=0.24.0",
            "pytest-html-reporter>=0.2.9",
            "hypothesis>=6.92.1",
            "scikit-learn>=1.3.0",
            "nltk>=3.8.1",
            "psutil>=5.9.0",
            "jinja2>=3.1.2",
            "bz2file>=0.98",
        ]
    },
)
