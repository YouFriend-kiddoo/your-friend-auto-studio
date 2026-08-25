import os, json, random, textwrap, requests, time, asyncio, urllib.parse, re
from google import genai
from PIL import Image, ImageDraw, ImageFont

# MoviePy imports
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip
import edge_tts

API_KEY = os.environ.get("GEMINI_API_KEY")
YT_CLIENT_ID = os.environ.get("YOUTUBE_CLIENT_ID")
YT_CLIENT_SECRET = os.environ.get("YOUTUBE_CLIENT_SECRET")
YT_REFRESH_TOKEN = os.environ.get("YOUTUBE_REFRESH_TOKEN")

client = genai.Client(api_key=API_KEY) if API_KEY else None

# --- CUTE SOFT MALE VOICES - pick one ---
# Best for kids: en-US-GuyNeural (warm male), en-GB-RyanNeural (soft British male), en-US-AndrewNeural
VOICE = "en-US-GuyNeural" # <--- soft cute male, change if you want female: en-US-AnaNeural

def get_story():
    topics = [
        "Lion and Turtle become best friends and save forest from fire",
        "Honest woodcutter who returns magical golden axe",
        "Greedy crow who learns to share food with friends",
        "Little turtle who never gave up and wins big race",
        "Kind little girl who helps injured baby lion cub"
    ]
    topic = random.choice(topics)
    prompt = f"""
    Write a 550 word kids moral story for YouTube Shorts/Reels about: {topic}.
    Requirements:
    - First line Title: 5-6 words cute title with 1 emoji
    - Story: Very simple English for 5 year old, full of dialogues like "Wow!", "Let's help!".
    - Divide story into exactly 6 short paragraphs, each paragraph 2-3 sentences.
    - Each paragraph = 1 scene.
    - Happy ending.
    - Last line Moral: one line.
    - 500+ words total.
    """
    MODELS = ["gemini-2.5-flash","gemini-2.5-pro","gemini-2.0-flash","gemini-1.5-flash"]
    text = None
    for m in MODELS:
        try:
            print(f"Trying {m}")
            r = client.models.generate_content(model=m, contents=prompt)
            text = r.text.strip()
            if len(text) > 300: break
        except Exception as e:
            print(f"Fail {m}: {e}")
            time.sleep(1)
    if not text or len(text) < 300:
        text = """Title: Brave Turtle and Lion 🦁
        Once Timmy turtle saw Leo lion crying. "Why are you crying?" asked Timmy. Leo said "I have no friends."
        Timmy said "I will be your friend!". They played together all day in the forest.
        Suddenly they saw fire in forest. Animals were scared.
        Timmy said "We must help!". Leo roared and called all animals. Together they poured water.
        Fire stopped. All animals cheered "Hooray! Timmy and Leo are heroes!". They all became best friends.
        Moral: True friendship and helping others makes you a hero."""

    # Extract
    title = topic
    story = text
    try:
        if "Title:" in text:
            tline = text.split("Title:")[1].split("\n")[0].replace("*","").strip()
            if len(tline) > 4: title = tline[:80]
    except: pass

    # Get 6 paragraphs for 6 scenes
    paras = [p.strip() for p in re.split(r'\n\s*\n', text) if len(p.strip()) > 20]
    # If not 6 paras, split by sentences
    if len(paras) < 6:
        sents = re.split(r'(?<=[.!?])\s+', story)
        chunk = max(2, len(sents)//6)
        paras = [" ".join(sents[i:i+chunk]) for i in range(0, len(sents), chunk)][:6]
    while len(paras) < 6: paras.append(paras[-1])
    paras = paras[:6]

    full_story_for_voice = " ".join(paras) # for TTS
    print(f"Title: {title}")
    print(f"Scenes: {len(paras)}")
    return title, paras, full_story_for_voice

async def make_voice(text, out="voice.mp3"):
    # Perfect narration with pauses
    # Add SSML-like pauses for better flow
    clean = text.replace("Moral:", "And the moral of the story is,")
    # edge-tts with soft, cute style
    communicate = edge_tts.Communicate(clean, VOICE, rate="-5%", pitch="+2Hz")
    await communicate.save(out)
    print(f"Voice saved with {VOICE}")

def download_image(prompt, path):
    safe = urllib.parse.quote(f"cute pixar 3d cartoon style, {prompt}, kids storybook illustration, vibrant colors, soft lighting, happy, detailed forest, ultra cute")
    url = f"https://image.pollinations.ai/prompt/{safe}?width=1080&height=1920&nologo=true&seed={random.randint(0,9999999)}&enhance=true"
    try:
        print(f"IMG: {prompt[:60]}")
        r = requests.get(url, timeout=40)
        if r.status_code == 200 and len(r.content) > 8000:
            open(path,'wb').write(r.content)
            return True
    except Exception as e:
        print(f"IMG fail {e}")
    return False

def make_video_pro(paras, title):
    # 1. Make voice first to get exact duration
    asyncio.run(make_voice(" ".join(paras)))
    audio = AudioFileClip("voice.mp3")
    total_dur = audio.duration
    print(f"Total audio: {total_dur:.1f}s")
    # If still short, duplicate last para to reach 55-65 sec
    if total_dur < 50:
        extra = " ".join(paras[-2:])
        asyncio.run(make_voice(" ".join(paras) + " " + extra, "voice.mp3"))
        audio = AudioFileClip("voice.mp3")
        total_dur = audio.duration
        print(f"Extended audio: {total_dur:.1f}s")

    per_scene = total_dur / len(paras)

    clips = []
    for i, para in enumerate(paras):
        img_path = f"img_{i}.jpg"
        scene_prompt = para[:150] # use story line as image prompt
        ok = download_image(scene_prompt, img_path)
        if not ok:
            # create fallback gradient
            im = Image.new('RGB', (1080,1920), (255, 220, 120 + i*10))
            im.save(img_path)

        # Add cinematic Ken Burns zoom + text overlay
        # Create clip with zoom effect
        clip = ImageClip(img_path).set_duration(per_scene)
        # Zoom from 100% to 115% slowly (real video feel)
        clip = clip.resize(lambda t: 1 + 0.12 * t / per_scene)

        # Add text box
        try:
            base = Image.open(img_path).convert('RGBA')
            base = base.resize((1080,1920))
            txt_img = Image.new('RGBA', (1080,1920), (0,0,0,0))
            d = ImageDraw.Draw(txt_img)
            try:
                f_big = ImageFont.truetype("DejaVuSans-Bold.ttf", 52)
                f_small = ImageFont.truetype("DejaVuSans.ttf", 38)
            except:
                f_big = ImageFont.load_default()
                f_small = ImageFont.load_default()
            # bottom gradient
            d.rectangle([(0, 1280), (1080, 1920)], fill=(0,0,0,170))
            if i==0:
                wrapped_title = "\n".join(textwrap.wrap(title, 20))
                d.multiline_text((50, 80), wrapped_title, font=f_big, fill=(255,255,255), stroke_width=4, stroke_fill=(0,0,0), spacing=8)
                # subtitle
                d.text((50, 1340), para[:180], font=f_small, fill=(255,255,255))
            else:
                wrapped = "\n".join(textwrap.wrap(para[:220], 32))
                d.multiline_text((40, 1330), wrapped, font=f_small, fill=(255,255,255), spacing=8)
            # composite
            combined_path = f"final_{i}.jpg"
            Image.alpha_composite(base, txt_img).convert('RGB').save(combined_path)
            clip = ImageClip(combined_path).set_duration(per_scene)
            clip = clip.resize(lambda t: 1 + 0.10 * t / per_scene)
        except Exception as e:
            print(f"Text overlay fail {e}")

        clips.append(clip)
        time.sleep(0.8)

    final = concatenate_videoclips(clips, method="compose").set_audio(audio)
    final.write_videofile("video.mp4", fps=24, codec='libx264', audio_codec='aac')
    print("VIDEO DONE - duration %.1f" % final.duration)
    return "video.mp4"

def get_token():
    if not all([YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN]): return None
    r = requests.post("https://oauth2.googleapis.com/token", data={"client_id": YT_CLIENT_ID, "client_secret": YT_CLIENT_SECRET, "refresh_token": YT_REFRESH_TOKEN, "grant_type": "refresh_token"})
    return r.json().get("access_token")

def upload(video_path, title, story_text):
    token = get_token()
    if not token: return False
    desc = story_text[:4000] + "\n\nMoral: Be kind and help others!\n#kidsstories #moralstories #kidsvideo #cartoonstories #bedtimestories"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    body = {"snippet": {"title": (title + " | Kids Moral Story")[:95], "description": desc, "tags": ["kids","moral","cartoon"], "categoryId": "27"}, "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": True}}
    init = requests.post("https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status", headers=headers, data=json.dumps(body))
    print(f"Init {init.status_code}")
    url = init.headers.get("Location")
    if not url:
        print(init.text[:600]); return False
    with open(video_path, "rb") as f:
        up = requests.put(url, data=f, headers={"Content-Type":"video/*"})
    print(f"Upload {up.status_code}")
    return up.status_code in [200,201]

if __name__ == "__main__":
    title, paras, full_text = get_story()
    vp = make_video_pro(paras, title)
    upload(vp, title, full_text)
