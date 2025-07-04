# Test Data Directory

This directory contains all test data and temporary files created during test execution.

## Structure

- `.alfred/` - Test Alfred directory structure
  - `tasks/` - Test task files
  - `workspace/` - Test workspace directories  
  - `debug/` - Test debug logs
  - `specs/` - Test specification files
  - `config.json` - Test configuration

## Usage

Tests should use this directory for all file operations instead of the production `.alfred` directory.
This ensures test isolation and prevents interference with actual project data.

## Cleanup

This directory is automatically cleaned up between test runs to ensure test isolation.