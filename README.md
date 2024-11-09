# StoryGen App - Make fun and engaging children's story
StoryGen App takes a text story and creates a fun and engaging picture book in PDF or video format for small children in minutes. 

## Requirements

Python 3.9, 3.10 or 3.11.


## Installation

1. Clone the repo and `cd` into the code directory
```bash
➜  git clone https://github.com/sekharkafle/storycreator.git
➜  cd storycreator
```
2. Setup virtual environment (optional):
```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file in your code root directory and set NVIDIA API Key:
```bash
NVIDIA_API_KEY=...
```
## Usage

To run the program, use below command:

```
python3 storygen.py --url https://en.wikipedia.org/wiki/The_Sparrow%27s_Lost_Bean
```
After successful execution, the program will generate video output file ./data/video/story_video.mp4 .
To generate the book in pdf format, pass --pdf option in the command.
```
python3 storygen.py --url https://en.wikipedia.org/wiki/The_Sparrow%27s_Lost_Bean --pdf
```
The output file will be at ./data/story.pdf .

## Overview


## Technology 

## TODO 

