import os, json, random, textwrap, requests
from google import genai
from PIL import Image, ImageDraw, ImageFont
from gtts import gTTS
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)

YT_CLIENT_ID = os.environ.get("YT_CLIENT_ID")
YT_CLIENT_SECRET = os.environ.get("YT_CLIENT_SECRET")
YT_REFRESH_TOKEN = os.environ.get("YT_REFRESH_TOKEN")

def get_story():
    topics = [
        "A student who failed in 12th but became successful later",
        "True friendship in hostel life",
        "A mother who secretly works day and night for family",
        "A boy who started from zero with no money",
        "Kindness returns when you least expect it"
    ]
    topic = random.choice(topics)
    prompt = "Write 400 word emotional motivational story in simple Indian youth English about: " + topic + ". Title: then Story: 4 paragraphs plus lesson."
    response = client.models.generate_content(model="gemini-3.6-flash", contents=prompt)
    text = response.text.strip()
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
        story = story + " Life always teaches us. Keep going never give up."
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
            font = ImageFont.load_default()
        wrapped = "\n".join(textwrap.wrap(part, 30))
        bbox = d.multiline_textbbox((0,0), wrapped, font=font)
        h = bbox[3]-bbox[1]
        y_pos = 960 - h//2
        d.multiline_text((82, y_pos+2), wrapped, font=font, fill=(0,0,0), spacing=12, align="center")
        d.multiline_text((80, y_pos), wrapped, font=font, fill=(255,255,255), spacing=12, align="center")
        path = "img_" + str(i) + ".jpg"
        img.save(path, quality=95)
        imgs.append(path)
    return imgs

def make_video(imgs, story_text):
    gTTS(text=story_text, lang='en', tld='co.in', slow=False).save("voice.mp3")
    audio = AudioFileClip("voice.mp3")
    if audio.duration < 65:
        gTTS(text=story_text, lang='en', slow=True).save("voice2.mp3")
        audio = AudioFileClip("voice2.mp3")
    dur_per = audio.duration / len(imgs)
    clips = [ImageClip(im).set_duration(dur_per) for im in imgs]
    final = concatenate_videoclips(clips, method="compose").set_audio(audio)
    final.write_videofile("video.mp4", fps=24, codec='libx264', audio_codec='aac')
    return "video.mp4"

def get_access_token():
    if not all([YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN]):
        return None
    r = requests.post("https://oauth2.googleapis.com/token", data={"client_id": YT_CLIENT_ID, "client_secret": YT_CLIENT_SECRET, "refresh_token": YT_REFRESH_TOKEN, "grant_type": "refresh_token"})
    return r.json().get("access_token")

def upload_to_youtube(video_path, title, description):
    token = get_access_token()
    if not token:
        return False
    headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
    body = {"snippet": {"title": title, "description": description, "categoryId": "22"}, "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}}
    init = requests.post("https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status", headers=headers, data=json.dumps(body))
    upload_url = init.headers.get("Location")
    if not upload_url:
        print(init.text)
        return False
    with open(video_path, "rb") as f:
        up = requests.put(upload_url, data=f, headers={"Content-Type": "video/*"})
    print("Upload status")
    print(str(up.status_code))
    return up.status_code in [200,201]

if __name__ == "__main__":
    title, story = get_story()
    print("Title is " + title)
    imgs = make_images(story)
    video_path = make_video(imgs, story)
    desc = story + "\n\n#motivation #yourfriend"
    upload_to_youtube(video_path, title, desc)
