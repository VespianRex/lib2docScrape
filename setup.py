from setuptools import setup, find_packages

setup(
    name="lib2docscrape",
    packages=find_packages(),
    install_requires=[
        "beautifulsoup4>=4.12.2",
        "aiohttp>=3.9.1",
        "asyncio>=3.4.3",
        "pydantic>=2.5.2"
    ],
    extras_require={
        "test": [
            "pytest>=7.0.0",
            "pytest-cov>=4.1.0",
            "pytest-html>=4.1.1",
            "pytest-asyncio>=0.24.0",
            "pytest-html-reporter>=0.2.9"
        ]
    }
)
