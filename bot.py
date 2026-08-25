import os, json, random, textwrap, requests, time, urllib.parse
from google import genai
from PIL import Image, ImageDraw, ImageFont
from gtts import gTTS
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

API_KEY = os.environ.get("GEMINI_API_KEY")
YT_CLIENT_ID = os.environ.get("YOUTUBE_CLIENT_ID")
YT_CLIENT_SECRET = os.environ.get("YOUTUBE_CLIENT_SECRET")
YT_REFRESH_TOKEN = os.environ.get("YOUTUBE_REFRESH_TOKEN")

client = genai.Client(api_key=API_KEY) if API_KEY else None

def get_story():
    topics = [
        "Lion and Turtle becoming best friends helping forest",
        "Honest woodcutter and magical golden axe",
        "Greedy crow learns to share food",
        "Little turtle never gives up and wins race",
        "Kind girl helps injured baby lion"
    ]
    topic = random.choice(topics)
    prompt = f"Write 500 word cute kids moral story about: {topic}. Need Title: on first line. Then full Story: very simple English, many dialogues, fun, 450+ words, happy ending, Moral at end. For 5 year old."
    MODELS = ["gemini-2.5-flash","gemini-2.5-pro","gemini-2.0-flash","gemini-1.5-flash"]
    text = None
    for m in MODELS:
        try:
            print(f"Trying {m}")
            r = client.models.generate_content(model=m, contents=prompt)
            text = r.text.strip()
            print(f"OK {m} len {len(text)}")
            break
        except Exception as e:
            print(f"Fail {m}: {e}")
            time.sleep(2)
    if not text or len(text) < 200:
        text = "Title: The Brave Turtle and Lion\nStory: Once Timmy turtle met Leo lion. Leo was sad. Timmy said 'Why sad?'. Leo said 'No friends'. Timmy said 'I will be your friend'. They played together. One day hunter came. Timmy hid lion in bush. Hunter went away. Lion hugged turtle. They lived happily. Moral: True friendship helps always. " * 6

    title = topic
    story = text
    try:
        if "Title:" in text:
            t = text.split("Title:")[1].split("\n")[0].replace("*","").strip()[:80]
            if len(t) > 5: title = t
            if "Story:" in text: story = text.split("Story:")[-1].strip()
    except: pass
    # Make story longer for 1 min - repeat if needed
    if len(story.split()) < 130:
        story = story + " " + story
    print(f"Final story words: {len(story.split())}")
    return title, story

def download_cartoon_image(prompt, path):
    # Free AI image - Pollinations
    safe_prompt = urllib.parse.quote(f"cute cartoon kids storybook illustration, {prompt}, soft colors, 3d pixar style, happy animals, forest background")
    url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1080&height=1920&nologo=true&seed={random.randint(1,999999)}"
    try:
        print(f"Downloading image: {prompt[:40]}")
        r = requests.get(url, timeout=30)
        if r.status_code == 200 and len(r.content) > 5000:
            with open(path, 'wb') as f:
                f.write(r.content)
            return True
    except Exception as e:
        print(f"Img fail: {e}")
    return False

