from pydantic import BaseModel, validator

class Config(BaseModel):
    bupt_userno: str = ''
    bupt_pwd: str = ''