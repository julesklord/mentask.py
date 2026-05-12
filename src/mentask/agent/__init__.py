"""
Agent Module
============

This module provides the core Agent class for the mentask framework.

The Agent class is a specialized autonomous coding assistant that:
- Orchestrates multi-agent workflows
- Performs code analysis and verification
- Executes tasks autonomously
- Manages git worktrees and subagents
"""

from .orchestrator import AgentOrchestrator as Agent

__all__ = ["Agent"]
