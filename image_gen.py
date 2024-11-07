import requests
import base64
import json
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Frame
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

from PIL import Image
import fitz

def generate_image(prompt:str, key:str):
    """Generates image using StabilityAI diffusion model available as NVidia NIM API.

    Args:
        prompt: Image gen prompt
        key: NVIDIA API Key
    Returns:
        Generated image in base64 format
    """
    invoke_url = "https://ai.api.nvidia.com/v1/genai/stabilityai/stable-diffusion-3-medium"

    headers = {
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
    }
    
    payload = {
        "prompt": prompt,
        "cfg_scale": 5,
        "aspect_ratio": "16:9",
        "seed": 0,
        "steps": 50,
        "negative_prompt": ""
    }
    
    response = requests.post(invoke_url, headers=headers, json=payload)

    response.raise_for_status()
    response_body = response.json()
    #print(response_body)
    return response_body['image']

def base64_to_imagefile(data, file:str):
    """Decodes base64 encoded image and saves as an image file.
    
    Args:
        data: Base64 image
        file: output location to save file
    """
    # Extract the base64 encoded image data
    base64_image = data

    # Decode the base64 data
    image_bytes = base64.b64decode(base64_image)

    # Save the image to a file
    with open(file, "wb") as image_file:
        image_file.write(image_bytes)

def json_to_img(file:str):
    """Decodes base64 encoded image from a json file and saves as an image file.
    
    Args:
        file: output location to save file
    """
    with open(file, 'r') as f:
        # Load the JSON data 
        data = json.load(f)
        img_file = file.replace('json', 'jpg')
        base64_to_imagefile(data['image'], img_file)
        
def generate_image_stability(prompt:str, key:str, file:str):
    """Generates image using StabilityAI diffusion model.

    Args:
        prompt: Image gen prompt
        key: StabilityAI API Key
        file: output file location
    Returns:
        Generated image in base64 format
    """
    response = requests.post(
        f"https://api.stability.ai/v2beta/stable-image/generate/sd3",
        headers={
            "authorization": f"Bearer {key}",
            "accept": "image/*"
        },
        files={"none": ''},
        data={
            "prompt": prompt,
            "output_format": "jpeg",
        },
    )
    
    if response.status_code == 200:
        with open(file, 'wb') as outfile:
            outfile.write(response.content)
    else:
        raise Exception(str(response.json()))

def add_text(c, text, width, height, is_right = False):
    """Adds text to a given frame in the PDF page

    Args:
        c: PDF Canvas
        text: Text to be added
        width: width of the page
        height: height of the page
        is_right: flag to align the text to left or right side of the page
    """
    # Define the box dimensions and position
    x, y, w, h = 10, 10, 0.5 * width, 0.5*height

    # Create a Frame for the text
    #frame = Frame(x, y, w, h, showBoundary=0) 

    # Create a Paragraph style
    styles = getSampleStyleSheet()
    style = styles["Normal"]
    style.fontSize = 45
    style.fontName = "Helvetica-Bold"
    style.leading = 45 * 1.2
    style.textColor = colors.lightgrey
    # Create a Paragraph object with the text
    p = Paragraph(text, style)
    
    # Draw the paragraph on the canvas
    p.wrapOn(c, 0.5 * width, 100)
    if is_right:
        p.drawOn(c, 50, h - 50)  
    else:
        p.drawOn(c, 0.5 * width - 50, h - 50)   

def create_pdf(filename, data, img_path):
    """Creates a story PDF by combining image and text to generate pages

    Args:
        filename: output file name
        data: object of type ChildrenStory data model
        img_path: Directory where images are stored
    """
    # Open the title image and get its dimensions
    title_img = f'{img_path}/title.jpg'
    with Image.open(title_img) as img:
        width, height = img.size

    # Create a PDF canvas based on the title image size
    c = canvas.Canvas(filename, pagesize=(width, height))

    # Draw the title image on the canvas
    c.drawImage(title_img, 0, 0, width, height)
    # Add page break
    c.showPage()
    #initiate with left alignment
    right_align  = False
    #draw all pages
    for page_data in data.pages:
        #get image and text for the page
        page_img = f"{img_path}/{page_data.page_no}.jpg"
        page_text = page_data.content
        #draw image and text
        c.drawImage(page_img, 0, 0, width, height)
        add_text(c, page_text, width, height, right_align)
        #alternate left and right alignment
        right_align = not right_align
        # Add page break for the next page
        c.showPage()
    #save file
    c.save()

def pdf_to_image(pdf_path, output_folder):
    """Exports pdf pages to an image file

    Args:
        pdf_path: location of the pdf file
        output_folder: location of output images
    """
    doc = fitz.open(pdf_path)
    for page in doc:
        p = doc.load_page(page.number)
        pix = p.get_pixmap()
        pix.save(f"{output_folder}/{page.number}.png")
