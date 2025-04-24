from pydantic import BaseModel


class CreateMatch(BaseModel):
    when: str
    where: str
    language: str
    # name: Optional[str]
