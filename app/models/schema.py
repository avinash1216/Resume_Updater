from typing import List, Optional
from pydantic import BaseModel, Field

class PersonalInfo(BaseModel):
    name: str = Field(..., description="The candidate's full name.")
    email: str = Field(..., description="Professional email address.")
    phone: str = Field(..., description="Phone number.")
    location: str = Field(..., description="City, State, Country (e.g., 'Hyderabad, India').")
    linkedin: Optional[str] = Field(None, description="LinkedIn profile URL or username.")
    github: Optional[str] = Field(None, description="GitHub profile URL or username.")
    website: Optional[str] = Field(None, description="Personal portfolio or website URL.")
    role: Optional[str] = Field(None, description="Professional title or role (e.g. 'Data Engineer 2').")

class Education(BaseModel):
    institution: str = Field(..., description="Name of the university or school.")
    location: str = Field(..., description="City and state/country of the institution.")
    degree: str = Field(..., description="Degree obtained (e.g., 'B.Tech in Computer Science').")
    graduation_date: str = Field(..., description="Date of graduation (e.g., 'May 2024' or 'Aug 2016 -- Jun 2020').")
    gpa: Optional[str] = Field(None, description="GPA or percentage if applicable (e.g., '8.38/10' or '93%').")

class WorkExperience(BaseModel):
    company: str = Field(..., description="Name of the employer company.")
    role: str = Field(..., description="Job title / role.")
    location: str = Field(..., description="City and state/country of employment.")
    start_date: Optional[str] = Field(None, description="Start date (e.g., 'Jul 2023').")
    end_date: Optional[str] = Field(None, description="End date or 'Present'.")
    bullets: List[str] = Field(..., description="Action-oriented bullet points describing achievements and responsibilities.")

class Project(BaseModel):
    name: str = Field(..., description="Name of the project.")
    technologies: List[str] = Field(..., description="Technologies, languages, and frameworks used in the project.")
    link: Optional[str] = Field(None, description="URL to repository or live demo.")
    bullets: List[str] = Field(..., description="Bullet points describing the project features, challenges, and outcomes.")

class SkillGroup(BaseModel):
    category: str = Field(..., description="Category of skills (e.g., 'Programming Languages', 'APIs & Frameworks').")
    skills: List[str] = Field(..., description="List of skills under this category.")

class Resume(BaseModel):
    personal_info: PersonalInfo = Field(..., description="Candidate's personal contact information.")
    education: List[Education] = Field(..., description="Education history, ordered from most recent to oldest.")
    experience: List[WorkExperience] = Field(..., description="Work history, ordered from most recent to oldest.")
    projects: List[Project] = Field(..., description="Notable projects done by the candidate.")
    skills: List[SkillGroup] = Field(..., description="Grouped technical skills.")
    summary: Optional[str] = Field(None, description="A brief professional summary or objective statement.")
    personal_skills: Optional[List[str]] = Field(None, description="List of soft/personal skills (e.g., ['Team collaboration', 'Adaptability']).")
    interests: Optional[List[str]] = Field(None, description="List of personal interests (e.g., ['Exploring emerging technologies', 'Travelling']).")
