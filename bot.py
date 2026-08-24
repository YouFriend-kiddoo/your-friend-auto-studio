import os, json, random, textwrap, requests
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont
from gtts import gTTS
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

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
        "How exam pressure made him stronger"
    ]
    topic = random.choice(topics)
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = "Write 380 to 420 word emotional motivational story in simple Indian youth English about: " + topic + ". Start with Title: then Story: 4 paragraphs plus life lesson. Minimum 380 words."
    res = model.generate_content(prompt)
    text = res.text.strip()
    title = topic.title()
    story = text
    if "Title:" in text:
        try:
            t = text.split("Title:")[1].split("\n")[0].strip()
            if len(t) > 5:
                title = t[:90]
            if "Story:" in text:
                story = text.split("Story:")[-1].strip()
        except:
            pass
    if len(story.split()) < 300:
        story = story + " " + story
    return title, story

def make_images(story):
    imgs = []
    words = story.split()
    chunk_size = max(1, len(words)//6)
    chunks = [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)][:6]
    while len(chunks) < 6:
        chunks.append(chunks[-1])
    for i, part in enumerate(chunks):
        img = Image.new('RGB', (1080,1920), (18,18,40))
        d = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", 48)
        except:
            try:
                font = ImageFont.truetype("DejaVuSans.ttf", 48)
            except:
                font = ImageFont.load_default()
        wrapped = "\n".join(textwrap.wrap(part, 30))
        bbox = d.multiline_textbbox((0,0), wrapped, font=font)
        h = bbox
