from setuptools import setup, find_packages

setup(
    name="aiocvv",
    version="0.0.1",
    description="An asynchronous client for Classeviva written in Python.",
    url="https://github.com/Vinchethescript/aiocvv",
    author="Vinche.zsh",
    author_email="vinchethescript@gmail.com",
    packages=find_packages(),
    install_requires=["aiohttp", "appdirs", "bcrypt"],
    python_requires=">=3.7",
)