from pydantic import BaseModel, conint

class AdmissionInput(BaseModel):
    gre_score: int
    toefl_score: int
    university_rating: int
    sop: float
    lor: float
    cgpa: float
    research: conint(ge=0, le=1) 

class BatchAdmissionInput(BaseModel):
    predictions: list[AdmissionInput]
