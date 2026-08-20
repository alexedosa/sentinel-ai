# Sentinel

Sentinel is a personal AI engineering and development intelligence system.

It observes what you're working on, combines your explicit intent with development activity and stored context, and uses an LLM to turn that information into useful engineering intelligence and actionable recommendations.

The long-term goal is simple:

Build a personal senior-engineer-like system that understands what I'm working on, why I'm working on it, and what I should do next — while turning the work itself into useful content.

## Why Sentinel?

When building projects, context gets scattered across:

* GitHub activity
* Project state
* Previous decisions
* Personal notes
* Current intentions

Sentinel brings those signals together.

Instead of treating an LLM as a generic chatbot, Sentinel gives it evidence and context before asking it to reason.

## How It Works

User Request
↓
Context
↓
GitHub Activity + User Signals + Project State
↓
Evidence
↓
LLM Intelligence
↓
Decision Layer
↓
Actionable Intelligence


The important distinction is that the LLM does not become the source of truth.

GitHub activity is stored as actual development evidence.

User statements are stored as user signals.

The LLM interprets those signals rather than treating its interpretation as factual history.


## Current Features

* GitHub activity synchronization
* User intent and signal storage
* Context aggregation
* Evidence filtering
* LLM-powered development analysis
* Intent confidence
* Evidence confidence
* Project confidence
* Alignment detection
* Project resolution
* Project state tracking
* Provider-independent LLM service
* Actionable development recommendations

## Tech Stack

* Python
* Django
* Django REST Framework
* SQLite (development)
* GitHub API
* Groq / OpenAI-compatible LLMs
* python-dotenv

The LLM integration is abstracted behind a service layer so Sentinel is not tightly coupled to a single provider.


## Getting Started

### 1. Clone the repository

git clone <repository-url>
cd sentinel

### 2. Create and activate a virtual environment

python -m venv venv

Windows:

.\venv\Scripts\Activate.ps1

### 3. Install dependencies

pip install -r requirements.txt

### 4. Configure environment variables

Create a .env file:

LLM_PROVIDER=groq
LLM_MODEL=openai/gpt-oss-120b
LLM_API_KEY=your_api_key

GITHUB_TOKEN=your_github_token

### 5. Apply migrations

python manage.py migrate

### 6. Run the server

python manage.py runserver

## Example

A request such as:

"I'm continuing to work on WebSockets."

is not immediately treated as a factual development event.

Sentinel first gathers available evidence.

User Intent
↓
"I'm continuing to work on WebSockets."

GitHub Evidence
↓
Recent repository activity

Stored Context
↓
Previous signals + project state

LLM Analysis
↓
Intent: High
Evidence: Low
Project: Low
Alignment: Insufficient Evidence

Recommendation
↓
Practical next steps for the WebSocket work

This allows Sentinel to distinguish between what the user says, what actually happened, and what the model infers.


## Current Status

Early development / active build.

The core intelligence pipeline is currently being built.

Working components include:

* Context construction
* GitHub synchronization
* User signal persistence
* Evidence construction
* LLM analysis
* Decision finalization
* Project resolution
* Project state synchronization
* LLM provider abstraction

The system is currently focused on building a reliable intelligence foundation before expanding into automated content generation.


## Roadmap

### Intelligence

* Improve project resolution
* Improve evidence relevance
* Track project evolution over time
* Improve confidence scoring
* Detect meaningful changes in development direction


### Engineering Assistant

* Generate development plans from current project state
* Identify useful next actions
* Detect stalled projects
* Surface technical inconsistencies


### Content Engine

Turn genuine development activity into content for platforms such as:

* LinkedIn
* Instagram
* Other build-in-public channels

The content system should be derived from real development evidence rather than fabricated progress.

## Design Philosophy

Evidence before inference.

The system should distinguish facts from interpretations.

Intent is not proof.

A user saying they worked on something does not mean the repository proves they did.

LLMs reason; systems remember.

The application owns persistent state and evidence. The LLM provides interpretation.

Keep the architecture replaceable.

LLM providers should be replaceable without rewriting Sentinel's intelligence layer.

Build for usefulness, not complexity.

Sentinel is intended to be a practical personal engineering system, not an unnecessarily complicated AI framework.


## License

This project is currently for personal development and experimentation.
