from moviepy.editor import *
import moviepy.editor as mp
from PIL import Image as pil
from pkg_resources import parse_version
from gtts import gTTS

if parse_version(pil.__version__)>=parse_version('10.0.0'):
    pil.ANTIALIAS=pil.LANCZOS

def merge_audio_video(image_path, audio_path, video_path):
    """Merges audio and video files and generates video clip

    Args:
        image_path: path of image file to be used for generating video
        audio_path: path of audio file to be used for generating video
        video_path: output video path
    """
    image = pil.open(image_path)
    audio_clip = AudioFileClip(audio_path)
    image_clip = ImageClip(image_path, duration=audio_clip.duration)
    image_clip = image_clip.resize(image.size)
    # Combine the image and audio
    video_clip = image_clip.set_audio(audio_clip)
    # Write the video to a file
    video_clip.write_videofile(video_path, fps=24, codec="libx264",temp_audiofile="temp-audio.m4a", remove_temp=True, audio_codec="aac")

def combine_videos(video_clips, output_file):
    """Combines multiple video clips into a single movie file."""

    clips = [mp.VideoFileClip(clip) for clip in video_clips]
    final_clip = mp.concatenate_videoclips(clips)
    final_clip.write_videofile(output_file, fps=24, codec="libx264",temp_audiofile="temp-audio.m4a", remove_temp=True, audio_codec="aac")


def save_video(page_count, video_path, output_file):
    """Aggregates multiple video clips and save as a single merged video"""
    video_files = [f'{video_path}/{i}.mp4' for i in range(page_count)]
    combine_videos(video_files, output_file)


def save_audio(data, audio_path):
    """Creates audio files

    Args:
        data: data with multiple texts to convert audio
        audio_path: path of audio file to be used for generating video
    """
    # Create title audio file
    title = data.title
    ff = f"{audio_path}/title.mp3"
    tts = gTTS(title, lang='en')
    tts.save(ff)
    # Create page audio file
    for page_data in data.pages:
        ff = f"{audio_path}/{page_data.page_no}.mp3"
        page_text = page_data.content.replace("'","")
        tts = gTTS(page_text, lang='en')
        tts.save(ff)

def save_audio_video(data, image_path, audio_path, video_path):
    """Merges image and audio to create video files

    Args:
        data: data with multiple page data
        image_path: image file directory
        audio_path: audio file directory
        video_path: output video path
    """
    title = data.title
    a_p = f"{audio_path}/title.mp3"
    i_p = f"{image_path}/0.png"
    v_p = f"{video_path}/0.mp4"
    merge_audio_video(i_p, a_p, v_p)
    for page_data in data.pages:
        a_p = f"{audio_path}/{page_data.page_no}.mp3"
        i_p = f"{image_path}/{page_data.page_no}.png"
        v_p = f"{video_path}/{page_data.page_no}.mp4"
        merge_audio_video(i_p, a_p, v_p)