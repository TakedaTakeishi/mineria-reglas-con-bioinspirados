#!/usr/bin/env python
"""
MOEA/D ARM Evolution - Modern CLI Entry Point.

Uses Typer for command-line interface with Rich formatting.
Legacy main.py remains for backward compatibility.
"""
from src.cli import app

if __name__ == "__main__":
    app()
