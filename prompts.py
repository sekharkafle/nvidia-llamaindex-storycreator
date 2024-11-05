STORY_JSON_PROMPT = """
Generate a title and list of pages for the story provided.
Make sure full story is included in the response.
Make sure each page is 1 sentence long.
Respond with a valid JSON. Do not add any sentence before or after the JSON object.
  \n\n Original story: '''{story}'''.
"""


STORY_GENERATE_IMAGE_PROMPT = """
You are an AI agent that generates prompts that can be passed to image generation multimodal LLM.
You are given a children's book with a title and page content of the book.
Your job is to create prompt to generate fun and engaging pictures to be used for {page} in the book.
Make sure name/character used is fully described in each page. 
e.g. Instead of saying Annie is walking slowly, say Annie the crocodile is walking slowly. 
Do not return a content or any other details. Only return the prompt text.
Similarly instead of saying John is curious, say John, 5 year old boy, is curious.
  \n\n Here is the story: \n
  ''{story}'''
"""

EXTRACT_SUMMARIZE_STORY_PROMPT = "extract the story from documents"

SAFE_STORY_PROMPT = """
Rewrite story to make it safe for children. 
\n\n Story: ''{story}'''
"""