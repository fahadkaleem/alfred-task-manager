## Python Unit Testing Best Practices For Building Reliable Applications

In software development, the importance of unit testing cannot be overstated.

A poorly constructed test suite can lead to a fragile codebase, hidden bugs, and hours wasted in debugging.

Not to mention hard to maintain, extend, redundant, non-deterministic and no proper coverage. So how do you deal with the complexities of crafting effective unit tests?

How do you ensure your code works as expected? What’s the difference between good and great software?

The answer? Thoughtful and efficient tests.

After conversations with Senior Python developers, reading countless books on the subject and my broad experience as a Python developer for 8+ years, I collected the below Python unit testing best practices.

This article will guide you through the labyrinth of best practices and strategies to ensure your tests are reliable, maintainable and efficient.

You’ll learn how to keep your tests fast, simple, and focused on singular functions or components.

We’ll delve into the art of making tests readable and deterministic, ensuring they are an integrated part of your build process.

The nuances of naming conventions, isolation of components, and the avoidance of implementation coupling will be dissected.

We’ll also touch upon advanced concepts like Dependency Injection, Test Coverage Analysis, and Test-Driven Development (TDD).

Let’s embark on this journey to ensure your unit tests are as robust and effective as your code.

### Why Care About Unit Testing Best Practices?

Without proper practices, tests can become a source of frustration and inefficiency bottlenecks.

If you don’t take the time to learn and put in place best practices from the get-go, refactoring and maintenance become difficult.

From minor issues like changing your tests often to larger issues like broken CI Pipelines blocking releases.

Common issues include:

1.  **Inefficient Testing**: Tests that are slow or complex can delay development cycles, making the process cumbersome and less productive.
2.  **Lack of Clarity**: Badly written tests with unclear intentions make it difficult for developers to understand what is being tested or why a test fails.
3.  **Fragile Tests**: Tests that are tightly coupled with implementation details can break easily with minor code changes, leading to increased maintenance.
4.  **Test Redundancy**: Writing tests that duplicate implementation logic can lead to bloated test suites.
5.  **Non-Deterministic Tests**: Flaky tests that produce inconsistent results undermine trust in the testing suite and can mask real issues.
6.  **Inadequate Coverage**: Missing key scenarios, especially edge cases, can leave significant gaps in the test suite, allowing bugs to go undetected.

In this article, we aim to resolve these challenges by providing guidelines and techniques to write tests that are fast, simple, readable, deterministic and well-integrated into the development process.

The goal is to enhance the effectiveness of the testing process, leading to more reliable and maintainable Python applications.

### Tests Should Be Fast

Fast tests foster regular testing, which in turn speeds up bug discovery. Long-running tests can slow down development and discourage regular testing.

Certain tests, due to their reliance on complex data structures, may take longer. It’s wise to divide these into a separate suite, run via scheduled tasks or use mocking to reduce external resource dependency.

Fast tests can be run regularly, a key aspect in continuous integration environments where tests may accompany every commit.

To maintain a strong development workflow, prioritize testing concise code segments and minimize dependencies and large setups.

The faster your tests, the more dynamic and efficient your development cycle will be.

### Tests Should Be Independent

Each test should be able to run individually and as part of the test suite, irrespective of the sequence in which it’s executed.

Adhering to this rule necessitates that each test starts with a fresh dataset and often requires some form of post-test cleanup.

Pytest manages this process via Fixture Setup/Teardown, ensuring that each test is self-contained and its outcome unaffected by preceding or later tests.

```python
import pytest

@pytest.fixture
def fresh_dataset():
    # Setup a fresh dataset
    dataset = create_dataset()
    yield dataset
    # Cleanup after the test
    dataset.cleanup()

def test_sample(fresh_dataset):
    # Test using the fresh dataset
    assert some_condition(fresh_dataset) == expected_result
```

### Each Test Should Test One Thing

A test unit should concentrate on one small functionality and verify its correctness.

Avoid combining many functionalities in a single test, as this can obscure the source of errors and be difficult to refactor.

Instead, write separate tests for each functionality, which aids in pinpointing specific issues and ensures clarity.

This approach enhances test effectiveness and maintainability.

**What Not To Do:**

```python
# Bad practice: Testing multiple functionalities in one test
def test_user_creation_and_email_sending():
    user = createUser("test@example.com")
    assert user.email == "test@example.com"
    sendWelcomeEmail(user)
    assert emailService.last_sent_email == "test@example.com"
```

**What To Do:**

```python
# Good practice: Testing one functionality per test
def test_user_creation():
    user = createUser("test@example.com")
    assert user.email == "test@example.com"

def test_welcome_email_sending():
    user = User("test@example.com")
    sendWelcomeEmail(user)
    assert emailService.last_sent_email == "test@example.com"
```

### Tests Should Be Readable (Use Sound Naming Conventions)

Readable tests act as documentation, conveying the intended behaviour of the code.

Well-structured and comprehensible tests help with easier maintenance and quicker debugging.

The use of descriptive names and straightforward logic ensures that anyone reviewing the code can understand the test’s purpose and function.

**What Not To Do:**

```python
def test1():
  assert len([]) == 0
```

**What To Do:**

```python
def test_empty_list_has_zero_length():
    assert len([]) == 0
```

### Tests Should Be Deterministic

Deterministic tests give consistent results under the same conditions, ensuring test predictability and trustworthiness.

**Deterministic**

```python
def test_addition():
    assert 2 + 2 == 4
```

This test is deterministic because it produces the same outcome.

It avoids relying on external factors like network dependencies or random data, which can lead to erratic test results.

By ensuring tests are deterministic, you create a robust foundation for your test suite.

This allows for repeatable, reliable testing across different environments and over time.

**Non-Deterministic**

```python
import random

def test_random_number_is_even():
    assert random.randint(1, 100) % 2 == 0
```

This test is non-deterministic because it relies on a random number generator.

The outcome can vary between runs, sometimes passing and sometimes failing, making it unreliable.

**Managing Non-Deterministic Tests:**

To manage non-deterministic tests, it’s crucial to drop randomness or external dependencies where possible.

