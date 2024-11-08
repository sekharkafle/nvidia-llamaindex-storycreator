from bs4 import BeautifulSoup
import requests
import os
from models import ChildrenStory
from pydantic_core import from_json
import pypdf

def write_file(content:str, file:str):
    """Writes a text file.

    Args:
        content: Text content for the file
        file: file name
    """
    with open(file, "w", encoding="utf-8") as outfile:
        outfile.write(content)

def read_file(file:str):
    """Reads a file.

    Args:
        file: file name
    Returns:
        text from the file
    """
    with open(file, 'r') as openfile:
        return openfile.read()

def read_pdf(file_path):
    """Reads pdf file.

    Args:
        file_path: full path and name of the epdf file
    Returns:
        text from the pdf file
    """
    with open(file_path, "rb") as pdf_file:
        pdf_reader = pypdf.PdfReader(pdf_file)
        num_pages = len(pdf_reader.pages)

        text = ""
        for page_num in range(num_pages):
            page = pdf_reader.pages[page_num]
            text += page.extract_text()
    return text
    
def save_url_data(url, file):
    """Gets html document from a URL and saves content as a local file

    Args:
        url: url
        file: local file path and name
    Returns:
        Generated image in base64 format
    """
    
    # Fetch the HTML content
    url = url
    response = requests.get(url)
    html_content = response.content
    
    # Parse the HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extract the text from the body
    body_text = soup.body.get_text()
    
    # Save the text
    body_text = " ".join(body_text.split()) 
    write_file(body_text, file)

def has_file(dir_path, filename):
    """Checks if a file exists in the given directory."""
    return os.path.isfile(os.path.join(dir_path, filename))

def parse_prompt(file_name):
    """Reads a file and extracts prompt stored within double quotes."""
    prompt = read_file(file_name)
    index = prompt.find("\"")
    prompt = prompt[index+1:-1]
    return prompt

def has_prompts(path, story):
    """Checks if prompts were previously stored."""
    if not has_file(path, 'title_prompt.txt'):
        return False
    for i, _ in enumerate(story.pages):
        if not has_file(path, f'{str(i)}_prompt.txt'):
            return False
    return True
    
def get_full_story_with_title(story:ChildrenStory):
    """Returns full story to be passed in prompt to LLM.

    Args:
        story: ChildrenStory object
    Returns:
        text form of the story object with title
    """
    content = ''
    content = content + 'Title : ' + story.title + '\n'
    for i, page in enumerate(story.pages):
        content = content + 'Page ' + str(i) + ' : ' + page.content + '\n'
    return content
    
def get_full_story(story:ChildrenStory):
    """Returns full story to be passed in prompt to LLM.

    Args:
        story: ChildrenStory object
    Returns:
        text form of the story object without title
    """
    content = ''
    for i, page in enumerate(story.pages):
        content = 'Page ' + str(i) + ' : ' + page.content + '\n'
    return content

def get_title(story:ChildrenStory):
    """Returns title """
    return story.title

def read_story_json(path:str):
    """Converts json file to ChildrenStory object """
    story_json = read_file(path)
    story = ChildrenStory.model_validate(from_json(story_json))
    return story