# Forager Stream

A flexible and extensible information collection system designed to gather, process, and store data from various sources.

## Overview

Forager Stream is a modular Python framework that allows you to collect, process, and manage information from different sources like RSS feeds. It provides both a CLI interface and an API server for interacting with the collected data.

## Features

- **RSS Feed Collection**: Automatically fetch and store articles from RSS feeds
- **API Server**: RESTful API for managing feeds and accessing collected articles
- **Flexible Storage**: SQLite-based storage system with migration support
- **CLI Interface**: Command-line tools for managing inputs and the API server
- **Configurable**: YAML-based configuration for subscriptions and other settings

## Installation

```bash
# Clone the repository
git clone https://github.com/morphychan/forager-stream
cd forager-stream

# Install dependencies
pip install -e .
```

## Usage

### Configure RSS Feeds

Create or edit `config/subscriptions.yaml` with your RSS feed subscriptions:

```yaml
default_interval: 300  # Default polling interval in seconds

feeds:
  - id: news
    name: Tech News
    url: https://example.com/rss
    category: technology
    tags: [tech, news]
    interval: 600  # Override default interval
    enabled: true
```

### CLI Commands

```bash
# Display help
forager --help

# Run or test specific input plugins
forager input --help

# Run the API server
forager api run
```

### API Server

The API server provides endpoints for managing RSS feeds and accessing articles:

- `/feeds/` - Manage RSS feed subscriptions
- `/articles/` - Query and search collected articles

## Development

Forager Stream is built with:

- Python 3.13+
- SQLAlchemy for database operations
- FastAPI for the API server
- Typer for CLI interface
- Alembic for database migrations

## License

MIT 