If randomness is essential, consider using fixed seeds for random number generators.

For external dependencies like databases or APIs, use mock objects or fixtures to simulate predictable responses.

Libraries like Faker and Hypothesis allow you to test your code against a variety of sample input data.

```python
def test_random_number_is_even():
    random.seed(42)  # Setting a fixed seed
    assert random.randint(1, 100) % 2 == 0
```

### Tests Should Not Include Implementation Details

Tests should verify behaviour, not implementation details.

They should focus on what the code does, not how it does it.

This distinction is crucial for creating robust, maintainable tests that remain valid even when the underlying implementation changes.

**What Not To Do:**

```python
def test_add():
    assert 2 + 3 == 5  # includes implementation detail
```

**What To Do:**

```python
def test_add():
    assert add(2, 3) == 5  # Implementation detail abstracted
```

In the second example, the test checks if `add` correctly computes the sum, independent of how the function achieves this.

This approach allows the `add` function to evolve (e.g., optimization, refactoring) without requiring changes to the test as long as it fulfils its intended behaviour.

### Tests Should Be Part Of The Commit and Build Process

Integrating tests into the commit and build process is essential for maintaining code quality.

This integration ensures that tests are automatically run during the build, catching issues early and preventing bugs from reaching production.

It enforces a standard of code health and functionality, serving as a crucial checkpoint before deployment.

Automated testing within the build process streamlines development, enhances reliability and fosters a culture of continuous integration and delivery.

You can use pre-commit hooks to run tests before each commit, ensuring that only passing code is committed.

You can set up Pytest to run with CI tooling like GitHub Actions, Bamboo, CircleCI, Jenkins and so on that runs your test after deployment thus helping your release with confidence.

### Use Single Assert Per Test Method

Each test should aim to verify a single aspect of the code, making it easier to identify the cause of any failures.

This approach simplifies tests and makes them more maintainable.

**Multiple Asserts (Not Recommended):**

```python
def test_user_profile():
    user = UserProfile('John', 'Doe')
    assert user.first_name == 'John'
    assert user.last_name == 'Doe'
    assert user.full_name() == 'John Doe'
```

**Single Assert per Test (Recommended):**

```python
def test_user_first_name():
    user = UserProfile('John', 'Doe')
    assert user.first_name == 'John'

def test_user_last_name():
    user = UserProfile('John', 'Doe')
    assert user.last_name == 'Doe'

def test_user_full_name():
    user = UserProfile('John', 'Doe')
    assert user.full_name() == 'John Doe'
```

In the recommended approach, each test focuses on a single assertion, providing a clear and specific test for each aspect of the user profile.

This makes it easier to diagnose issues when a test fails, as each test is focused on one functionality.

### Use Fake Data/Databases in Testing

Using fake data or databases in testing allows you to simulate various scenarios without relying on actual databases, which can be unpredictable and slow down tests.

Fake data ensures consistency in test environments and prevents tests from failing due to external data changes.

It also helps keep tests faster and prevents accidental updates to the source data.

```python
def test_calculate_average_age():
    fake_data = [{'age': 25}, {'age': 35}, {'age': 45}]
    average_age = calculate_average_age(fake_data)
    assert average_age == 35
```

```python
from unittest.mock import MagicMock

def test_user_creation():
    db = MagicMock()
    db.insert_user.return_value = True
    user_service = UserService(db)
    result = user_service.create_user("John Doe", "john@example.com")
    assert result is True
```

In the first example, `fake_data` is used to test the calculation function without needing real data.

In the second, a mock database (`MagicMock`) is used to simulate database interactions.

This technique isolates the tests from external data sources and makes them more predictable and faster.

You can also spin up a local SQLite database for your tests.

SQLite databases are lightweight, don’t need a separate server, and can be integrated into a test setup.

### Use Dependency Injection

In Python unit testing, Dependency Injection (DI) is a best practice that enhances code testability and modularity.

DI involves providing objects with their dependencies from outside, rather than having them create dependencies internally.

This method is particularly valuable in testing, as it allows for easy substituting of real dependencies with mocks or stubs.

For instance, a class that requires a database connection can be injected with a mock database during testing, isolating the class’s functionality from external systems.

This separation fosters cleaner, more maintainable code and simplifies the creation of focused reliable unit tests.

**Without Dependency Injection**

```python
class DatabaseConnector:
    def connect(self):
        # Code to connect to a database
        return "Database connection established"

class DataManager:
    def __init__(self):
        self.db = DatabaseConnector()

    def data_operation(self):
        return self.db.connect() + " - Data operation done"
```

In this scenario, testing `DataManager`‘s `data_operation` method is challenging because it’s tightly coupled with `DatabaseConnector`.

**With Dependency Injection (DI)**

```python
class DatabaseConnector:
    def connect(self):
        # Code to connect to a database
        return "Database connection established"

class DataManager:
    def __init__(self, db_connector):
        self.db = db_connector

    def data_operation(self):
        return self.db.connect() + " - Data operation done"

# During testing
class MockDatabaseConnector:
    def connect(self):
        return "Mock database connection"

# Test
def test_data_operation():
    mock_db = MockDatabaseConnector()
    data_manager = DataManager(mock_db)
    result = data_manager.data_operation()
    assert result == "Mock database connection - Data operation done"
```

In the DI example, `DataManager` receives its `DatabaseConnector` dependency from the outside.

This allows us to inject a `MockDatabaseConnector` during testing, focusing the test on `DataManager`‘s behaviour without relying on the actual database connection logic.

This makes the test more reliable, faster, and independent of external factors like a real database.

### Use Setup and Teardown To Isolate Test Dependencies

In Python unit testing, isolating test dependencies is key to reliable outcomes.

Setup and teardown methods are instrumental and enable reusable and isolated test environments

The setup method prepares the test environment before each test, ensuring a clean state.

Conversely, the teardown method cleans up after tests, removing any data or state alterations.

This process prevents interference between tests, maintaining their independence.

Fixtures, in Pytest, provide a flexible way to set up and tear down code for many tests.

