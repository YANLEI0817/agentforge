# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-10-11

### Added

- Provider-agnostic core abstractions: `Provider`, `Tool`, `Memory`, `EventBus`, `Agent`, and `Team`.
- Built-in **Mock Provider** so every example and test runs offline with **zero API keys**.
- `OpenAIProvider`, `AnthropicProvider`, and `OllamaProvider` with lazy SDK imports.
- `@tool` decorator that auto-generates JSON Schema from function signatures and docstrings.
- ReAct-style reasoning loop in `Agent` with an observable event trace (AgentLens).
- Supervisor-based multi-agent orchestration in `Team`.
- Command-line interface (`agentforge`) with `mock`/`openai`/`anthropic`/`ollama` providers.
- Three runnable examples: `research_agent`, `coding_team`, and `debate_team`.
- Test suite: 13 core tests plus 8 offline provider tests (fake SDK injection).
- Documentation: `README.md`, `ARCHITECTURE.md`, and `CONTRIBUTING.md`.
- MIT `LICENSE`.
- GitHub Actions CI running the test suite on Python 3.9–3.13.

[Unreleased]: https://github.com/YANLEI0817/agentforge/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/YANLEI0817/agentforge/releases/tag/v0.1.0