def make_images(story, title):
    # Split story into 6 scenes and create image prompts
    words = story.split()
    chunk = max(20, len(words)//6)
    parts = [" ".join(words[i:i+chunk]) for i in range(0, len(words), chunk)][:6]
    while len(parts) < 6: parts.append(parts[-1])

    scene_prompts = [
        f"{title}, cute baby lion and turtle as friends in forest, title card",
        f"{parts[1][:100]}, cute animals talking",
        f"{parts[2][:100]}, forest adventure",
        f"{parts[3][:100]}, animals helping each other",
        f"{parts[4][:100]}, happy celebration",
        f"{parts[5][:100]}, moral lesson, sunset happy ending"
    ]

    imgs = []
    for i, (part, sc_prompt) in enumerate(zip(parts, scene_prompts)):
        img_path = f"img_{i}.jpg"
        ok = download_cartoon_image(sc_prompt, img_path)
        if not ok:
            # fallback to color image
            img = Image.new('RGB', (1080,1920), (255,230,100))
            d = ImageDraw.Draw(img)
            try: f = ImageFont.truetype("DejaVuSans-Bold.ttf", 48)
            except: f = ImageFont.load_default()
            d.text((50,900), f"Scene {i+1}\n" + "\n".join(textwrap.wrap(part[:120], 20)), fill=(0,0,0), font=f)
            img.save(img_path)

        # Add text overlay on image
        try:
            base = Image.open(img_path).convert('RGB').resize((1080,1920))
            draw = ImageDraw.Draw(base)
            # semi-transparent box at bottom for text
            draw.rectangle([(0,1250),(1080,1920)], fill=(0,0,0,120))
            overlay = Image.new('RGBA', (1080,1920), (0,0,0,0))
            odraw = ImageDraw.Draw(overlay)
            odraw.rectangle([(0,1300),(1080,1750)], fill=(0,0,0,150))
            base = Image.alpha_composite(base.convert('RGBA'), overlay).convert('RGB')
            draw = ImageDraw.Draw(base)
            try:
                font = ImageFont.truetype("DejaVuSans.ttf", 42)
                font_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 56)
            except:
                font = ImageFont.load_default()
                font_title = ImageFont.load_default()
            if i==0:
                wt = "\n".join(textwrap.wrap(title.upper(), 18))
                draw.multiline_text((80,100), wt, font=font_title, fill=(255,255,255), stroke_width=3, stroke_fill=(0,0,0))
            else:
                wrapped = "\n".join(textwrap.wrap(part[:200], 30))
                draw.multiline_text((60,1320), wrapped, font=font, fill=(255,255,255), spacing=10)
            base.save(img_path, quality=95)
        except Exception as e:
            print(f"Overlay fail {e}")
        imgs.append(img_path)
        time.sleep(1) # avoid rate limit
    print(f"Images ready: {imgs}")
    return imgs

def make_video(imgs, story_text):
    # Make voice - full story for 60 sec
    # Use longer text - ensure 1 min
    clean = story_text[:800] # ~130 words = ~60 sec
    if len(clean.split()) < 120:
        clean = (clean + " ") * 2
    print(f"TTS words: {len(clean.split())}")
    gTTS(text=clean, lang='en', tld='co.uk', slow=False).save("voice.mp3")
    audio = AudioFileClip("voice.mp3")
    print(f"Audio duration: {audio.duration} sec")
    # Force 60 sec video - if audio short, extend image duration
    if audio.duration < 50:
        # speed fix: make audio 55 sec by setting image longer (video will be audio length)
        # add small silence by looping? we just make clips longer than audio? final will be audio length
        # So we duplicate story to make longer audio
        gTTS(text=clean + " " + clean[:400], lang='en', tld='co.uk', slow=False).save("voice.mp3")
        audio = AudioFileClip("voice.mp3")
        print(f"New audio duration: {audio.duration}")

    dur = audio.duration / len(imgs)
    print(f"Each image duration: {dur}")
    clips = [ImageClip(im).set_duration(dur) for im in imgs]
    final = concatenate_videoclips(clips, method="compose").set_audio(audio)
    final.write_videofile("video.mp4", fps=24, codec='libx264', audio_codec='aac')
    print("Video done")
    return "video.mp4"

def get_token():
    if not all([YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN]): return None
    r = requests.post("https://oauth2.googleapis.com/token", data={"client_id": YT_CLIENT_ID, "client_secret": YT_CLIENT_SECRET, "refresh_token": YT_REFRESH_TOKEN, "grant_type": "refresh_token"})
    return r.json().get("access_token")

def upload(video_path, title, story):
    token = get_token()
    if not token: return False
    desc = story[:4000] + "\n\nMoral: Kindness wins!\n#kidsstories #moralstories #cartoon #kidsvideo"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    body = {"snippet": {"title": (title + " | Kids Moral Story")[:95], "description": desc, "tags": ["kids","moral","cartoon","animals"], "categoryId": "27"}, "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": True}}
    init = requests.post("https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status", headers=headers, data=json.dumps(body))
    print(f"Init {init.status_code}")
    url = init.headers.get("Location")
    if not url:
        print(init.text[:500])
        return False
    with open(video_path, "rb") as f:
        up = requests.put(url, data=f, headers={"Content-Type":"video/*"})
    print(f"Upload {up.status_code} {up.text[:400]}")
    return up.status_code in [200,201]

if __name__ == "__main__":
    title, story = get_story()
    imgs = make_images(story, title)
    vp = make_video(imgs, story)
    upload(vp, title, story)