```python
import pytest

@pytest.fixture
def resource_setup():
    # Setup code: Create resource
    resource = "some resource"
    print("Resource created")

    # This yield statement is where the test execution will take place
    yield resource

    # Teardown code: Release resource
    print("Resource released")

def test_example(resource_setup):
    assert resource_setup == "some resource"
```

This approach ensures that the resource is set up before each test that uses the fixture and properly cleaned up afterwards, maintaining test isolation and reliability.

If you need a refresher on Pytest fixture setup and teardown, this article is a good starting point.

You can easily control fixture scopes using the `scope` parameter as detailed in this guide.

### Group Related Tests

Organizing related tests into modules or classes is a cornerstone of good unit testing in Python.

This practice enhances test clarity and manageability.

By grouping, you logically categorize tests based on functionality, such as testing a specific module or feature.

This not only makes it easier to locate and run related tests but also improves the readability of your test suite.

For instance, all tests related to a `User` class might reside in a `TestUser` class:

```python
class TestUser(unittest.TestCase):
    def test_username(self):
        # Test for username
    def test_password(self):
        # Test for password
```

This structure ensures an organized approach, where related tests are grouped, making it easier to navigate and maintain the test suite.

### Mock Where Necessary (with Caution)

In Python unit testing, the judicious use of mocking is essential.

Mocking replaces parts of your system under test with mock objects, isolating tests from external dependencies like databases or APIs.

This accelerates testing and focuses on the unit’s functionality.

However, over-mocking can lead to tests that pass despite bugs in production code, as they might not accurately represent real-world interactions.

These articles provide a practical guide on how to use Mock and Monkeypatch in Pytest.

### Use Test Framework Features To Your Advantage

Leveraging the full spectrum of features offered by Python test frameworks like Pytest can significantly enhance your testing practice. Key among these in Pytest are `conftest.py`, fixtures, and parameterization.

`conftest.py` serves as a central place for fixture definitions, making them accessible across multiple test files, thereby promoting reuse and reducing code duplication.

Pytest Fixtures offer a powerful way to set up and tear down resources needed for tests, ensuring isolation and reliability.

Pytest Parameterization allows for the easy creation of multiple test cases from a single test function, enabling efficient testing of various input scenarios.

Harnessing these features streamlines the testing process, ensuring more organized, maintainable, and comprehensive test suites.

### Practice Test Driven Development (TDD)

TDD is a foundational practice involving writing tests before writing the actual code.

Start by creating a test for a new function or feature, which initially fails (as the feature isn’t implemented yet).

Then, write the minimal amount of code required to pass the test.

This cycle of “Red-Green-Refactor” — writing a failing test, making it pass, and then refactoring — guides development, ensuring that your codebase is thoroughly tested and designed with testing in mind.

As you iterate, the tests evolve along with the code, facilitating a robust and maintainable codebase.

### Regularly Review and Refactor Tests

Consistent review and refactoring of tests are crucial.

This involves examining tests to ensure they remain relevant, efficient, and readable.

Refactoring might include removing redundancy, updating tests to reflect code changes, or improving test organization and naming.

This proactive approach keeps the test suite streamlined, improves its reliability, and ensures it continues to support ongoing development and codebase evolution.

### Analyze Test Coverage

Coverage analysis involves using tools like coverage.py to measure the extent to which your test suite exercises your codebase.

High coverage means you’ve tested a larger part of your code.

While this is helpful, it doesn’t mean your code is free from bugs. It means you’ve tested the implemented logic.

Testing edge cases and against a variety of test data to uncover potential bugs should be your top priority.

You can read more about how to generate Pytest coverage reports here.

### Test for Security Issues as Part of Your Unit Tests

Security testing involves crafting tests to uncover vulnerabilities like injection flaws, broken authentication, and data exposure.

Using libraries like `Bandit`, you can automate the detection of common security issues.

For instance, if your application involves user input processing, your tests should include cases that check for common security issues like SQL injection or cross-site scripting (XSS).

Consider a function that queries a database:

```python
def get_user_details(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    # Execute query and return results
```

This function is vulnerable to SQL injection. To test for this security issue, you can write a unit test that attempts to exploit this vulnerability:

```python
import pytest
from mymodule import get_user_details

def test_sql_injection_vulnerability():
    malicious_input = "1; DROP TABLE users"
    with pytest.raises(SecurityException):
        get_user_details(malicious_input)
```

In this test, `malicious_input` simulates an SQL injection attack.

The test checks if the function `get_user_details` properly handles such input, ideally by raising a `SecurityException` or similar.

Using tools like `Bandit`, you can automatically scan your code for such vulnerabilities and known security issues.

I would also recommend against using raw SQL in your code unless absolutely necessary and instead use an ORM (Object Relational Mapping) tool like SQLAlchemy or SQL Model to perform database operations.

### Conclusion

In this comprehensive guide, we’ve gone through the essential Python unit testing best practices.

From the importance of fast, independent, and focused tests, to the clarity that comes from readable and deterministic tests, you now have the tools to enhance your testing strategy.

We’ve covered advanced techniques like Dependency Injection, Test Coverage Analysis, Test-Driven Development (TDD), and the critical role of security testing in unit tests.

As you apply these best practices, continue to review and refine your tests.

Embrace the mindset of continuous improvement and let these principles guide you towards creating exemplary Python applications.

Your journey in mastering Python unit testing doesn’t end here; it evolves with every line of code you write and the tests you create.

So, go ahead, apply these Python unit testing best practices, and witness the transformation in your development workflow.

## 5 Best Practices For Organizing Tests (Simple And Scalable)

Picture this: you join a growing project with thousands of tests. Or your project has grown over time to hundreds of tests.

Different developers work on the codebase, each with various skills and styles, leading to inconsistent best practices.

Scattered test files, inconsistent naming conventions, overloaded fixtures. and `conftest.py` files, creating more confusion than clarity.

Debugging even a single test failure takes hours. It’s messy and overwhelming, leaving you wondering where to begin and how to refactor.

But it doesn’t have to be this way.

For this article, I’ve reviewed and studied some of the best practices for organizing tests for simplicity, scalability, and efficiency.

I’ll also share stuff I learned from my 9 years of professional experience as a Python developer in the industry.

