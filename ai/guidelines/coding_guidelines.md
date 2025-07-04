# Epic Task Manager Coding Guidelines

These guidelines ensure our codebase remains clean, readable, and maintainable. They are based on Clean Code principles, Python best practices, and emphasize self-documenting code.

## Core Philosophy

> "The code is the documentation. If you need to explain it, refactor it."

1. **Code should speak for itself** - Write code so clear that anyone can understand what it does without comments
2. **Functions should do one thing** - Each function has a single, clear responsibility
3. **Names reveal intent** - Variable and function names should clearly express their purpose
4. **Be consistent** - Follow established patterns throughout the codebase

## Import Organization

All imports must be at the top of the file, organized in three groups separated by blank lines:

```python
# Standard library imports
import os
import sys
from datetime import datetime
from typing import List, Optional

# Third-party imports
import pytest
from fastmcp import FastMCP
from pydantic import BaseModel
from sqlalchemy import create_engine

# Local application imports
from alfred.models.project import Project
from alfred.services.task_service import TaskService
from alfred.utils.validators import validate_project_name
```

## Variable and Function Naming

### Variables
- Use descriptive names that explain the variable's purpose
- Prefer clarity over brevity
- Use snake_case for all variables

```python
# Bad
n = 5
d = {"name": "John", "age": 30}
temp = calculate_price() * 1.08

# Good
max_retry_attempts = 5
user_profile = {"name": "John", "age": 30}
price_with_tax = calculate_price() * TAX_RATE
```

### Functions
- Function names should be verbs that describe what they do
- Parameters should clearly indicate expected types
- Return types should be explicit

```python
# Bad
def process(data):
    return data * 2

def check(email):
    return "@" in email

# Good
def calculate_total_price(base_price: float, tax_rate: float) -> float:
    return base_price * (1 + tax_rate)

def is_valid_email_address(email: str) -> bool:
    return "@" in email and "." in email.split("@")[1]
```

### Classes
- Use CapWords (PascalCase) for class names
- Class names should be nouns
- Avoid generic names like Manager, Handler unless truly generic

```python
# Bad
class data_processor:
    pass

class Manager:
    pass

# Good
class ProjectRepository:
    pass

class TaskDependencyValidator:
    pass
```

## Constants

- Use UPPER_SNAKE_CASE for constants
- Group related constants together
- Define at module level, not inside functions

```python
# Bad
def calculate_price():
    discount = 0.1
    max_discount = 0.5
    return price * (1 - discount)

# Good
DEFAULT_DISCOUNT_RATE = 0.1
MAX_DISCOUNT_RATE = 0.5
MIN_ORDER_AMOUNT = 10.0

def calculate_discounted_price(price: float, discount_rate: float = DEFAULT_DISCOUNT_RATE) -> float:
    effective_discount = min(discount_rate, MAX_DISCOUNT_RATE)
    return price * (1 - effective_discount)
```

## Comments Philosophy

### When NOT to Comment
- Never explain WHAT the code does - the code should be clear enough
- Don't comment obvious operations
- Don't use comments to explain bad variable names - rename them instead

```python
# Bad
# Increment counter by 1
counter += 1

# Get user by id
user = get_user(user_id)

# Check if list is empty
if len(items) == 0:
    pass

# Good (no comments needed)
counter += 1

user = get_user_by_id(user_id)

if not items:
    pass
```

### When TO Comment
- Explain WHY when the business logic is not obvious
- Document workarounds or temporary solutions
- Clarify complex algorithms or mathematical formulas

```python
# Good comments
import time
from typing import List, Optional
from alfred.models.user import User

MAX_RETRY_ATTEMPTS = 3

# We need to retry 3 times due to external API rate limiting
for attempt in range(MAX_RETRY_ATTEMPTS):
    response = call_external_api()
    # 429 = Too Many Requests
    if response.status_code != 429:
        break
    # Exponential backoff
    time.sleep(2 ** attempt)

# Using binary search since dataset is pre-sorted and can be very large (>1M records)
def find_user_in_sorted_list(users: List[User], target_id: int) -> Optional[User]:
    left, right = 0, len(users) - 1
    # ... binary search implementation
```

