from setuptools import setup, find_packages

setup(
    name="tabletalk",
    version="0.1.0",
    description="A conversational EDA assistant for exploring data schemas",
    author="TableTalk Team",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.11",
    install_requires=[
        "duckdb>=0.9.0",
        "pandas>=2.0.0",
        "pyarrow>=10.0.0",
        "langchain>=0.1.0",
        "langchain-community>=0.0.20",
        "ollama>=0.1.7",
        "pyyaml>=6.0",
        "click>=8.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "tabletalk=main:main",
        ],
    },
)
