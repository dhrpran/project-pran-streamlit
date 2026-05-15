from sqlalchemy import Column, Integer, String

from database import Base


class Content(Base):
    __tablename__ = "content"

    id = Column(Integer, primary_key=True, index=True)
    home_title = Column(String)
    home_text = Column(String)
    hero_image = Column(String)
    schools = Column(Integer)
    students = Column(Integer)
    districts = Column(Integer)
    activities = Column(Integer)

    def to_dict(self) -> dict:
        return {
            "home_title": self.home_title,
            "home_text": self.home_text,
            "hero_image": self.hero_image,
            "schools": self.schools,
            "students": self.students,
            "districts": self.districts,
            "activities": self.activities,
        }