### NEVER Use Inline Comments
Comments must NEVER appear on the same line as code. Always place comments on their own line above the code they describe:

```python
# Bad - NEVER do this
user_count += 1  # increment user count
status = "active"  # set default status

# Good
# Track active users
user_count += 1

# Default status for new users
status = "active"
```

## Function Design

### Size and Complexity
- Functions should be small (ideally < 10 lines)
- Functions should do ONE thing
- Extract complex conditions into well-named functions

```python
# Bad
def process_order(order):
    if order.status == "pending" and order.payment_verified and order.items:
        for item in order.items:
            if item.quantity > 0 and item.in_stock:
                item.reserve()
                order.total += item.price * item.quantity
        if order.total > 100:
            order.discount = 0.1
        order.status = "confirmed"
        send_email(order.customer.email)
        update_inventory()
        log_transaction()

# Good
from alfred.models.order import Order, OrderStatus

BULK_DISCOUNT_RATE = 0.1

def process_order(order: Order) -> None:
    if not can_process_order(order):
        return

    reserve_order_items(order)
    apply_order_discounts(order)
    finalize_order(order)

def can_process_order(order: Order) -> bool:
    return (order.status == OrderStatus.PENDING
            and order.payment_verified
            and order.has_items())

def reserve_order_items(order: Order) -> None:
    for item in order.get_available_items():
        item.reserve()
        order.add_to_total(item.price * item.quantity)

def apply_order_discounts(order: Order) -> None:
    if order.qualifies_for_bulk_discount():
        order.apply_discount(BULK_DISCOUNT_RATE)

def finalize_order(order: Order) -> None:
    """Complete order processing with confirmation and notifications."""
    order.status = OrderStatus.CONFIRMED
    # Additional finalization logic here
```

### Parameters
- Limit function parameters (ideally ≤ 3)
- Use data classes or dictionaries for related parameters
- Avoid boolean flags - use separate functions instead

```python
# Bad
def create_user(name, email, age, address, phone, is_admin, send_welcome_email):
    pass

def format_date(date, use_long_format):
    if use_long_format:
        return date.strftime("%B %d, %Y")
    return date.strftime("%m/%d/%Y")

# Good
from dataclasses import dataclass

@dataclass
class CreateUserRequest:
    name: str
    email: str
    age: int
    address: str
    phone: str
    is_admin: bool = False

def create_user(request: CreateUserRequest) -> 'User':
    pass

def format_date_short(date: datetime) -> str:
    return date.strftime("%m/%d/%Y")

def format_date_long(date: datetime) -> str:
    return date.strftime("%B %d, %Y")
```

## Error Handling

- Use specific exceptions, not generic ones
- Fail fast and fail clearly
- Provide context in error messages

```python
# Bad
def get_user(user_id):
    try:
        return database.query(f"SELECT * FROM users WHERE id = {user_id}")
    except:
        return None

# Good
from alfred.models.user import User
from alfred.exceptions import DatabaseConnectionError, ServiceUnavailableError, UserNotFoundError

def get_user_by_id(user_id: int) -> User:
    if not isinstance(user_id, int) or user_id <= 0:
        raise ValueError(f"Invalid user_id: {user_id}. Must be a positive integer.")

    try:
        return database.query_user(user_id)
    except DatabaseConnectionError as e:
        raise ServiceUnavailableError(f"Cannot retrieve user {user_id}: Database unavailable") from e
    except UserNotFoundError:
        raise ValueError(f"User with id {user_id} does not exist")
```

## Type Hints

Always use type hints for function parameters and return values. For forward references, you can either use quotes or import annotations from `__future__` - both approaches are acceptable:

