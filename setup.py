"""Setup configuration for AudAgent."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="audagent",
    version="0.1.0",
    author="AudAgent Contributors",
    description="On-the-fly Privacy Auditing for AI Agents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ZhengYeah/AudAgent",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Security",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[],
    extras_require={
        "yaml": ["pyyaml>=6.0"],
        "dev": ["pytest>=7.0", "pytest-cov>=4.0"],
    },
)
