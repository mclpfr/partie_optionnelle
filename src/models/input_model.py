from pydantic import BaseModel
from typing import List

class AdmissionInput(BaseModel):
    gre_score: int 
    toefl_score: int 
    university_rating: int
    sop: float 
    lor: float 
    cgpa: float 
    research: int 

class BatchAdmissionInput(BaseModel):
    predictions: List[AdmissionInput]