import argparse
import asyncio
import os
import nest_asyncio
from dotenv import load_dotenv
from llama_index.core import Settings
from llama_index.core import  SimpleDirectoryReader, ServiceContext, SummaryIndex
from llama_index.llms.nvidia import NVIDIA
from llama_index.embeddings.nvidia import NVIDIAEmbedding

from llama_index.core.workflow.retry_policy import ConstantDelayRetryPolicy
    
from llama_index.core.workflow import (
    Event,
    StartEvent,
    StopEvent,
    Workflow,
    step,
)
from llama_index.utils.workflow import (
    draw_all_possible_flows,
    draw_most_recent_execution,
)

from llama_index.core import PromptTemplate
from llama_index.core.program import LLMTextCompletionProgram
from llama_index.core.response_synthesizers import SimpleSummarize

from nemoguardrails import LLMRails, RailsConfig
from llama_index.core.output_parsers import PydanticOutputParser

from image_gen import (generate_image, base64_to_imagefile, create_pdf, pdf_to_image)
from video_gen import (save_audio, save_audio_video, save_video)
from utils import (write_file, read_file, has_file, save_url_data, read_story_json, has_prompts, parse_prompt, get_full_story_with_title)

from events import (StoryEvent, ChildrenStoryEvent, PromptEvent, PDFEvent, RawStoryEvent, StorySummaryEvent, BookImageEvent, AudioEvent)
from models import (ChildrenStory, ChildrenStoryPrompt)
from prompts import STORY_JSON_PROMPT, STORY_GENERATE_IMAGE_PROMPT, SAFE_STORY_PROMPT, EXTRACT_SUMMARIZE_STORY_PROMPT


MODEL_NAME = 'meta/llama3-70b-instruct'
EMBED_MODEL_NAME = 'NV-Embed-QA'
DATA_PATH = './data'
IMAGE_PATH = 'image'
AUDIO_PATH = 'audio'
VIDEO_PATH = 'video'
RAW_STORY_FILE = 'raw_story.txt'
STORY_JSON_FILE = 'story.json'
STORY_PDF_FILE = 'story.pdf'
TITLE_PROMPT_FILE = 'title_prompt.txt'
TITLE_JPEG_FILE = 'title.jpg'
VIDEO_NAME = 'story_video.mp4'

