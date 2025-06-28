# Epic Task Manager Testing Guidelines

## Table of Contents
1. [Core Principles](#core-principles)
2. [Test Planning Strategy](#test-planning-strategy)
3. [Test Organization](#test-organization)
4. [Fixture Management](#fixture-management)
5. [Parameterized Testing](#parameterized-testing)
6. [Mocking Strategy](#mocking-strategy)
7. [Database Testing](#database-testing)
8. [Test Data Management](#test-data-management)
9. [Error Testing](#error-testing)
10. [Integration Testing](#integration-testing)
11. [Performance Considerations](#performance-considerations)
12. [CI/CD Integration](#cicd-integration)

## Core Principles

### 1. Test Real Code, Mock External Dependencies Only
- **DO**: Use real implementations of internal components
- **DO**: Mock external services (APIs, databases, file systems)
- **DON'T**: Mock internal functions, classes, or modules
- **DON'T**: Mock what you're testing

```python
# GOOD: Mock external dependency
def test_create_project_with_external_api(mocker):
    mocker.patch('epicmanager.services.external_api.notify', return_value=True)

    # Use real service and repository
    project_service = ProjectService(real_repository)
    project = project_service.create_project("Test Project")

    assert project.name == "Test Project"
    assert project.id is not None

# BAD: Mocking internal components
def test_create_project_bad(mocker):
    # DON'T DO THIS - mocking internal logic
    mocker.patch('epicmanager.services.project_service.validate_name')
    mocker.patch('epicmanager.repositories.project_repository.save')
```

### 2. Read Code Before Writing Tests
Before writing any test:
1. **Read the implementation** thoroughly
2. **Identify all code paths** (if/else, try/except)
3. **Note actual enums, constants, and values** used
4. **Understand dependencies** and side effects
5. **Map out edge cases** and error conditions

```python
# STEP 1: Read the actual implementation first
# epicmanager/models/project.py
class ProjectStatus(Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"

# STEP 2: Use the actual values in tests
def test_project_status_transitions():
    # Use actual enum values, not hardcoded strings
    project = Project(name="Test", status=ProjectStatus.ACTIVE)

    project.archive()
    assert project.status == ProjectStatus.ARCHIVED  # NOT "archived"
```

### 3. Test Planning Before Implementation
Always create a test plan before writing tests:

```python
"""
Test Plan for ProjectService.create_project():

HAPPY PATH:
- Create project with valid name
- Create project with description
- Create project with all optional fields
- Verify project ID generation
- Verify created_at timestamp

EDGE CASES:
- Empty name (should fail)
- Name at max length (255 chars)
- Name with special characters
- Duplicate names in same workspace

ERROR SCENARIOS:
- Database connection failure
- Transaction rollback on error
- Concurrent creation attempts

INTEGRATION:
- Project appears in search results
- Project accessible via get_project
- Audit log entry created
"""
```

## Test Organization

### File Structure
```
tests/
├── conftest.py                    # Shared fixtures
├── unit/
│   ├── models/
│   │   ├── conftest.py           # Model-specific fixtures
│   │   ├── test_project.py
│   │   ├── test_feature.py
│   │   └── test_task.py
│   ├── services/
│   │   ├── conftest.py           # Service-specific fixtures
│   │   ├── test_project_service.py
│   │   └── test_task_service.py
│   └── tools/
│       ├── test_project_tools.py
│       └── test_task_tools.py
├── integration/
│   ├── test_project_workflow.py
│   ├── test_task_dependencies.py
│   └── test_template_application.py
└── e2e/
    └── test_full_workflows.py
```

### Class-Based Test Organization
Group related tests under classes for better organization:

```python
import pytest
from epicmanager.models import Project, ProjectStatus
from epicmanager.services import ProjectService

class TestProjectCreation:
    """Tests for project creation functionality."""

    def test_create_project_happy_path(self, project_service):
        """Test creating a project with valid data."""
        project = project_service.create_project(
            name="Test Project",
            description="A test project"
        )

        assert project.id is not None
        assert project.name == "Test Project"
        assert project.description == "A test project"
        assert project.status == ProjectStatus.ACTIVE

    def test_create_project_minimal(self, project_service):
        """Test creating a project with only required fields."""
        project = project_service.create_project(name="Minimal")

        assert project.name == "Minimal"
        assert project.description is None

    @pytest.mark.parametrize(
        "invalid_name,error_type",
        [
            ("", ValueError),
            (None, TypeError),
            ("a" * 256, ValueError),
        ],
        ids=["empty_name", "none_name", "name_too_long"]
    )
    def test_create_project_invalid_name(self, project_service, invalid_name, error_type):
        """Test project creation with invalid names."""
        with pytest.raises(error_type):
            project_service.create_project(name=invalid_name)

class TestProjectUpdate:
    """Tests for project update functionality."""

    def test_update_project_name(self, project_service, sample_project):
        """Test updating project name."""
        updated = project_service.update_project(
            project_id=sample_project.id,
            name="Updated Name"
        )

        assert updated.name == "Updated Name"
        assert updated.id == sample_project.id
```

## Fixture Management

### Fixture Placement Rules
1. **Test file fixtures**: Place at the top of the test file
2. **Shared fixtures**: Place in appropriate `conftest.py`
3. **Scope appropriately**: Use the narrowest scope possible

```python
# At the top of test_project_service.py
import pytest
from datetime import datetime
from epicmanager.models import Project, ProjectStatus
from epicmanager.services import ProjectService

# File-specific fixtures at the top
@pytest.fixture
def project_data():
    """Sample project data for testing."""
    return {
        "name": "Test Project",
        "description": "A test project",
        "start_date": datetime.now(),
        "metadata": {"team": "backend"}
    }

@pytest.fixture
def active_project(project_service):
    """Create an active project for testing."""
    return project_service.create_project(
        name="Active Project",
        status=ProjectStatus.ACTIVE
    )

# In conftest.py for shared fixtures
@pytest.fixture(scope="session")
def db_engine():
    """Database engine for the test session."""
    engine = create_engine("postgresql://test")
    yield engine
    engine.dispose()

@pytest.fixture(scope="function")
def db_session(db_engine):
    """Database session with automatic rollback."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def project_service(db_session):
    """Project service with test database."""
    repo = ProjectRepository(db_session)
    return ProjectService(repo)
```

## Parameterized Testing

### Best Practices for Parameterization
Always use `ids` within the parameterize decorator for clarity:

```python
import pytest
from epicmanager.models import TaskPriority, TaskStatus

class TestTaskPriorityCalculation:
    @pytest.mark.parametrize(
        "priority,urgency,importance,expected_score",
        [
            (TaskPriority.CRITICAL, 10, 10, 100),
            (TaskPriority.HIGH, 8, 7, 56),
            (TaskPriority.MEDIUM, 5, 5, 25),
            (TaskPriority.LOW, 2, 3, 6),
            (TaskPriority.NONE, 0, 0, 0),
        ],
        ids=[
            "critical_max_score",
            "high_priority",
            "medium_priority",
            "low_priority",
            "no_priority"
        ]
    )
    def test_calculate_priority_score(self, priority, urgency, importance, expected_score):
        """Test priority score calculation with various inputs."""
        task = Task(priority=priority, urgency=urgency, importance=importance)
        assert task.calculate_priority_score() == expected_score

    @pytest.mark.parametrize(
        "task_data,expected_status,expected_errors",
        [
            # Happy path cases
            (
                {"name": "Valid Task", "description": "Test"},
                TaskStatus.PENDING,
                None
            ),
            # Edge cases
            (
                {"name": "A" * 255, "tags": ["test"] * 10},
                TaskStatus.PENDING,
                None
            ),
            # Error cases
            (
                {"name": ""},
                None,
                ValueError("Task name cannot be empty")
            ),
            (
                {"name": "Test", "priority": "invalid"},
                None,
                ValueError("Invalid priority value")
            ),
        ],
        ids=[
            "valid_task_minimal",
            "valid_task_edge_case",
            "empty_name_error",
            "invalid_priority_error"
        ]
    )
    def test_task_creation_scenarios(self, task_service, task_data, expected_status, expected_errors):
        """Test task creation with various data combinations."""
        if expected_errors:
            with pytest.raises(type(expected_errors), match=str(expected_errors)):
                task_service.create_task(**task_data)
        else:
            task = task_service.create_task(**task_data)
            assert task.status == expected_status
```

### Complex Parameterization Patterns

```python
# Nested parameterization for comprehensive coverage
@pytest.mark.parametrize("project_status", [
    ProjectStatus.ACTIVE,
    ProjectStatus.ARCHIVED
])
@pytest.mark.parametrize("user_role,can_modify", [
    ("admin", True),
    ("member", True),
    ("viewer", False),
], ids=["admin_user", "member_user", "viewer_user"])
def test_project_permissions(project_service, project_status, user_role, can_modify):
    """Test project modification permissions across statuses and roles."""
    project = create_project_with_status(project_status)
    user = create_user_with_role(user_role)

    if can_modify and project_status == ProjectStatus.ACTIVE:
        result = project_service.update_project(project.id, user, name="Updated")
        assert result.name == "Updated"
    else:
        with pytest.raises(PermissionError):
            project_service.update_project(project.id, user, name="Updated")
```

## Mocking Strategy

### External Dependencies Only
Mock only at system boundaries:

```python
# GOOD: Mocking external services
class TestNotificationService:
    def test_send_task_notification(self, mocker):
        """Test notification sending with mocked email service."""
        # Mock only the external email service
        mock_email = mocker.patch('epicmanager.external.email_client.send')
        mock_email.return_value = {"status": "sent", "id": "123"}

        # Use real notification service
        notification_service = NotificationService()
        task = Task(name="Important Task", assignee="user@example.com")

        result = notification_service.notify_task_assigned(task)

        # Verify the external service was called correctly
        mock_email.assert_called_once_with(
            to="user@example.com",
            subject="Task Assigned: Important Task",
            body=mocker.ANY
        )
        assert result.sent is True

# GOOD: Mocking file system operations
def test_export_project_data(tmp_path, mocker):
    """Test project export with mocked S3 upload."""
    # Mock only the S3 upload
    mock_s3 = mocker.patch('boto3.client')
    mock_upload = mock_s3.return_value.upload_file

    # Use real export service
    export_service = ExportService()
    project = Project(name="Test Project")

    # Export to temporary file (real file operations)
    export_path = tmp_path / "export.json"
    export_service.export_project(project, export_path)

    # Verify file was created
    assert export_path.exists()

    # Upload to S3 (mocked)
    export_service.upload_to_s3(export_path, "bucket/path")
    mock_upload.assert_called_once()
```

### When NOT to Mock

```python
# BAD: Don't mock internal validation
def test_validation_bad(mocker):
    # DON'T DO THIS
    mocker.patch('epicmanager.models.project.validate_name')

# GOOD: Test validation directly
def test_validation_good():
    # Test the actual validation logic
    with pytest.raises(ValueError, match="Project name cannot be empty"):
        Project(name="")
```

## Database Testing

### Transaction-Based Test Isolation

```python
# conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from epicmanager.database import Base

@pytest.fixture(scope="session")
def db_engine():
    """Create database engine for test session."""
    # Use in-memory SQLite for tests
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()

@pytest.fixture(scope="function")
def db_session(db_engine):
    """Provide transactional database session."""
    connection = db_engine.connect()
    transaction = connection.begin()

    # Configure session to use our connection
    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()

    # Make session available to app
    yield session

    # Rollback transaction to ensure test isolation
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(autouse=True)
def clear_database(db_session):
    """Clear all data between tests."""
    # Delete in correct order to respect foreign keys
    for table in reversed(Base.metadata.sorted_tables):
        db_session.execute(table.delete())
    db_session.commit()
```

### Repository Testing Pattern

```python
class TestProjectRepository:
    """Test project repository with real database."""

    def test_create_project(self, db_session):
        """Test creating a project in database."""
        repo = ProjectRepository(db_session)

        project = repo.create(
            name="Test Project",
            description="Testing database operations"
        )

        # Verify in database
        db_session.flush()

        stored = db_session.query(Project).filter_by(id=project.id).first()
        assert stored is not None
        assert stored.name == "Test Project"
        assert stored.created_at is not None

    def test_concurrent_access(self, db_session):
        """Test handling concurrent project access."""
        repo = ProjectRepository(db_session)
        project = repo.create(name="Concurrent Test")

        # Simulate concurrent session
        other_session = Session(bind=db_session.bind)
        other_repo = ProjectRepository(other_session)

        # Both sessions try to update
        repo.update(project.id, name="Update 1")

        with pytest.raises(OptimisticLockError):
            other_repo.update(project.id, name="Update 2")
```

## Test Data Management

### Factory Pattern for Test Data

```python
# tests/factories.py
from datetime import datetime, timedelta
from epicmanager.models import Project, Task, TaskStatus, TaskPriority

class ProjectFactory:
    """Factory for creating test projects."""

    @staticmethod
    def create(
        name: str = "Test Project",
        description: str = None,
        status: ProjectStatus = ProjectStatus.ACTIVE,
        **kwargs
    ) -> Project:
        """Create a project with sensible defaults."""
        return Project(
            name=name,
            description=description or f"Description for {name}",
            status=status,
            created_at=datetime.utcnow(),
            **kwargs
        )

    @staticmethod
    def create_batch(count: int, **kwargs) -> list[Project]:
        """Create multiple projects."""
        return [
            ProjectFactory.create(
                name=f"Project {i}",
                **kwargs
            )
            for i in range(count)
        ]

class TaskBuilder:
    """Builder pattern for complex task creation."""

    def __init__(self):
        self._name = "Test Task"
        self._status = TaskStatus.PENDING
        self._priority = TaskPriority.MEDIUM
        self._dependencies = []
        self._tags = []

    def with_name(self, name: str):
        self._name = name
        return self

    def with_status(self, status: TaskStatus):
        self._status = status
        return self

    def with_dependencies(self, *tasks):
        self._dependencies.extend(tasks)
        return self

    def with_deadline(self, days_from_now: int):
        self._deadline = datetime.utcnow() + timedelta(days=days_from_now)
        return self

    def build(self) -> Task:
        task = Task(
            name=self._name,
            status=self._status,
            priority=self._priority,
            deadline=getattr(self, '_deadline', None)
        )
        for dep in self._dependencies:
            task.add_dependency(dep)
        return task

# Usage in tests
def test_task_with_dependencies(db_session):
    """Test task with complex dependencies."""
    # Use builder for complex setup
    parent_task = TaskBuilder().with_name("Parent Task").build()

    child_task = (TaskBuilder()
        .with_name("Child Task")
        .with_dependencies(parent_task)
        .with_deadline(days_from_now=7)
        .build())

    assert child_task.can_start() is False
    parent_task.complete()
    assert child_task.can_start() is True
```

### Deterministic Test Data

```python
import random
from datetime import datetime
from freezegun import freeze_time

class TestDeterministicData:
    """Ensure deterministic test data generation."""

    @pytest.fixture(autouse=True)
    def fixed_random_seed(self):
        """Fix random seed for deterministic tests."""
        random.seed(42)
        yield
        # Seed is automatically restored after test

    @freeze_time("2024-01-01 12:00:00")
    def test_task_scheduling(self, task_service):
        """Test task scheduling with fixed time."""
        task = task_service.create_task(
            name="Scheduled Task",
            scheduled_for="1 hour from now"
        )

        # Time is frozen, so this is deterministic
        assert task.scheduled_at == datetime(2024, 1, 1, 13, 0, 0)

    def test_random_task_assignment(self, mocker):
        """Test random assignment with controlled randomness."""
        users = ["alice", "bob", "charlie"]

        # Control random.choice to always return first item
        mocker.patch('random.choice', side_effect=lambda x: x[0])

        task = Task(name="Random Assignment")
        task.assign_randomly(users)

        assert task.assignee == "alice"
```

## Error Testing

### Comprehensive Error Scenarios

```python
class TestErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.parametrize(
        "error_condition,expected_exception,expected_message",
        [
            # Validation errors
            (
                {"name": ""},
                ValueError,
                "Project name cannot be empty"
            ),
            (
                {"name": "a" * 256},
                ValueError,
                "Project name exceeds maximum length"
            ),
            # Business logic errors
            (
                {"archive_deleted_project": True},
                InvalidStateError,
                "Cannot archive deleted project"
            ),
            # Database errors
            (
                {"duplicate_name": True},
                IntegrityError,
                "Project with this name already exists"
            ),
        ],
        ids=[
            "empty_name",
            "name_too_long",
            "invalid_state_transition",
            "duplicate_name_constraint"
        ]
    )
    def test_project_creation_errors(
        self,
        project_service,
        error_condition,
        expected_exception,
        expected_message
    ):
        """Test various error conditions in project creation."""
        if "duplicate_name" in error_condition:
            # Create first project
            project_service.create_project(name="Duplicate Test")

        with pytest.raises(expected_exception, match=expected_message):
            if "name" in error_condition:
                project_service.create_project(name=error_condition["name"])
            elif "archive_deleted_project" in error_condition:
                project = project_service.create_project(name="Test")
                project_service.delete_project(project.id)
                project_service.archive_project(project.id)
            elif "duplicate_name" in error_condition:
                project_service.create_project(name="Duplicate Test")
```

### Transaction Rollback Testing

```python
def test_transaction_rollback_on_error(db_session, mocker):
    """Test that transactions roll back on error."""
    project_service = ProjectService(db_session)

    # Mock external service to fail after database write
    mocker.patch(
        'epicmanager.services.audit_service.log_creation',
        side_effect=Exception("Audit service failed")
    )

    initial_count = db_session.query(Project).count()

    with pytest.raises(Exception, match="Audit service failed"):
        project_service.create_project_with_audit(name="Test Project")

    # Verify rollback occurred
    final_count = db_session.query(Project).count()
    assert final_count == initial_count
```

## Integration Testing

### Full Stack Integration Tests

```python
class TestProjectWorkflow:
    """Integration tests for complete project workflows."""

    def test_complete_project_lifecycle(self, app_context):
        """Test full project lifecycle from creation to deletion."""
        # Create project
        project_service = ProjectService()
        project = project_service.create_project(
            name="Integration Test Project",
            description="Testing full workflow"
        )

        # Add features
        feature_service = FeatureService()
        feature1 = feature_service.create_feature(
            project_id=project.id,
            name="User Authentication",
            priority="high"
        )

        # Add tasks to feature
        task_service = TaskService()
        tasks = []
        for i in range(3):
            task = task_service.create_task(
                feature_id=feature1.id,
                name=f"Task {i+1}",
                estimate_hours=8
            )
            tasks.append(task)

        # Create dependencies
        dependency_service = DependencyService()
        dependency_service.create_dependency(
            source_id=tasks[0].id,
            target_id=tasks[1].id
        )

        # Complete tasks in order
        task_service.complete_task(tasks[0].id)
        task_service.complete_task(tasks[1].id)

        # Verify feature progress
        feature = feature_service.get_feature(feature1.id)
        assert feature.progress_percentage == 66.67

        # Archive project
        project_service.archive_project(project.id)

        # Verify cascade effects
        archived_project = project_service.get_project(project.id)
        assert archived_project.status == ProjectStatus.ARCHIVED

        # Verify search doesn't return archived by default
        search_results = project_service.search_projects("Integration")
        assert len(search_results) == 0

        # But can search with include_archived
        search_results = project_service.search_projects(
            "Integration",
            include_archived=True
        )
        assert len(search_results) == 1

    def test_template_application_workflow(self, app_context):
        """Test applying templates to projects."""
        # Create project
        project = ProjectService().create_project(name="Template Test")

        # Apply template
        template_service = TemplateService()
        template_service.apply_template(
            project_id=project.id,
            template_name="technical_approach"
        )

        # Verify structure created
        features = FeatureService().get_features(project_id=project.id)
        assert len(features) == 4  # Technical approach template has 4 sections

        expected_features = [
            "Problem Analysis",
            "Solution Design",
            "Implementation Plan",
            "Testing Strategy"
        ]

        feature_names = [f.name for f in features]
        assert feature_names == expected_features
```

### API Integration Tests

```python
from fastapi.testclient import TestClient

class TestAPIIntegration:
    """Test API endpoints with full stack."""

    def test_project_api_workflow(self, client: TestClient, auth_headers):
        """Test project creation through API."""
        # Create project
        response = client.post(
            "/api/v1/projects",
            json={
                "name": "API Test Project",
                "description": "Created via API"
            },
            headers=auth_headers
        )
        assert response.status_code == 201
        project_id = response.json()["id"]

        # Get project
        response = client.get(
            f"/api/v1/projects/{project_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["name"] == "API Test Project"

        # Update project
        response = client.patch(
            f"/api/v1/projects/{project_id}",
            json={"description": "Updated via API"},
            headers=auth_headers
        )
        assert response.status_code == 200

        # Search projects
        response = client.get(
            "/api/v1/projects/search?q=API",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert len(response.json()["results"]) >= 1
```

## Performance Considerations

### Test Performance Optimization

```python
# Efficient fixture usage
@pytest.fixture(scope="module")
def heavy_test_data():
    """Create expensive test data once per module."""
    # This runs once for all tests in the module
    return generate_large_dataset()

@pytest.fixture(scope="function")
def isolated_test_data(heavy_test_data):
    """Provide isolated copy for each test."""
    # Shallow copy for isolation without recreation
    return heavy_test_data.copy()

# Use pytest-benchmark for performance tests
def test_search_performance(benchmark, large_project_set):
    """Benchmark project search performance."""
    project_service = ProjectService()

    # Benchmark the search operation
    result = benchmark(
        project_service.search_projects,
        query="test",
        limit=100
    )

    assert len(result) <= 100
    assert benchmark.stats["mean"] < 0.1  # Must complete in <100ms
```

### Parallel Test Execution

```python
# pytest.ini
[tool:pytest]
addopts =
    -n auto  # Run tests in parallel
    --strict-markers
    --tb=short

# Mark tests that must run serially
@pytest.mark.serial
def test_database_migration():
    """Test that must run in isolation."""
    pass
```

## CI/CD Integration

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest-check
        name: pytest-check
        entry: pytest
        language: system
        pass_filenames: false
        args: [
          '--tb=short',
          '--quiet',
          '-x',  # Stop on first failure
          'tests/unit'  # Run only unit tests in pre-commit
        ]
```

### GitHub Actions Configuration

```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.11, 3.12]

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        pip install uv
        uv pip sync requirements.txt requirements-dev.txt

    - name: Run tests with coverage
      run: |
        pytest \
          --cov=epicmanager \
          --cov-report=xml \
          --cov-report=term-missing \
          --junitxml=junit/test-results-${{ matrix.python-version }}.xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## Summary Checklist

Before submitting any test:

- [ ] Created comprehensive test plan covering happy path, edge cases, and errors
- [ ] Read actual implementation code to use correct values/enums
- [ ] Fixtures organized at appropriate level (file-specific at top, shared in conftest)
- [ ] Tests grouped logically under classes
- [ ] Parameterized tests use `ids` parameter for clarity
- [ ] Only external dependencies are mocked
- [ ] Database tests use transaction rollback for isolation
- [ ] Error scenarios thoroughly tested with proper assertions
- [ ] Integration tests verify complete workflows
- [ ] No hardcoded values - all constants imported from source
- [ ] Test names clearly describe what is being tested
- [ ] No test interdependencies - each test runs independently

Remember: Tests are documentation. They should clearly show how the system works and what it guarantees.
