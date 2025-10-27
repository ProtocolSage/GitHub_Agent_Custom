"""Setup script for GitHub Assistant."""

from setuptools import setup, find_packages

setup(
    name='github-assistant',
    version='1.0.0',
    description='AI-powered GitHub and Git automation assistant',
    packages=find_packages(),
    install_requires=[
        'PyGithub>=2.5.0',
        'GitPython>=3.1.43',
        'anthropic>=0.39.0',
        'click>=8.1.7',
        'rich>=13.9.4',
        'python-dotenv>=1.0.1',
        'requests>=2.32.3',
        'PyYAML>=6.0.2',
    ],
    entry_points={
        'console_scripts': [
            'gh-assist=github_assistant.cli:cli',
        ],
    },
    python_requires='>=3.8',
)