We’ll tackle the challenges of disorganized tests head-on and show you how to create a future-proof testing strategy.

You’ll learn how to:

*   **Avoid common pitfalls** like overloaded test files and monolithic tests.
*   **Leverage the testing pyramid** to effectively balance unit, integration, and end-to-end tests.
*   **Structure your tests** to mirror application code and separate them cleanly in dedicated folders.
*   **Maximize Pytest’s flexibility** to organize fixtures, manage test data, and control scope with `conftest.py`.
*   **How to organize views, templates, and URLs for specific frameworks** like Django, ensuring best practices.

By the end of this article, you’ll have the tools and techniques to build a scalable, maintainable test suite that grows with your project and makes it quick and easy to understand and onboard new developers.

Let’s dive in!

### Why Disorganized Tests Are An Issue?

Before we go into solutions, we must talk about the problem first.

Disorganized tests introduce chaos into your development workflow, making even simple tasks unnecessarily complex.

Overloading a single test file or module with too many tests results in slow feedback and harder debugging.

Inconsistent naming conventions create confusion and waste time as new developers struggle to locate specific tests.

Global fixtures, when overused, lead to test interdependence, causing unrelated tests to fail unexpectedly.

Worse yet, overloaded fixtures with too many responsibilities blur the line between setup and test logic, making tests fragile and difficult to maintain.

Monolithic tests — large, unwieldy tests that try to do too much — are especially hard to debug and mask poor code design and bad practices.

And then there are flaky tests — tests that sometimes pass and sometimes fail.

Ignoring or leaving these unresolved frustrates your team and erodes confidence in your test suite.

Without proper organization, your tests become a liability instead of an asset.

Let’s look at some best practices on how to tackle these and organize your tests for ease today and tomorrow.

### Best Practice # 1 — Organizing Tests by Testing Pyramid

One of the easiest ways to get started organizing your tests is to think of it in terms of the Testing Pyramid.

Without getting into too much detail here, it means you have a lot of unit tests, fewer service or integration tests, and the least end-to-end or functional tests.

These could also be UI tests using tools like Selenium, Playwright or Cypress.

UI tests are slow and heavy while unit tests are fast and lightweight. If you’re unfamiliar with the test pyramid concept I recommend you check out Martin Fowler’s article.

*   **Unit Tests** —Fast, isolated tests that validate small, discrete units of code like functions or classes.
*   **Integration Tests** — These ensure that different components of your application work together as expected, such as testing APIs or database interactions.
*   **End-to-End Tests** — These simulate real-world workflows and validate the behavior of the entire application from the user’s perspective.

There is no agreed-upon definition of each of these, but I encourage you to familiarize yourself with the various types of testing.

Grouping your tests by type immediately gives developers a high-level perspective and aids in deciding what you need to test and in which order.

A typical folder structure may look like this.

```
tests/
├── unit/
│   ├── __init__.py
│   ├── test_user.py
│   ├── test_order.py
│   ├── test_payment_service.py
│   └── test_notification_service.py
│
├── integration/
│   ├── __init__.py
│   ├── test_api_endpoints.py
│   ├── test_database_interactions.py
│   └── test_service_integration.py
│
├── e2e/
│   ├── __init__.py
│   ├── test_user_journey.py
│   ├── test_checkout_flow.py
│   └── test_admin_dashboard.py
│
│
├── conftest.py
└── pytest.ini
```

Pytest also gives you the option to mark your tests using the `@pytest.mark.X` decorator for example — `@pytest.mark.unit`, which is very helpful.

You can also run tests directly using the marker for example

```
$ pytest -m unit
```

Check out this article if you need a refresher on Pytest markers.

### Best Practice #2: Test Structure Should Mirror Application Code

Another good practice in organizing tests is to mirror your application’s folder structure.

This is a simple yet powerful way to ensure clarity and maintainability.

When your tests align with your application’s modules and directories, navigating between the two becomes intuitive — saving time and reducing confusion.

For example, if your application has separate modules for `models`, `services`, and `controllers`, your test directory should reflect this structure.

Each test file focuses on the corresponding module, making it easier to locate and update tests when code changes.

This structure also helps new team members quickly understand how the test suite relates to the application, making new feature development and refactors easier.

**Example Structure:**
If your application code looks like this:

```
src/
├── models/
│   ├── user.py
│   └── order.py
├── services/
│   ├── payment_service.py
│   └── notification_service.py
└── controllers/
    └── order_controller.py
```

Your test folder should mirror it like this:

```
tests/
├── models/
│   ├── test_user.py
│   └── test_order.py
├── services/
│   ├── test_payment_service.py
│   └── test_notification_service.py
└── controllers/
    └── test_order_controller.py
```

**Benefits:**

1.  Improved Readability: Directly map tests to the corresponding application components.
2.  Easier Debugging: Quickly locate and fix tests related to a specific module.
3.  Scalability: As the application grows, the test structure naturally evolves alongside it.
4.  Collaboration: This makes it easier for developers and QA teams to align their work.

By mirroring your application’s structure, your test suite becomes an organized, intuitive resource rather than a tangled mess of files.

### Best Practice #3 — How to Group or Organize Fixtures

Fixtures are reusable pieces of code that can be used in tests, to reduce boilerplate, improve efficiency, and handle setup and teardown.

Organizing fixtures effectively is key to maintaining a clean and scalable test suite.

Poorly managed fixtures can lead to unnecessary complexity, slow tests, and hard-to-track dependencies.

By grouping and scoping your fixtures thoughtfully, you can streamline your testing process and improve efficiency.

Here’s a quick run-through of Pytest fixture scopes. If you’re familiar with that then please skip ahead.

Pytest fixtures can have different scopes, determining their lifespan and reuse:

**Function-Scoped** (default): The fixture is created and destroyed for each test function. Use this for test-specific setups, such as temporary files or isolated database states.

```python
@pytest.fixture
def temp_file():
    with open("temp.txt", "w") as f:
        yield f
```

**Class-Scoped**: The fixture is created once per test class and shared across its methods. Ideal for initializing objects or states used in all tests within a class.

