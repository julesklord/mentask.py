"""
Agent Module
============

This module provides the core AgentOrchestrator class for the mentask framework.

The AgentOrchestrator class is a specialized autonomous coding assistant that:
- Orchestrates multi-agent workflows
- Performs code analysis and verification
- Executes tasks autonomously
- Manages git worktrees and subagents
"""

from .orchestrator import AgentOrchestrator

__all__ = ["AgentOrchestrator"]
