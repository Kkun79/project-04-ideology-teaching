from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime


@dataclass
class Textbook:
   id: str
   name: str
   author: str
   publisher: str
   year: str
   isbn: str = ""
   description: str = ""
   file_path: str = ""


@dataclass
class Courseware:
   id: str
   title: str
   chapter: str
   description: str = ""
   file_path: str = ""
   created_at: str = ""


@dataclass
class Syllabus:
   id: str
   title: str
   semester: str
   total_hours: int = 0
   content: str = ""
   file_path: str = ""


@dataclass
class Reference:
   id: str
   title: str
   author: str
   publisher: str
   year: str
   isbn: str = ""
   description: str = ""


@dataclass
class CurrentPolitics:
   id: str
   title: str
   source: str
   date: str
   summary: str
   url: str = ""
   tags: list = field(default_factory=list)
   content: str = ""


@dataclass
class Case:
   id: str
   title: str
   category: str
   era: str
   summary: str
   content: str = ""
   tags: list = field(default_factory=list)
   source: str = ""


@dataclass
class KeyTerm:
   id: str
   term: str
   proposed_time: str
   meaning: str
   significance: str
   source_publication: str
   url: str = ""
   related_terms: list = field(default_factory=list)


@dataclass
class StudyTourPlan:
   id: str
   title: str
   destination: str
   duration: str
   objectives: str
   itinerary: str = ""
   budget: str = ""
   notes: str = ""
   ai_generated: bool = False


@dataclass
class ScenarioScript:
   id: str
   title: str
   type: str  # "情景剧" or "演讲稿"
   theme: str
   characters: str = ""
   content: str = ""
   notes: str = ""
   ai_generated: bool = False


@dataclass
class ExhibitionExhibit:
   id: str
   title: str
   era: str
   description: str
   dialogue: str = ""
   image_url: str = ""
   order: int = 0
