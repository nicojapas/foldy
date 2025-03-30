#!/usr/bin/env python3
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="foldersense",
    version="0.1.0",
    author="FolderSense Team",
    author_email="example@example.com",
    description="A privacy-conscious, AI-driven folder organization tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/foldersense",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Utilities",
        "Topic :: Desktop Environment :: File Managers",
    ],
    python_requires=">=3.6",
    install_requires=[req for req in requirements if not req.startswith('#')],
    entry_points={
        "console_scripts": [
            "foldersense=main:main",
        ],
    },
) 