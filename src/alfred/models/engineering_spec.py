# src/alfred/models/engineering_spec.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class ReviewerStatus(BaseModel):
    reviewer: str
    status: str
    notes: Optional[str] = None


class SuccessMetrics(BaseModel):
    product_perspective: str
    engineering_perspective: str


class Requirement(BaseModel):
    story: str  # "As a user, I want to..."


class ApiDetails(BaseModel):
    name_and_method: str
    description: str


class DataStorageField(BaseModel):
    field_name: str
    is_required: bool
    data_type: str
    description: str
    example: str


class ABTestTreatment(BaseModel):
    treatment_name: str
    description: str


class ABTest(BaseModel):
    trial_name: str
    control: str
    treatments: List[ABTestTreatment]


class EngineeringSpec(BaseModel):
    project_name: str
    overview: str
    review_status: List[ReviewerStatus] = Field(default_factory=list)
    definition_of_success: SuccessMetrics
    glossary: Optional[Dict[str, str]] = Field(default_factory=dict)

    functional_requirements: List[Requirement] = Field(default_factory=list)
    non_functional_requirements: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)

    # Design Section
    major_design_considerations: str
    architecture_diagrams: Optional[str] = None
    api_changes: List[ApiDetails] = Field(default_factory=list)
    api_usage_estimates: Optional[str] = None
    event_flows: Optional[str] = None
    frontend_updates: Optional[str] = None
    data_storage: List[DataStorageField] = Field(default_factory=list)
    auth_details: Optional[str] = None
    resiliency_plan: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)
    dependents: List[str] = Field(default_factory=list)

    # Observability Section
    failure_scenarios: str
    logging_plan: str
    metrics_plan: str
    monitoring_plan: str

    # Testing Section
    testing_approach: str
    new_technologies_considered: Optional[str] = None

    # Rollout Section
    rollout_plan: str
    release_milestones: str
    ab_testing: List[ABTest] = Field(default_factory=list)

    alternatives_considered: Optional[str] = None
    misc_considerations: Optional[str] = None
