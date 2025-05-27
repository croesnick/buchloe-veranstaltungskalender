from datetime import date, datetime
from typing import Union
from pydantic import BaseModel, model_serializer


class Event(BaseModel):
    title: str
    start: Union[date, datetime]
    end: Union[date, datetime]
    location: str
    description: str
    url: str

    @model_serializer
    def serialize_model(self):
        return {
            "title": self.title,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "location": self.location,
            "description": self.description,
            "url": self.url,
        }
