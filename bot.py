import os, json, random, textwrap, requests, time
from datetime import datetime
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont
from gtts import gTTS
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

# --- CONFIG ---
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
YT_CLIENT_ID = os.environ.get("YT_CLIENT_ID")
YT_CLIENT_SECRET = os.environ.get("YT_CLIENT_SECRET")
YT_REFRESH_TOKEN = os.environ.get("YT_REFRESH_TOKEN")

def get_story():
    topics = ["A student who failed but never gave up","True friendship in hostel life","A mother who secretly works hard for family","A boy who started from zero","Kindness returns in unexpected way","Exam pressure to success"]
    topic = random.choice(topics)
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""Write a 180-220 word emotional motivational story in simple English (Indian youth style) about: {topic}.
    Format:
    Title: [catchy title 5-7 words]
    Story: [story]
    Make it Your Friend channel style. No hate."""
    res = model.generate_content(prompt)
    text = res.text.strip()
    lines = text.split("\n")
    title = lines[0].replace("Title:","").replace("Story:","").strip()[:90]
    story = "\n".join(lines[1:]).replace("Title:","").replace("Story:","").strip()
    if len(title)<5: title = topic.title()
    if len(story)<100: story = text
    return title, story

def make_images(story):
    imgs=[]
    chunks = textwrap.wrap(story, 180)[:5]
    if len(chunks)<5: chunks += [chunks[-1]]*(5-len(chunks))
    for i, part in enumerate(chunks):
        img = Image.new('RGB', (1080,1920), (12,12,30))
        d = ImageDraw.Draw(img)
        try: font = ImageFont.truetype("DejaVuSans.ttf", 50)
        except: font = ImageFont.load_default()
        wrapped = "\n".join(textwrap.wrap(part, 32))
        # shadow
        d.text((82,802), wrapped, font=font, fill=(0,0,0))
        d.text((80,800), wrapped, font=font, fill=(255,255,255))
        path = f"img_{i}.jpg"
        img.save(path)
        imgs.append(path)
    return imgs

def make_video(imgs, story_text):
    gTTS(text=story_text, lang='en', slow=False).save("voice.mp3")
    audio = AudioFileClip("voice.mp3")
    dur_per = audio.duration / len(imgs)
    clips = [ImageClip(im).set_duration(dur_per).resize((1080,1920)) for im in imgs]
    final = concatenate_videoclips(clips).set_audio(audio)
    final.write_videofile("video.mp4", fps=24, codec='libx264', audio_codec='aac')
    return "video.mp4"

def get_access_token():
    if not all([YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN]):
        print("Missing YT secrets - video will be made but not uploaded")
        return None
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": YT_CLIENT_ID,
        "client_secret": YT_CLIENT_SECRET,
        "refresh_token": YT_REFRESH_TOKEN,
        "grant_type": "refresh_token"
    })
    print("Token response