```python
@pytest.fixture(scope="class")
def sample_data():
    return {"key": "value"}
```

**Module-Scoped**: The fixture is shared across all tests in a module. Best for expensive setups like database connections or API clients.

```python
@pytest.fixture(scope="module")
def db_connection():
    return connect_to_db()
```

There is also session scope which applies a fixture to an entire test session.

#### Centralized vs. Localized Fixtures: Finding the Right Balance

When managing fixtures in Pytest, the choice between a centralized fixtures folder and localized `conftest.py` files often depends on the size and complexity of your project.

Both approaches have unique benefits, and combining them into a hybrid strategy can offer the best of both worlds.

#### Centralized Fixtures

Using a dedicated `fixtures/` folder is ideal for shared resources that multiple test directories rely on, such as database connections or API clients.

Grouping fixtures into modules like `fixtures_db.py` or `fixtures_api.py` keeps them organized and promotes reusability.

```
tests/
├── fixtures/
│   ├── fixtures_db.py
│   ├── fixtures_api.py
│   └── fixtures_auth.py
├── unit/
│   ├── conftest.py
│   └── test_models.py
├── integration/
│   ├── conftest.py
│   └── test_api.py
```

But these come with tradeoffs.

**Pros:**

*   Centralized Management: Grouping fixtures by functionality (e.g., `fixtures_db.py`, `fixtures_api.py`) keeps them organized and easy to locate (especially mocks).
*   Reusability: Shared fixtures are available across your test suite without duplication.
*   Scalability: Works well for large projects with many test files and fixtures.
*   Better Separation of Concerns: Fixtures can be split into modules, reducing the size of any single file.

**Cons:**

*   Requires Explicit Imports: You must import fixtures into tests, which can make them less “magically available.”
*   Potential for Overuse: Centralized fixtures can lead to over-reliance, creating hidden dependencies between unrelated tests.

#### Using `conftest.py` in Local Directories (Localised Fixtures)

On the other hand, `conftest.py` files in specific test directories are perfect for test-specific setups.

These ensure that narrowly scoped logic doesn’t clutter the global namespace or affect unrelated tests.

For example.

```
tests/
├── unit/
│   ├── conftest.py        # Fixtures specific to unit tests
│   └── test_models.py
├── integration/
│   ├── conftest.py        # Fixtures specific to integration tests
│   └── test_api.py
```

**Pros:**

*   Implicit Discovery: Pytest automatically discovers fixtures defined in `conftest.py`, so there’s no need to import them manually.
*   Localized Scope: Fixtures are scoped to a specific directory, reducing the risk of unintended dependencies between unrelated tests.
*   Simpler for Small Projects: Keeps fixtures tied closely to the tests they support, making it easy to understand their usage.

**Cons:**

*   Difficult to Scale: As the number of tests grows, managing fixtures across multiple `conftest.py` files can become unwieldy.
*   Duplication: Without careful planning, fixtures may be duplicated across directories, leading to maintenance challenges.

#### Best of Both Worlds

In larger projects, you may want to consider a hybrid approach:

1.  Use a `fixtures/` folder for broadly shared, reusable fixtures like database connections or mocks.
2.  Use local `conftest.py` files for directory-specific or narrowly scoped fixtures, such as test-specific data or setup logic.

```
tests/
├── fixtures/
│   ├── fixtures_db.py
│   ├── fixtures_api.py
│   └── fixtures_auth.py
├── unit/
│   ├── conftest.py
│   └── test_models.py
├── integration/
│   ├── conftest.py
│   └── test_api.py
```

This approach keeps your test suite maintainable and scalable.

I like to keep my fixtures within a `conftest.py` file local to that directory and share common fixtures in a `conftest.py` file placed in the `tests` directory.

Having learned how to organize your fixtures, let’s see if it’s a good idea to include tests within the application code. And what factors drive that decision.

### Best Practice #4 — Tests Outside vs. Inside Application Code

A key decision is whether to keep tests **outside** or **inside** (with) the application code.

Each approach has its advantages and trade-offs, and the right choice depends on your project’s size, purpose, and deployment strategy.

#### Tests Outside Application Code

**Advantages:**

*   Separation of Concerns: Keeping tests in a `tests/` folder ensures your application code is clean and free of testing artifacts.
*   Clarity and Organization: A dedicated folder allows for a clear hierarchy and separation of unit, integration, and end-to-end tests.
*   Avoids Deployment Risks: Excluding tests from production deployments reduces overhead and mitigates potential security risks.
*   Scalability: Works well for large projects with extensive test suites.

```
project/
├── src/
│   ├── models/
│   └── services/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   └── fixtures/
```

Best suited for production-grade applications, where maintaining a clean separation between test code and production code is essential.

#### Tests as Part of Application Code

**Advantages:**

*   Tightly Coupled Testing: Embedding tests within application modules can simplify testing for libraries or reusable modules, as tests are colocated with the code they validate.
*   Smaller Projects: Useful for smaller projects or packages where the simplicity of having everything in one place outweighs the benefits of separation.
*   Quick Context: Developers can quickly access and understand the tests alongside the code.

**Potential Risks:**

*   Deployment Risks: Without proper filtering, test code might inadvertently be included in production builds.
*   Codebase Clutter: Embedding tests can make the codebase harder to navigate, especially as the project grows.

```
src/
├── models/
│   ├── user.py
│   └── tests/
│       └── test_user.py
├── services/
│   ├── payment_service.py
│   └── tests/
│       └── test_payment_service.py
```

Ensure production builds exclude `tests/` folders by configuring your deployment pipeline or packaging tools.

#### Choosing the Right Approach

When to Keep Tests Outside:

*   Large applications with multiple developers and complex testing needs.
*   Projects where deployment risks or production performance are critical.
*   Applications requiring robust test suites with a clear separation of concerns.

When to Embed Tests Inside:

*   Small libraries or standalone modules intended for reuse.
*   Quick prototyping or proof-of-concept projects.
*   When ease of access and simplicity are prioritized over scalability.

### Best Practice #5 — Organizing Tests for Django Applications

