from setuptools import setup, find_packages

setup(
    name="saas-billing-app",
    version="1.0.0",
    description="A SaaS billing management application built with PyQt6",
    packages=find_packages(),
    install_requires=[
        "PyQt6>=6.6.1",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "saas-billing=src.main:main",
        ],
    },
)
