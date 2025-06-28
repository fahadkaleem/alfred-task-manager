# Gemini Codebase Documentation

This document provides a comprehensive overview of the Epic Task Manager codebase, designed to assist Gemini in understanding and interacting with the project.

## 1. Project Overview

**Purpose:** The Epic Task Manager is a command-line tool that orchestrates software development workflows. It guides developers through a structured process, from task initiation to completion, ensuring that each phase of the development lifecycle is properly managed and tracked.

**Key Features:**

- **State Machine:** Utilizes a robust state machine to manage the workflow of each task, ensuring that tasks progress through a predefined set of phases.
- **Task Management:** Allows users to start, resume, and track tasks, with support for different task sources such as Jira, Linear, and local files.
- **Workflow Automation:** Automates various aspects of the development workflow, such as creating task-specific workspaces, managing artifacts, and advancing tasks through different phases.
- **Extensible Architecture:** The project is designed with a modular and extensible architecture, allowing for the addition of new features and integrations.

**Core Technologies:**

- **Python:** The primary programming language used in the project.
- **FastMCP:** A library for building command-line applications, used to create the user interface and expose the project's functionality.
- **Pydantic:** A data validation library used to define the data models and ensure data consistency.
- **Transitions:** A state machine library used to manage the workflow of each task.

## 2. Codebase Structure

The codebase is organized into the following key directories:

- **`src/epic_task_manager`**: The main source code for the project, containing the following subdirectories:
    - **`config`**: Contains the project's configuration settings, including settings for different environments.
    - **`models`**: Defines the Pydantic models used throughout the application to ensure data consistency.
    - **`state`**: Implements the state machine for managing the workflow of each task.
    - **`tools`**: Contains the implementation of the tools that are exposed to the user through the command-line interface.
    - **`prompts`**: Contains the implementation of the prompts that are exposed to the user through the command-line interface.
- **`tests`**: Contains the test suite for the project, with tests for each of the key components.

## 3. Key Files and Modules

The following are some of the key files and modules in the codebase:

- **`main.py`**: The entry point for the command-line application, responsible for initializing the application and executing the user's commands.
- **`src/epic_task_manager/server.py`**: Defines the tools that are available to the user and uses the `fastmcp` library to create a server that exposes these tools.
- **`src/epic_task_manager/state/task_state.py`**: Implements the state machine for managing the workflow of each task, including the different states and transitions.
- **`src/epic_task_manager/tools/epic_tool_provider.py`**: Implements the tools that are exposed to the user through the command-line interface, such as starting a new task, advancing to the next phase, and getting the current status of a task.

## 4. Commands and Usage

The following are some of the key commands that can be used to interact with the Epic Task Manager:

- **`initialize_project`**: Initializes a new Epic Task Manager project, creating the necessary directory structure and configuration files.
- **`begin_or_resume_task`**: Starts a new task, creating a new workspace and initializing the state machine for the task.
- **`submit_for_review`**: Submits the work for the current phase of a task, advancing the task to the next phase in the workflow.
- **`approve_and_advance`**: Advances a task to the next major phase in the workflow, signifying human approval of the current phase's work.
- **`approve_or_request_changes`**: Provides feedback on a submitted artifact during a review step, either approving it or requesting revisions.
- **`get_task_summary`**: Retrieves a summary of a task's current status, including its current state and the status of its artifacts.
- **`inspect_archived_artifact`**: Retrieves the content of an archived artifact for a specific phase of a task.
- **`mark_step_complete`**: Marks a single step as complete during a multi-step phase, such as the coding phase.
- **`get_active_task`**: Retrieves the ID of the currently active task.
- **`implement_next_task_prompt`**: Implements the next task using the Epic Task Manager workflow.

These commands can be executed using the `mcp call` command, followed by the name of the tool and any required parameters. For example, to start a new task with the ID "TEST-123", you would run the following command:

```
mcp call epic-task-manager begin_or_resume_task '{"task_id": "TEST-123"}'
```
