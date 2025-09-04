# from datetime import datetime
# from typing import Optional
# from pydantic import BaseModel, EmailStr, ConfigDict

# # from models.enrollment import Enrollment
# from schemas.course import CourseRead


# class EnrollmentResponse(BaseModel):
#     id: int
#     first_name: str
#     last_name: str
#     created_at: datetime
#     email: EmailStr
#     phone_number: Optional[str] = None
#     is_approved: bool
#     course_id: int
#     user_id: Optional[int] = None

#     model_config = ConfigDict(from_attributes=True)


# class EnrollmentCreate(BaseModel):
#     first_name: str
#     last_name: str
#     email: EmailStr
#     phone_number: Optional[str]
#     course_id: int



# class EnrollmentUpdate(BaseModel):
#     first_name: str
#     last_name: str
#     email: EmailStr
#     phone_number: str
#     course_id: int
#     user_id: Optional[int] = None



# class EnrollmentPartialUpdate(BaseModel):
#     first_name: Optional[str] = None
#     last_name: Optional[str] = None
#     email: Optional[EmailStr] = None
#     phone_number: Optional[str] = None
#     course_id: Optional[int] = None
#     user_id: Optional[int] = None