```python
from typing import List, Optional, Dict, Union, Tuple, Generator
from alfred.models.task import Task, TaskStatus

def find_tasks_by_status(
    status: TaskStatus,
    project_id: Optional[int] = None,
    limit: int = 100
) -> List[Task]:
    pass

def parse_configuration(
    config_data: Dict[str, Union[str, int, bool]]
) -> Tuple['Config', List[str]]:
    """Parse configuration data and return a Config object with validation errors."""
    pass

# Option 1: Use quotes for forward references
from typing import Generic, TypeVar

TResult = TypeVar('TResult')

class RepositoryResult(Generic[TResult]):
    def __init__(self, data: TResult):
        self.data = data
    
    @classmethod
    def success(cls, data: TResult) -> 'RepositoryResult[TResult]':
        return cls(data=data)

# Option 2: Use future annotations (if you prefer cleaner syntax)
from __future__ import annotations
from typing import Generic, TypeVar

TResult = TypeVar('TResult')

class RepositoryResult(Generic[TResult]):
    def __init__(self, data: TResult):
        self.data = data
    
    @classmethod
    def success(cls, data: TResult) -> RepositoryResult[TResult]:  # No quotes needed
        return cls(data=data)
```

### Type Hint Best Practices

1. **Handle forward references (choose either approach)**:
```python
# Option 1: Use quotes when needed
def create_user(self) -> 'UserRepository':
    pass

# Option 2: Use future annotations for cleaner syntax
from __future__ import annotations

def create_user(self) -> UserRepository:  # No quotes needed
    pass
```

Both approaches are valid. Choose based on your preference and consistency within a module.

2. **Use specific types over generic ones**:
```python
# Bad
def process_data(data: list) -> dict:
    pass

# Good
def process_user_profiles(profiles: List['UserProfile']) -> Dict[str, 'ValidationResult']:
    pass
```

3. **Use Union types for multiple possible types**:
```python
from typing import Union

def handle_response(response: Union['SuccessResponse', 'ErrorResponse']) -> 'ProcessingResult':
    pass
```

## Pydantic Models

Use Pydantic for all data validation and serialization. Pydantic models provide automatic validation, serialization, and clear documentation:

```python
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime
from typing import Optional, List
from enum import Enum

class TaskPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class CreateTaskRequest(BaseModel):
    model_config = ConfigDict(
        use_enum_values=True,
        json_schema_extra={
            "example": {
                "title": "Implement user authentication",
                "description": "Add JWT-based authentication to the API",
                "priority": "high",
                "assigned_to": 42
            }
        }
    )
    
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None
    assigned_to: Optional[int] = Field(None, gt=0)
    tags: List[str] = Field(default_factory=list, max_items=10)

    @field_validator('due_date')
    @classmethod
    def due_date_must_be_future(cls, value):
        if value and value < datetime.now():
            raise ValueError('Due date must be in the future')
        return value
```

### Pydantic Best Practices

1. **Use Field() for validation and documentation**:
```python
from decimal import Decimal
from pydantic import Field, BaseModel

class User(BaseModel):
    age: int = Field(..., ge=0, le=150, description="User's age in years")
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    balance: Decimal = Field(..., decimal_places=2, ge=Decimal('0'))
```

2. **Prefer Pydantic models over dictionaries**:
```python
# Bad
def create_project(data: dict) -> dict:
    if "name" not in data:
        raise ValueError("Name is required")
    return {"id": 1, "name": data["name"]}

# Good
class CreateProjectRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None

class ProjectResponse(BaseModel):
    id: int
    name: str
    created_at: datetime

def create_project(request: CreateProjectRequest) -> ProjectResponse:
    return ProjectResponse(
        id=1,
        name=request.name,
        created_at=datetime.now()
    )
```

## Enums

Use Enums for all constant sets of values. This provides type safety and prevents invalid values:

```python
from enum import Enum, auto

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Permission(Enum):
    READ = auto()
    WRITE = auto()
    DELETE = auto()
    ADMIN = auto()

# Usage
def update_task_status(task_id: int, status: TaskStatus) -> None:
    # Type checker ensures only valid statuses are passed
    pass

# String enums for JSON serialization
task_status = TaskStatus.PENDING
print(task_status.value)  # "pending"

# Integer enums for internal use
permission = Permission.ADMIN
print(permission.value)  # 4
```

### Enum Best Practices

1. **Use string enums for API/external interfaces**:
```python
class OrderStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
```

2. **Group related constants into enums**:
```python
# Bad
TASK_PRIORITY_LOW = 1
TASK_PRIORITY_MEDIUM = 2
TASK_PRIORITY_HIGH = 3
TASK_PRIORITY_CRITICAL = 4

# Good
class TaskPriority(int, Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

    @property
    def is_urgent(self) -> bool:
        return self.value >= TaskPriority.HIGH.value
```

