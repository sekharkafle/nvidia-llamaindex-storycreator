from models import ChildrenStory
from llama_index.core.workflow import Event
class PromptEvent(Event):
    path: str
    story: ChildrenStory

class RawStoryEvent(Event):
    path: str

class StoryEvent(Event):
    story: str

class StorySummaryEvent(Event):
    story: str

class ChildrenStoryEvent(Event):
    story: ChildrenStory

class BookImageEvent(Event):
    path: str
    story: ChildrenStory
    
class PDFEvent(Event):
    path: str
    story: ChildrenStory

class AudioEvent(Event):
    path: str
    story: ChildrenStory
    pdf: str
