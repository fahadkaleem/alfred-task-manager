# Engineering Specification Creation

You are about to transform a Product Requirements Document (PRD) into a comprehensive Engineering Specification.

## Task ID: {{ additional_context.task_id }}

## Product Requirements Document

```
{{ additional_context.prd_content }}
```

## Your Objective

Analyze the PRD above and create a structured Engineering Specification that will serve as the foundation for implementation. Your specification should be detailed enough for engineers to understand the scope, approach, and technical requirements.

## Required Specification Structure

Create an EngineeringSpec with the following fields:

### Basic Information
- **project_name**: Clear, descriptive name for the project
- **overview**: High-level summary of what this project accomplishes
- **review_status**: Leave empty initially (will be filled during reviews)

### Success Metrics
- **definition_of_success**: Object containing:
  - `product_perspective`: How success is measured from product/user standpoint
  - `engineering_perspective`: Technical success criteria

### Requirements
- **functional_requirements**: List of Requirement objects, each with a `story` field (e.g., "As a user, I want to...")
- **non_functional_requirements**: List of strings for performance, scalability, security requirements
- **assumptions**: List of assumptions being made
- **glossary**: Dictionary of technical terms and their definitions

### Design Section
- **major_design_considerations**: Key architectural decisions and trade-offs
- **architecture_diagrams**: Text description or links to diagrams
- **api_changes**: List of ApiDetails objects, each with:
  - `name_and_method`: e.g., "GET /api/users"
  - `description`: What the API does
- **api_usage_estimates**: Expected load and usage patterns
- **event_flows**: Description of event-driven workflows if applicable
- **frontend_updates**: UI/UX changes required
- **data_storage**: List of DataStorageField objects, each with:
  - `field_name`: Name of the field
  - `is_required`: Boolean
  - `data_type`: Type of data
  - `description`: What the field stores
  - `example`: Example value
- **auth_details**: Authentication/authorization requirements
- **resiliency_plan**: How the system handles failures
- **dependencies**: External services or libraries this depends on
- **dependents**: Services that will depend on this

### Observability
- **failure_scenarios**: What could go wrong and how to detect it
- **logging_plan**: What to log and when
- **metrics_plan**: Key metrics to track
- **monitoring_plan**: Alerts and dashboards needed

### Testing & Rollout
- **testing_approach**: Unit, integration, E2E testing strategy
- **rollout_plan**: How to deploy safely
- **release_milestones**: Key milestones and timeline
- **ab_testing**: List of A/B tests if applicable

### Additional Considerations
- **new_technologies_considered**: Any new tech being introduced
- **alternatives_considered**: Other approaches that were evaluated
- **misc_considerations**: Any other important notes

## Guidelines

- Be comprehensive but concise
- Focus on clarity and completeness
- Consider operational aspects from day one
- Think about failure modes and recovery
- Ensure all fields are thoughtfully populated

Call `submit_work` with your completed EngineeringSpec.