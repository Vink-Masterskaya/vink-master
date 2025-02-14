from setuptools import setup, find_packages

# Читаем содержимое README.md
try:
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()
except FileNotFoundError:
    long_description = "Parser for competitors websites"

# Читаем зависимости из requirements.txt
try:
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]
except FileNotFoundError:
    requirements = [
        "scrapy>=2.11.0",
        "python-dotenv>=1.0.0",
        "python-json-logger>=2.0.7",
        "pandas>=2.2.0",
    ]

setup(
    name="competitors_parser",
    version="1.0.0",
    author="Your Company",
    author_email="your.email@company.com",
    description="Parser for competitors websites",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "run-parser=competitors_parser.scripts.start_parser:main",
        ],
    },
    include_package_data=True,
)
