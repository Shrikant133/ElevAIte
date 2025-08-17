from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime
from app.models.opportunity import OpportunityType, WorkMode

class OpportunityBase(BaseModel):
    title: str
    kind: OpportunityType
    location: Optional[str] = None
    mode: WorkMode = WorkMode.ONSITE
    url: Optional[HttpUrl] = None
    deadline_at: Optional[datetime] = None
    jd_text: Optional[str] = None
    skills_required: List[str] = []
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None

class OpportunityCreate(OpportunityBase):
    organization_name: str
    organization_website: Optional[str] = None

class OpportunityUpdate(BaseModel):
    title: Optional[str] = None
    location: Optional[str] = None
    mode: Optional[WorkMode] = None
    deadline_at: Optional[datetime] = None
    jd_text: Optional[str] = None
    skills_required: Optional[List[str]] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    status: Optional[str] = None

class OrganizationSchema(BaseModel):
    id: int
    name: str
    website: Optional[str]
    type: Optional[str]
    location: Optional[str]
    
    class Config:
        from_attributes = True

class OpportunitySchema(OpportunityBase):
    id: int
    organization_id: int
    organization: OrganizationSchema
    source: str
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class OpportunitySearchResult(BaseModel):
    opportunities: List[OpportunitySchema]
    total: int
    page: int
    per_page: int
    has_more: bool

class ScrapeOpportunityRequest(BaseModel):
    url: HttpUrl

class ScrapeOpportunityResponse(BaseModel):
    success: bool
    opportunity_id: Optional[int] = None
    title: Optional[str] = None
    company: Optional[str] = None
    error: Optional[str] = None