3. **Use enums with Pydantic models**:
```python
class Task(BaseModel):
    title: str
    status: TaskStatus
    priority: TaskPriority

    @field_validator('status', mode='before')
    @classmethod
    def validate_status(cls, value):
        if isinstance(value, str):
            return TaskStatus(value)
        return value
```

## Class Design

### Single Responsibility
Each class should have one reason to change:

```python
# Bad
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email

    def save_to_database(self):
        # Database logic
        pass

    def send_email(self, message):
        # Email logic
        pass

    def validate_password(self, password):
        # Validation logic
        pass

# Good
class User:
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email

class UserRepository:
    def save(self, user: User) -> None:
        pass

class EmailService:
    def send_to_user(self, user: User, message: str) -> None:
        pass

class PasswordValidator:
    def is_valid(self, password: str) -> bool:
        pass
```

## Testing

- Test function names should clearly describe what they test
- Use descriptive assertion messages
- Follow Arrange-Act-Assert pattern

```python
# Bad
def test_user():
    u = User("John", "john@example.com")
    assert u.name == "John"

# Good
from alfred.models.user import User

def test_user_creation_with_valid_data_sets_correct_attributes():
    # Arrange
    expected_name = "John Doe"
    expected_email = "john.doe@example.com"

    # Act
    user = User(name=expected_name, email=expected_email)

    # Assert
    assert user.name == expected_name, f"Expected name to be {expected_name}, got {user.name}"
    assert user.email == expected_email, f"Expected email to be {expected_email}, got {user.email}"
```

## SQLAlchemy and Database Best Practices

### Modern SQLAlchemy with Mapped Types

**ALWAYS use `Mapped` type annotations** for SQLAlchemy ORM models to ensure proper type checking and avoid `# type: ignore` workarounds:

```python
from sqlalchemy import String, Integer, ForeignKey, Enum, Column
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import Optional, List
from enum import Enum as PyEnum

class ProjectStatus(str, PyEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    PLANNING = "planning"

class Base(DeclarativeBase):
    pass

# Good - Modern SQLAlchemy with proper typing
class ProjectORM(Base):
    __tablename__ = "projects"

    # Use Mapped[] for all columns - this tells mypy the actual runtime type
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(Enum(ProjectStatus), nullable=False)

    # Relationships also use Mapped[]
    features: Mapped[List['FeatureORM']] = relationship("FeatureORM", back_populates="project")

# Bad - Old style without proper typing
class ProjectORM(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)  # mypy doesn't know this is int at runtime
    name = Column(String(255), nullable=False)  # mypy thinks this is Column[str]

    features = relationship("FeatureORM")  # No type information
```

### Repository Pattern with Proper Typing

```python
from typing import Optional, List
from sqlalchemy.orm import Session
from alfred.models.project import Project  # Domain model

class ProjectRepository:
    def __init__(self, session: Session):
        self.session = session

    def find_by_id(self, project_id: int) -> Optional[Project]:
        orm_project = self.session.query(ProjectORM).filter_by(id=project_id).first()
        return self._to_domain_model(orm_project) if orm_project else None

    def find_active_projects(self) -> List[Project]:
        orm_projects = self.session.query(ProjectORM).filter_by(status=ProjectStatus.ACTIVE).all()
        return [self._to_domain_model(p) for p in orm_projects]

    def save(self, project: Project) -> Project:
        orm_project = self._to_orm_model(project)
        self.session.add(orm_project)
        self.session.commit()
        return self._to_domain_model(orm_project)
    
    def _to_domain_model(self, orm_project: ProjectORM) -> Project:
        # Convert ORM model to domain model
        return Project(
            id=orm_project.id,
            name=orm_project.name,
            description=orm_project.description,
            status=orm_project.status
        )
    
    def _to_orm_model(self, project: Project) -> ProjectORM:
        # Convert domain model to ORM model
        return ProjectORM(
            id=project.id,
            name=project.name,
            description=project.description,
            status=project.status
        )
```

### Type Checking Philosophy

**Priority Order for Fixing Type Issues:**

