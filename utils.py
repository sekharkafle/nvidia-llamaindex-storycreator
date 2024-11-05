from bs4 import BeautifulSoup
import requests
import os
from models import ChildrenStory
from pydantic_core import from_json

def write_file(content:str, file:str):
    with open(file, "w") as outfile:
        outfile.write(content)

def read_file(file:str):
    with open(file, 'r') as openfile:
        return openfile.read()


def save_url_data(url, file):
    # Fetch the HTML content
    url = url
    response = requests.get(url)
    html_content = response.content
    
    # Parse the HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extract the text from the body
    body_text = soup.body.get_text()
    
    # Optionally, clean up the text
    body_text = " ".join(body_text.split()) 
    write_file(body_text, file)

def has_file(dir_path, filename):
    """Checks if a file exists in the given directory."""
    return os.path.isfile(os.path.join(dir_path, filename))

def parse_prompt(file_name):
    read_file(file_name)
    index = prompt.find("\"")
    prompt = prompt[index+1:-1]
    return prompt

def has_prompts(path, story):
    if not has_file(path, 'title_prompt.txt'):
        return False
    for i, _ in enumerate(story.pages):
        if not has_file(path, f'{str(i)}_prompt.txt'):
            return False
    return True
    
def get_full_story_with_title(story:ChildrenStory):
    content = ''
    content = content + 'Title : ' + story.title + '\n'
    for i, page in enumerate(story.pages):
        content = content + 'Page ' + str(i) + ' : ' + page.content + '\n'
    return content
    
def get_full_story(story:ChildrenStory):
    content = ''
    for i, page in enumerate(story.pages):
        content = 'Page ' + str(i) + ' : ' + page.content + '\n'
    return content

def get_title(story:ChildrenStory):
    return story.title

def read_story_json(path:str):
    story_json = read_file(path)
    story = ChildrenStory.model_validate(from_json(story_json))
    return story