Django applications often involve multiple components like models, views, templates, and serializers, where each one needs to be thoroughly tested.

Some ideas include grouping Django tests by `views` , `models` , `templates` and so on.

```
tests/
├── unit/
│   ├── models/
│   │   ├── test_user_model.py
│   │   ├── test_order_model.py
│   │   └── __init__.py
│   ├── serializers/
│   │   ├── test_user_serializer.py
│   │   └── test_order_serializer.py
│   ├── views/
│   │   ├── test_user_views.py
│   │   └── __init__.py
│   ├── templates/
│   │   └── test_user_templates.py
│   └── __init__.py
│
├── integration/
│   ├── test_user_workflow.py
│   ├── test_order_workflow.py
│   └── __init__.py
│
├── e2e/
│   ├── test_full_user_journey.py
│   ├── test_checkout_process.py
│   └── __init__.py
│
├── fixtures/
│   ├── fixtures_db.py
│   ├── fixtures_auth.py
│   └── __init__.py
│
└── conftest.py
```

These are just ideas and not hard and fast rules. Check out some sample Django projects for more ideas.

Some companies prefer to use Django Unit Tests and group their tests differently.

The best practice is the one that is easy for you and your team to understand, manage, and scale.

### Conclusion

In this article, you learned how to transform your test suite from a chaotic mess into a scalable, maintainable asset.

We covered key strategies for organizing your tests effectively like grouping by test pyramid, mirroring application code and organizing fixtures thoughtfully.

You also learned how to decide whether to package tests with application code or keep them separate and lastly, how to group tests in a Django application.

The overarching message is clear: there’s no one-size-fits-all solution.

The most important step is to take the time to **think critically about your test structure**.

Aim to make it easy to understand, maintain, and scale. Don’t be afraid to adapt your approach as your project evolves.

Now it’s your turn to put these principles into practice.

Start small — refactor a few files, organize your fixtures, or implement the Testing Pyramid. See what works for you and your team, and iterate from there.

## 13 Proven Ways To Improve Test Runtime With Pytest

Imagine this, you’ve just joined a company and your first task is to optimise the existing test suite and improve the CI/CD run time.

Or maybe you’re a veteran Python developer and with success, your test suite has grown substantially to 1000 tests, maybe 2000 tests?

Now it’s getting out of control and each run takes 5 mins or more. CI/CD Pipelines cost a small fortune.

You’re testing backend APIs, data ETL processes, user authentication, disk writes and so on.

How do you optimize test run time? Where do you start?

Well, in this article you’ll learn 13 (or maybe 14) practical strategies to improve the runtime of your Pytest suite.

No matter how large or small, Pytest expert or novice, you’ll learn tips to implement today.

I’ve also included a bonus tip from the folks over at Discord on how they were able to reduce the median test duration from 20 seconds down to 2 seconds!

Whether its API testing, integration tests with an in-memory database, or data transformation tests, these strategies will help you tackle any slowdown and set a foundation for efficient testing.

You’ll learn how to identify slow tests, profile them, fix bottlenecks, and put in place best practices.

All this and leveraging the power of Pytest features and plugins to your advantage.

Are you ready? Let’s begin.

### What You’ll Learn

In this article, you’ll learn:

*   How to identify slow-running tests in your test suite
*   Improve run-time of slow-running tests
*   Best practices to leverage Pytest features — fixtures, parametrization and the `xdist` plugin for running tests in parallel.
*   Efficiently handle setup teardown of databases
*   Strategies to benchmark and maintain a large growing test suite

### Why Should You Worry about Slow Tests?

Let’s ask an important question, why should you worry or care about slow tests?

Is this even a problem? Can’t you just let the tests run for as long as it takes and go do something else?

Well, the answer is no, and here’s why.

**Slow Feedback Loop**

As test-driven development (TDD) developers, we run tests as part of code development.

A slow test suite is incredibly frustrating and reduces the feedback loop, making you less agile and introducing room for distractions.

While it’s true you can run a single test in Pytest, you also want to make sure your functionality hasn’t broken anything else.

This is also called Regression Testing.

Slow tests delay this feedback, making it harder for you to rapidly identify and fix issues.

Fast tests, on the other hand, enable a smoother and more efficient development cycle, allowing you to iterate quickly

**Continuous Integration Efficiency**

Slow-running CI Pipelines can be a headache to deal with.

Some pipelines are set up to run on every Git Commit, making feedback painstaking.

Especially if you need to push commits iteratively to fix a stubborn test that passes locally but not on the CI server.

Fast running tests are a blessing.

**Cost Implications**

Slow tests also have cost implications beyond developer productivity, particularly in the cloud where resources are billed by usage.

Faster tests mean less resource consumption and, therefore, lower operational costs.

**Test Reliability and Maintenance**

Slow running tests often do so because they are doing too much, or are poorly optimized.

This can lead to reliability issues, where tests fail intermittently or have flaky behaviour.

Ensuring tests run quickly goes hand in hand with making them more reliable and easier to maintain.

Hoping you’re convinced why this is a problem worth addressing, let’s move on to identifying the problem tests.

### Identify The Problem Tests

What is the exact problem we’re trying to solve here?

Fix slow tests? Cool.

But how do you know which tests are slow? Are you sure those tests are responsible for the slowdown?

_Measure_ — Before doing any optimization, I strongly advise you to measure test collection and execution time.

After all, you cannot improve what you don’t measure.

_Optimize the right tests_ — While it’s tempting to optimise algorithms using tools like Pytest Benchmark, you need to understand where the low-hanging fruit is.

What tests you can easily make faster, after all you haven’t the time to rewrite every single test.

### Profiling Tests

In a large test suite, it’s not a good idea to try and optimize everything at once.

You can first identify the slow-running tests using the `--durations=x` flag.

To get a list of the slowest 10 test durations over 1.0s long:

```
pytest --durations=10 --durations-min=1.0
```

By default, Pytest will not show test durations that are too small (<0.005s) unless `-vv` is passed on the command line.

To quickly demo this, I’ve set up a simple project.

We have a simple repo