1. **Fix the root cause** - Use proper types (like `Mapped[]`) that accurately represent runtime behavior
2. **Refactor the code** - Change the implementation to be more type-friendly
3. **Use specific type ignores** - Only as a last resort, and document why
4. **Never use blanket ignores** - Avoid `# type: ignore` without specific error codes

```python
# Best - Fix the root cause with proper typing
class UserORM(Base):
    name: Mapped[str] = mapped_column(String(100))  # mypy knows this is str

# Good - Specific type ignore with explanation
def legacy_function() -> Any:  # type: ignore[misc]
    # TODO: Remove this when legacy API is updated
    return complex_legacy_system()

# Bad - Hiding type issues instead of fixing them
def convert_orm_to_model(orm_entity):  # type: ignore
    return SomeModel(name=orm_entity.name)  # type: ignore
```

### Database Migration Best Practices

```python
# Always use Alembic for schema changes
# Create migration: alembic revision --autogenerate -m "description"
# Apply migration: alembic upgrade head

# In migration files, be explicit about changes
def upgrade() -> None:
    op.add_column('projects', sa.Column('status', sa.Enum('active', 'archived'), nullable=False))

def downgrade() -> None:
    op.drop_column('projects', 'status')
```

## Specific Python Best Practices

### List Comprehensions
Use comprehensions when they improve readability:

```python
# Good for simple transformations
active_user_names = [user.name for user in users if user.is_active]

# Bad - too complex for comprehension
result = [process_complex_logic(item)
          for sublist in nested_list
          for item in sublist
          if complex_condition(item) and another_condition(sublist)]

# Better - use regular loops for complex logic
result = []
for sublist in nested_list:
    for item in sublist:
        if complex_condition(item) and another_condition(sublist):
            result.append(process_complex_logic(item))
```

### Context Managers
Use context managers for resource management:

```python
# Bad
file = open("data.txt")
data = file.read()
file.close()

# Good
with open("data.txt") as file:
    data = file.read()
```

### Property Decorators
Use properties for computed attributes:

```python
class Task:
    def __init__(self, title: str, estimated_hours: float):
        self.title = title
        self.estimated_hours = estimated_hours
        self.completed_hours = 0.0

    @property
    def progress_percentage(self) -> float:
        if self.estimated_hours == 0:
            return 0.0
        return (self.completed_hours / self.estimated_hours) * 100

    @property
    def is_overdue(self) -> bool:
        return self.completed_hours > self.estimated_hours
```

## Code Organization

### Module Structure
```
alfred/
├── models/          # Domain models (Pydantic)
├── database/        # Database models and repositories
├── services/        # Business logic
├── tools/           # MCP tool implementations
├── utils/           # Shared utilities
└── config/          # Configuration management
```

### File Naming
- Use lowercase with underscores
- Be descriptive but concise
- Group related functionality

```
# Good
task_service.py
project_repository.py
dependency_validator.py

# Bad
utils.py  # Too generic
proj_repo.py  # Unclear abbreviation
TaskServiceImpl.py  # Java-style naming
```

## Performance Considerations

### Lazy Evaluation
Use generators for large datasets:

```python
from typing import List, Generator
from alfred.models.task import Task

# Bad - loads everything into memory
def get_all_active_tasks() -> List[Task]:
    return [task for task in database.query_all_tasks() if task.is_active]

# Good - yields one at a time
def get_all_active_tasks() -> Generator[Task, None, None]:
    for task in database.query_all_tasks():
        if task.is_active:
            yield task
```

## Final Checklist

Before committing code, ensure:

- [ ] All functions have clear, descriptive names
- [ ] Variable names clearly indicate their purpose
- [ ] No unnecessary comments (code is self-documenting)
- [ ] Functions are small and do one thing
- [ ] All functions have type hints
- [ ] Constants are extracted and named
- [ ] Error handling is specific and informative
- [ ] Tests are descriptive and comprehensive
- [ ] Code follows PEP 8 style guide
- [ ] No code duplication (DRY principle)

## Remember

> "Clean code always looks like it was written by someone who cares." - Robert C. Martin

The goal is not just working code, but code that other developers (including future you) will thank you for writing.
