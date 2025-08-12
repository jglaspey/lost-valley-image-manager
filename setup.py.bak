from setuptools import setup, find_packages

setup(
    name="google-drive-image-processor",
    version="0.1.0",
    description="Automated batch processing system for Google Drive media files using local AI vision models",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "google-api-python-client>=2.0.0",
        "google-auth-httplib2>=0.1.0",
        "google-auth-oauthlib>=0.5.0",
        "Pillow>=9.0.0",
        "click>=8.0.0",
        "tqdm>=4.60.0",
        "python-dotenv>=0.19.0",
        "requests>=2.25.0",
        "pyyaml>=6.0",
        "pytest>=7.0.0",
        "pytest-cov>=4.0.0",
    ],
    entry_points={
        "console_scripts": [
            "image-processor=image_processor.cli.main:cli",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)