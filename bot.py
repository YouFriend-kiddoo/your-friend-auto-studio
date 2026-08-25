import os, json, random, textwrap, requests
from google import genai
from PIL import Image, ImageDraw, ImageFont
from gtts import gTTS
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

# FIX: Use correct env names that you added in GitHub
API_KEY = os.environ.get("GEMINI_API_KEY")
YT_CLIENT_ID = os.environ.get("YOUTUBE_CLIENT_ID")
YT_CLIENT_SECRET = os.environ.get("YOUTUBE_CLIENT_SECRET")
YT_REFRESH_TOKEN = os.environ.get("YOUTUBE_REFRESH_TOKEN")

client = genai.Client(api_key=API_KEY) if API_KEY else None

def get_story():
    topics = [
        "The Lion and Turtle who became best friends and helped forest",
        "Honest woodcutter and magical golden axe",
        "Greedy crow who learned to share",
        "Little turtle who never gave up in race",
        "Kind girl who helped injured lion"
    ]
    topic = random.choice(topics)
    prompt = f"Write 350 word cute kids moral story for 5-10 year old about: {topic}. Format: Title: short cute title with emoji. Story: very simple English, fun dialogues, happy ending, clear Moral: at end. 300+ words."
    # FIX: Correct model name
    response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
    text = response.text.strip()
    title = topic.title()
    story = text
    if "Title:" in text:
        try:
            t = text.split("Title:")[1].split("\n")[0].strip().replace("*","")[:80]
            if len(t)>5: title = t
            if "Story:" in text: story = text.split("Story:")[-1].strip()
        except: pass
    return title, story

def make_images(story, title):
    imgs=[]
    colors = [(255,230,100), (180,220,255), (200,255,200), (255,180,180), (220,180,255), (255,220,180)]
    words = story.split()
    chunk = max(1, len(words)//6)
    parts = [" ".join(words[i:i+chunk]) for i in range(0, len(words), chunk)][:6]
    while len(parts)<6: parts.append(parts[-1])
    for i, part in enumerate(parts):
        img = Image.new('RGB', (1080,1920), colors[i % len(colors)])
        d = ImageDraw.Draw(img)
        try: font_big = ImageFont.truetype("DejaVuSans-Bold.ttf", 58)
        except: font_big = ImageFont.load_default()
        try: font_small = ImageFont.truetype("DejaVuSans.ttf", 44)
        except: font_small = ImageFont.load_default()
        if i==0:
            wt = "\n".join(textwrap.wrap(title.upper(), 16))
            d.multiline_text((80, 700), wt, font=font_big, fill=(50,30,0), spacing=12)
            d.text((80, 1150), "KIDS MORAL STORY", fill=(200,0,80), font=font_big)
            d.text((80, 1240), "Your Friend", fill=(0,100,50), font=font_big)
        else:
            wrapped = "\n".join(textwrap.wrap(part, 28))
            bbox = d.multiline_textbbox((0,0), wrapped, font=font_small)
            y = 960 - (bbox[3]-bbox[1])//2
            d.multiline_text((84, y+4), wrapped, font=font_small, fill=(0,0,0), spacing=14, align="center")
            d.multiline_text((80, y), wrapped, font=font_small, fill=(60,30,0), spacing=14, align="center")
        img.save(f"img_{i}.jpg", quality=95)
        imgs.append(f"img_{i}.jpg")
    return imgs

def make_video(imgs, story_text):
    gTTS(text=story_text[:4000], lang='en', tld='co.uk', slow=False).save("voice.mp3")
    audio = AudioFileClip("voice.mp3")
    dur = audio.duration / len(imgs)
    clips = [ImageClip(im).set_duration(dur) for im in imgs]
    final = concatenate_videoclips(clips, method="compose").set_audio(audio)
    final.write_videofile("video.mp4", fps=24, codec='libx264', audio_codec='aac')
    return "video.mp4"

def get_token():
    print(f"Checking creds: ID exists={bool(YT_CLIENT_ID)} SECRET={bool(YT_CLIENT_SECRET)} REFRESH={bool(YT_REFRESH_TOKEN)}")
    if not all([YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN]):
        print("MISSING ENV"); return None
    r = requests.post("https://oauth2.googleapis.com/token", data={"client_id": YT_CLIENT_ID, "client_secret": YT_CLIENT_SECRET, "refresh_token": YT_REFRESH_TOKEN, "grant_type": "refresh_token"})
    print("Token response:", r.text[:500])
    return r.json().get("access_token")

def upload(video_path, title, story):
    token = get_token()
    if not token:
        print("No token"); return False
    desc = story[:4500] + "\n\nMoral: Always be kind!\n#kidsstories #moralstories #yourfriend #bedtimestories"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    body = {"snippet": {"title": (title + " | Kids Moral Story")[:95], "description": desc, "categoryId": "27", "tags": ["kids moral stories", "bedtime stories", "your friend"]}, "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": True}}
    init = requests.post("https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status", headers=headers, data=json.dumps(body))
    url = init.headers.get("Location")
    if not url:
        print("Init failed:", init.text); return False
    with open(video_path, "rb") as f:
        up = requests.put(url, data=f, headers={"Content-Type":"video/*"})
    print("Upload status:", up.status_code, up.text[:500])
    return up.status_code in [200,201]

if __name__ == "__main__":
    title, story = get_story()
    print("Title:", title)
    imgs = make_images(story, title)
    vp = make_video(imgs, story)
    upload(vp, title, story)