```
.
├── .gitignore
├── README.md
├── requirements.txt
└── tests
    ├── test_runtime_examples1.py
    └── test_runtime_examples2.py
```

In the `tests` folder, we have some basic tests and I’ve stuck a timer in there to simulate slow-running tests.

`tests/test_runtime_examples1.py`

```python
import time


def test_1():
    time.sleep(1)
    assert True


def test_2():
    time.sleep(5)
    assert True


def test_3():
    time.sleep(10)
    assert True
```

Similarly for the other file — `test_runtime_examples2.py` .

Let’s run the command

```
pytest --durations=10
```

We can see we have a nice report showing which tests took the longest time.

Next, you can also use the pytest-profiling plugin to generate tabular and heat graphs.

After you install the plugin, you can run Pytest with `--profile` or `--profile-svg` flags to generate a profiling report.

You can learn more about how to interpret these reports in our article on the 8 Useful Pytest Plugins.

### Understanding Test Collection

Alongside profiling, it’s also useful to understand how much time Pytest spends collecting your tests.

Thankfully, you can easily do this with the  `— collect-only` flag. This feature only shows you what’s collected and doesn’t run any tests.

You can narrow down by directory level and do more as specified in the docs.

You may not notice huge collection times with small test suites but with larger ones involving thousands of tests, it can easily add up to 30 seconds+.

Btw if you’re experiencing the `Pytest Collected 0 Items` error, we have a detailed guide on how to solve it here.

This article from Hugo Martins on the improvements to the Pytest Collection feature is also an interesting read.

### Optimize The Test Collection Phase

In large projects, Pytest may take considerable time just to collect tests before even running them.

This collection phase involves identifying which files contain tests and which functions or methods are test cases.

By optimizing this, you can reduce the startup time of your test runs.

**Keyword Expressions:**

Use `-k` to run tests matching a given expression. For example, to run only tests in a specific class:

```
pytest -k TestMyClass
```

**File Name Patterns:**

Specify particular test files or directories.

```
pytest tests/specific_directory/
```

**Define Testpath in Pytest Config File:**

You can tell Pytest to look at the `tests` directory to collect unit tests.

This can help shave off some time when Pytest doesn’t need to look at your source code and any doctests you may have.

You can combine `testpaths` with other options like `python_files` to further refine how tests are collected.

```ini
# pytest.ini
[pytest]
testpaths = tests/unit tests/integration
python_files = test_*.py
```

By setting this config in `pytest.ini`, you gain more control over which tests are executed, keeping your testing workflow efficient.

If you’ve never used `pytest.ini` or unfamiliar with Pytest config in general, here’s a good starting point.

### Avoid External Calls (Use Mocking Instead)

An incredible way to speed up your tests is to mock external dependencies.

Let’s say your tests connect to a real database or get data from an external REST API.

It helps to mock these out as you significantly reduce the test overhead.

By mocking (simulating) the behaviour of time-consuming external systems, such as databases or APIs, you can focus on the functionality you’re testing without the overhead of real system interactions.

This leads to faster, more efficient test execution.

A simple example can be found in the pytest-mock documentation.

```python
import pytest
import os

class UnixFS:

 @staticmethod
    def rm(filename):
        os.remove(filename)

def test_unix_fs(mocker):
    mocker.patch('os.remove')
    UnixFS.rm('file')
    os.remove.assert_called_once_with('file')
```

The `UnixFS` class contains a static method `rm` that removes a file using the `os.remove` function from Python’s standard library.

In the test function `test_unix_fs`, the `mocker.patch` method from the `pytest-mock` plugin is used to replace the `os.remove` function with a mock.

This mock prevents the actual deletion of a file during the test and allows for the verification of the `os.remove` call.

This test ensures that `UnixFS.rm` interacts with the file system as expected, without affecting real files during testing - while being significantly faster than the real thing.

### Run Tests In Parallel (Use pytest-xdist)

Another tool in your arsenal is Pytest’s parallel testing capability using the `pytest-xdist` plugin.

By distributing tests across multiple CPUs or even separate machines, `pytest-xdist` drastically cuts down the overall runtime of test suites.

This is especially beneficial for large codebases or projects with extensive test coverage.

With `pytest-xdist`, your tests no longer run sequentially; they run in parallel, utilising resources more effectively and providing faster feedback.

We wrote a whole post on using the pytest-xdist plugin to run tests in parallel so definitely check it out.

### Use Setup Teardown Fixtures For Databases

A big optimisation you can implement is once you learn how to use Pytest’s setup teardown mechanism.

This functionality allows you to execute setup and teardown code smoothly at the start or end of your test session or function or class or module.

Fixtures can be controlled using the `scope` parameter explained at length in this article.

A lot of applications use databases for I/O purposes.

If you’re not mocking, you’ll need to set up and teardown the database for each test.

Some apps may require 50–60 or even more tables. Imagine the overhead.

Nothing stops you from using an in-memory database (like SQLite) and recreating the tables for each test. However, this is super inefficient.

It’s way more efficient to create the database and tables once per test session and just truncate them before each test to start with a fresh slate.

A simple pseudo-code style example is as below using FastAPI and SQLModel.

**Database Engine Fixture (Session Scoped)**

This fixture creates the database engine, and it’s set to session scope to ensure it runs only once per test session.

```python
import pytest
from sqlmodel import SQLModel, create_engine
from fastapi.testclient import TestClient
from your_application import get_app  # Import your FastAPI app creation function

@pytest.fixture(scope='session')
def db_engine():
    # Replace with your database URL
    engine = create_engine('sqlite:///:memory:', echo=True)
    SQLModel.metadata.create_all(engine)  # Create all tables
    return engine
```

**Application Fixture (Function Scoped)**

This fixture initializes the FastAPI app for each test function, using the `db_engine` fixture.

```python
@pytest.fixture(scope='function')
def app(db_engine):
    # Modify your FastAPI app creation to accept an engine, if needed
    app = get_app(db_engine)

    yield app

    # Teardown logic, if needed
```

**Table Clearing Fixture (Function Scoped, Auto-Use)**

This fixture will clear the database tables after each test. It runs automatically due to `autouse=True`.

