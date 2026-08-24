import os, json, random, textwrap, requests
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont
from gtts import gTTS
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
YT_CLIENT_ID = os.environ.get("YT_CLIENT_ID")
YT_CLIENT_SECRET = os.environ.get("YT_CLIENT_SECRET")
YT_REFRESH_TOKEN = os.environ.get("YT_REFRESH_TOKEN")

def get_story():
    topics = [
        "A student who failed in 12th but became successful later",
        "True friendship in hostel life that changed life",
        "A mother who secretly works day and night for family",
        "A boy who started from zero with no money",
        "Kindness returns when you least expect it",
        "How exam pressure made him stronger",
        "A village boy who moved to city and proved everyone wrong"
    ]
    topic = random.choice(topics)
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""
Write a 380-420 word emotional motivational story in simple English (Indian youth style) about: {topic}.

Rules:
- Start with Title: [5-8 words catchy title]
- Then Story: in 4-5 paragraphs
- Simple English, emotional, Your Friend channel style
- Add life lesson at end
- 380 words minimum (
