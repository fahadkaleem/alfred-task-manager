# Git Guidelines

## 1. Branching
- **Branch Name:** All feature branches must follow the convention `feature/{task_id}`.
- **Base Branch:** All feature branches must be created from the `main` or `master` branch.

## 2. Commits
- **Commit Message Format:** Commit messages must follow the "Conventional Commits" specification.
  - `feat: A new feature`
  - `fix: A bug fix`
  - `docs: Documentation only changes`
  - `style: Changes that do not affect the meaning of the code`
  - `refactor: A code change that neither fixes a bug nor adds a feature`
  - `test: Adding missing tests or correcting existing tests`
- **Atomic Commits:** Each commit should represent a single logical change. Do not bundle unrelated changes into one commit.