from pydantic import BaseModel, Field
class CoachRequest(BaseModel):
    message:str|None=Field(None,min_length=1,max_length=4000); prompt:str|None=Field(None,min_length=1,max_length=4000); course_id:str|None=None; lesson_id:str|None=None
class CoachResponse(BaseModel):
    answer:str; degraded:bool=False; remaining_quota:int|None=None
