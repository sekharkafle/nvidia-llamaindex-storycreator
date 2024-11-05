from pydantic import BaseModel, Field
from typing import List
    
    
class StoryPage(BaseModel):
    """Data model for a page of the story."""
    page_no: int
    content: str
    
class ChildrenStory(BaseModel):
    """Data model for a children story."""
    title: str 
    pages: List[StoryPage]

class StoryPagePrompt(BaseModel):
    """Data model to store image prompt for a book page."""
    page_no: int
    prompt: str
    
class ChildrenStoryPrompt(BaseModel):
    """Data model for a children story prompts."""
    title_prompt: str 
    prompts: List[StoryPagePrompt]