```python
@pytest.fixture(scope='function', autouse=True)
def clear_tables(db_engine):
    # Clear the tables before the test starts
    with db_engine.connect() as connection:
        # Assuming SQLModel is used for models
        for table in SQLModel.metadata.sorted_tables:
            connection.execute(table.delete())

    yield  # Now yield control to the test
```

The pseudo code above cleanly demos how you can run a session-scoped `db_engine` fixture with a function-scoped `clear_tables` fixture to create tables once and truncate them for each test run.

This means we don’t have to start the db engine and create tables for each test, savings precious time.

### Do More With Less (Parametrized Testing)

A cool feature of Pytest is Parametrized Testing - which allows you to test multiple scenarios with a single test function.

By feeding different parameters into the same test logic, you can extensively cover various cases without writing separate tests for each.

This not only reduces code duplication but also allows you to do more with less.

```python
import pytest

@pytest.mark.parametrize("input,expected_output", [(1, 2), (2, 3), (3, 4)])
def test_increment(input, expected_output):
    assert input + 1 == expected_output
```

In this example, the `test_increment` function is executed three times with different `input` and `expected_output` values, testing the increment operation comprehensively with minimal code.

### Run Tests Selectively

A somewhat obvious but often overlooked improvement to run your suite faster is to run tests selectively.

This involves running only a subset of tests that are relevant to the changes in each commit, significantly speeding up the test suite.

```
# Command to run tests in a specific file
pytest tests/specific_feature_test.py

# Command to run a particular test class or method
pytest tests/test_module.py::TestClass
pytest tests/test_module.py::test_function
```

You can also set up pre-commit hooks to run the changed files as part of your Git Commit.

### Use Markers To Prioritise Tests

Running tests that are more likely to fail or that cover critical functionality first can provide faster overall feedback.

A neat way is to organize tests in a way that prioritizes key functionalities.

You can leverage Pytest markers to order tests based on your criteria — e.g. _fast, slow, backend, API, database, UI, data, smoke, recursion_ and so on.

### Efficient Fixture Management

A fast and easy win, though one that must be carefully considered and implemented is the use of Pytest fixtures with the correct scope.

We briefly touched on Pytest fixture scopes in our point on using setup teardown for databases including the `autouse=True` parameter.

Read more about fixture autouse here.

Proper use of fixtures, especially those with `scope=session` or `scope=module`, can prevent repeated setup and teardown.

Analyze your fixtures and refactor them for optimal reuse using the best scope.

### Avoid Sleep or Delay in Tests

Using sleep in tests can significantly increase test time unnecessarily.

Replace `sleep` with more efficient waiting mechanisms, like polling for a condition to be met.

### Configure Pytest Config Files Correctly

Optimizing configuration files like `pytest.ini` and `conftest.py` can significantly enhance the runtime efficiency of your test suite.

You can fine-tune these files for better performance.

#### Optimizing `pytest.ini`

*   By default, Pytest looks for test files in the current and all sub-directories. You can specify the `testpaths` parameter to point to any test folders.

```ini
[pytest]
testpaths =
	tests
	integration
```

*   Disable or reduce Pytest verbosity.
*   Avoid unnecessary captured logs (_caplog_) and outputs (_capsys_). If you’re unfamiliar, you can read more about how to capture logs using Pytest caplog and capturing stdout/stderr here. Disabling output capture where unnecessary can help optimise runtime.
*   Defining custom markers in `pytest.ini` can help you selectively run tests. Define markers for different categories (e.g., `smoke`, `slow`) and use them to include or exclude tests during runtime (`pytest -m "smoke"`).
*   Drop unnecessary environment variables.

#### Optimizing `conftest.py`

*   Drop unused fixtures and avoid repeat setup/teardown using the `scope` parameter.
*   Use the `pytest_addoption` and `pytest_generate_tests` hooks to add custom command-line options and dynamically alter test behaviour or parameters based on these options.
*   If your tests rely on data files, the way you load them can impact performance. Consider lazy loading or caching strategies for test data in fixtures to avoid unnecessary I/O operations.

### Plugin Housekeeping

Ditch unused plugins as Pytest has to load these in every time it runs and can slow down your suite.

Perform regular cleanups of your `requirements.txt` , `pyproject.toml` or other config and dependency files to keep things lean.

Plugins like pytest-incremental can be useful to help detect and run changed test files.

This allows for a faster feedback loop.

### Reduce or Limit Network Access

Network calls in tests, such as requests to web services, databases, or APIs, can significantly slow down your test suite.

These calls introduce latency, potential for network-related failures, and dependency on external systems, which might not always be desirable.

Consider selective mocking practices where it makes sense, such as in unit tests. Integration tests might still need to make real network calls.

Plugins like pytest-socket can prevent inadvertent internet access with the option to override when necessary.

### Use Temporary Files and Directories

Relying on the filesystem introduces potential errors due to changes in file structure or content, and can slow down tests due to disk read/write operations and system constraints.

To address this, you can mock file systems using the `mocker` fixture provided by the `pytest-mock` plugin, built atop the `unittest.mock` library.

Other strategies may include using In-Memory Filesystems like pyfakefs that create a fake filesystem in memory, mimicking real file interactions.

A useful strategy is to leverage Pytest built-in fixtures like `tmp_path` and `tmpdir` that provide temporary file and directory handling for test cases.

If you’re not familiar with how to use these, we’ve written a step-by-step guide on how to use the tmp_path fixture.

### Bonus - Consider Setting Up A Pytest Daemon (Advanced)

I came across an interesting read from Discord while writing this article.

It’s titled “PYTEST DAEMON: 10X LOCAL TEST ITERATION SPEED” — which curiously peeked my attention.

The author goes on to describe how the folks at Discord were able to reduce **_the median test duration from 20 seconds down to 2 seconds!_**

That’s very impressive!

By setting up a “pytest daemon” and “hot reloading” the changed files using the `importlib.reload(module)` library, they achieved better runtimes.

In the article, they also referred to this pytest-hot-reloading plugin from James Hutchinson.

It looks pretty cool and I may write an article in the future on how to use it so don’t forget to bookmark this website.