class ChildrenStoryGenerationWorkflow(Workflow):
    test_mode = False
    create_pdf = False
    #workflow step to read story from a url and pass to next step
    #can have shortcut to descendant step if results were previously persisted
    @step
    async def read_story(self, ev: StartEvent) -> ChildrenStoryEvent|PromptEvent|PDFEvent|RawStoryEvent|BookImageEvent|StopEvent:
        #TO-DO: PDF support
        if hasattr(ev, 'pdf'):
            return StopEvent(result="PDF support is not available yet!")
        if len(ev.url) > 0: 
            save_url_data(ev.url, f'{DATA_PATH}/{RAW_STORY_FILE}')
            return RawStoryEvent(path=f'{DATA_PATH}/{RAW_STORY_FILE}')
        elif has_file(DATA_PATH, STORY_JSON_FILE) and has_file(DATA_PATH, STORY_PDF_FILE):
            story = read_story_json(f'{DATA_PATH}/{STORY_JSON_FILE}')
            return PDFEvent(story = story, path=f'{DATA_PATH}/{STORY_PDF_FILE}')
        elif has_file(DATA_PATH, STORY_JSON_FILE):
            story = read_story_json(f'{DATA_PATH}/{STORY_JSON_FILE}')
            if has_file(f'{DATA_PATH}/{IMAGE_PATH}', TITLE_JPEG_FILE):
                return BookImageEvent(story = story, path=f'{DATA_PATH}/{IMAGE_PATH}')
            elif has_prompts(DATA_PATH, story):
                return PromptEvent(path=DATA_PATH, story=story)
            else:
                return ChildrenStoryEvent(story=story)
        elif has_file(DATA_PATH, RAW_STORY_FILE):
           return RawStoryEvent(path=f'{DATA_PATH}/{RAW_STORY_FILE}')
        else :
            return StopEvent(result="{error:'Please specify url'}")

    #workflow step to summarize story 
    @step
    async def summarize_story(self, ev: RawStoryEvent) -> StorySummaryEvent:
        reader = SimpleDirectoryReader(input_files=[ev.path])
        docs = reader.load_data()
        texts = [d.text for d in docs]
        summarizer = SimpleSummarize(llm = Settings.llm)
        response = await summarizer.aget_response(EXTRACT_SUMMARIZE_STORY_PROMPT, texts)
        return StorySummaryEvent(story=str(response))
    
    #workflow step to create guardrail to ensure story generated is safe     
    @step 
    async def create_guardrail(self, ev: StorySummaryEvent) -> StoryEvent|StopEvent:
        config = RailsConfig.from_path('config')
        rails = LLMRails(config)
        template = PromptTemplate(SAFE_STORY_PROMPT)
        prompt = template.format(story=ev.story)
        res = await rails.generate_async(prompt=prompt)
        return StoryEvent(story=str(res))

    #workflow step to generate book title and pages in json structure   
    @step #(retry_policy=ConstantDelayRetryPolicy(delay=5, maximum_attempts=5))
    async def generate_json(self, ev: StoryEvent) -> ChildrenStoryEvent:
        story = ev.story
        #print(story)
        program = LLMTextCompletionProgram.from_defaults(
            output_parser=PydanticOutputParser(output_cls=ChildrenStory),
            prompt_template_str=STORY_JSON_PROMPT,
            verbose=True,
        )
        output:ChildrenStory = program(story=story)
        if self.test_mode:
            output.pages = output.pages[0:2]
        write_file(output.json(), f'{DATA_PATH}/{STORY_JSON_FILE}')
        return ChildrenStoryEvent(story=output)

    #workflow step to generate image prompt for book page
    @step #(retry_policy=ConstantDelayRetryPolicy(delay=5, maximum_attempts=20))
    async def generate_prompt(self, ev: ChildrenStoryEvent) -> PromptEvent|StopEvent:
        story = ev.story
        template = PromptTemplate(STORY_TITLE_GENERATE_IMAGE_PROMPT)
        prompt = template.format(story=get_full_story_with_title(story))

        response = Settings.llm.complete(prompt)
        write_file(response.text, f'{DATA_PATH}/{TITLE_PROMPT_FILE}')
        for page in story.pages:
            template = PromptTemplate(STORY_GENERATE_IMAGE_PROMPT)
            prompt = template.format(page = f"page_no {str(page.page_no)}", story=get_full_story_with_title(story))

            response = Settings.llm.complete(prompt)
            write_file(response.text, f'{DATA_PATH}/{str(page.page_no)}_prompt.txt')
        return PromptEvent(path=DATA_PATH, story=story)
        
    #workflow step to generate image using prompt generated in previous step    
    @step
    async def generate_image(self, ev: PromptEvent) -> BookImageEvent:
        path = ev.path
        story = ev.story
        prompt = parse_prompt(f'{DATA_PATH}/{TITLE_PROMPT_FILE}')
        out_file = f'{path}/{IMAGE_PATH}/title.jpg'
        key = os.environ["NVIDIA_API_KEY"]
        base64_to_imagefile(generate_image(prompt, key), out_file)
        
        for i in range(len(story.pages)):
            prompt = parse_prompt(f'{path}/{i+1}_prompt.txt')
            print(prompt)
            out_file = f'{path}/{IMAGE_PATH}/{i+1}.jpg'
            base64_to_imagefile(generate_image(prompt, key), out_file)
        return BookImageEvent(story = story, path=f'{path}/{IMAGE_PATH}')

    #workflow step to generate pdf by merging page contents and images generated in previous steps
    @step
    async def generate_pdf(self, ev: BookImageEvent) -> PDFEvent|StopEvent:
        create_pdf(f'{DATA_PATH}/{STORY_PDF_FILE}', ev.story, ev.path)
        if self.create_pdf:
            return StopEvent(result=f'{DATA_PATH}/{STORY_PDF_FILE}')
        else:
            return PDFEvent(story = ev.story, path=f'{DATA_PATH}/{STORY_PDF_FILE}')
    
    #workflow step to generate audio file using tts conversion
    @step
    async def generate_audio(self, ev: PDFEvent) -> AudioEvent:
        story = ev.story
        save_audio(story, f'{DATA_PATH}/{AUDIO_PATH}' )
        return AudioEvent(story=story, pdf=ev.path, path=f'{DATA_PATH}/{AUDIO_PATH}' )

    #workflow step to generate final video by merging audio and image files generated in previous steps
    @step
    async def generate_video(self, ev: AudioEvent) -> StopEvent:
        pdf_to_image(ev.pdf, f'{DATA_PATH}/{IMAGE_PATH}' )
        save_audio_video(ev.story, f'{DATA_PATH}/{IMAGE_PATH}' , ev.path, f'{DATA_PATH}/{VIDEO_PATH}' )
        save_video(len(ev.story.pages) + 1, f'{DATA_PATH}/{VIDEO_PATH}' , f'{DATA_PATH}/{VIDEO_PATH}/{VIDEO_NAME}')
        return StopEvent(result = f'{DATA_PATH}/{VIDEO_PATH}/{VIDEO_NAME}')



async def main():
    parser = argparse.ArgumentParser(description='This program generates story book')

    # Parse arguments
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-f', '--file', help='Path to the file')
    group.add_argument('-u', '--url', help='URL to the story')
    parser.add_argument('-v', '--verbose', help='Increase output verbosity', action='store_true')
    parser.add_argument('-t', '--test', help='Run in test mode', action='store_true')
    parser.add_argument('-d', '--draw', help='Run in draw mode', action='store_true')
    parser.add_argument('-p', '--pdf', help='Output mode', action='store_true')
    args = parser.parse_args()
    verbose = args.verbose
    test_mode = args.test
    create_pdf = args.pdf
    
    # Draw flow
    if args.draw:
        draw_all_possible_flows(ChildrenStoryGenerationWorkflow, filename="story_gen_workflow.html")
        return
    
    # Load environment variables from .env file
    load_dotenv()
    Settings.llm = NVIDIA(model=MODEL_NAME)
    Settings.embed_model = NVIDIAEmbedding(model=EMBED_MODEL_NAME, truncate="END")
    
    nest_asyncio.apply()
    
    w = ChildrenStoryGenerationWorkflow(timeout=600, verbose=args.verbose)
    w.test_mode = test_mode
    w.create_pdf = create_pdf
    if args.file:
        if not args.file.endswith('.pdf'):
            print("Error: file must be pdf.")
            return 
        else:    
            result = await w.run(file = args.file)
            print("############################################################\n")
            print(result)
            print("\n############################################################")
    elif args.url:
        result = await w.run(url = args.url)
        print("############################################################\n")
        print(result)
        print("\n############################################################")

if __name__ == '__main__':
    asyncio.run(main())
