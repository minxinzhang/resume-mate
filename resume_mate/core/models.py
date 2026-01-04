from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class BaseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class Profile(BaseSchema):
    network: str
    username: str
    url: HttpUrl | None = None


class Location(BaseSchema):
    address: str | None = None
    postal_code: str | None = Field(None, alias="postalCode")
    city: str
    country_code: str | None = Field(None, alias="countryCode")
    region: str | None = None


class Basics(BaseSchema):
    name: str
    label: str | None = None
    email: str
    phone: str | None = None
    url: HttpUrl | None = None
    summary: str | None = None
    location: Location | None = None
    profiles: list[Profile] = Field(default_factory=list)


class WorkExperience(BaseSchema):
    name: str = Field(..., description="Company name")
    position: str
    url: HttpUrl | None = None
    start_date: str = Field(..., alias="startDate")
    end_date: str | None = Field(default=None, alias="endDate")
    summary: str | None = None
    highlights: list[str] = Field(default_factory=list)
    tech_stack: list[str] = Field(default_factory=list, alias="techStack")


class Project(BaseSchema):
    name: str
    description: str | None = None
    highlights: list[str] = Field(default_factory=list)
    tech_stack: list[str] = Field(default_factory=list, alias="techStack")
    url: HttpUrl | None = None
    start_date: str | None = Field(None, alias="startDate")
    end_date: str | None = Field(None, alias="endDate")


class Education(BaseSchema):
    institution: str
    url: HttpUrl | None = None
    area: str
    study_type: str = Field(..., alias="studyType")
    start_date: str = Field(..., alias="startDate")
    end_date: str | None = Field(None, alias="endDate")
    score: str | None = None
    courses: list[str] = Field(default_factory=list)


class Skill(BaseSchema):
    name: str
    level: str | None = None
    keywords: list[str] = Field(default_factory=list)


class MasterProfile(BaseSchema):
    basics: Basics
    work: list[WorkExperience] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    skills: list[Skill] = Field(default_factory=list)
