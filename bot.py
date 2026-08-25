import os, json, random, textwrap, requests, time, asyncio, urllib.parse, re
from PIL import Image
# FIX for Pillow 10 + MoviePy bug
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS

from PIL import ImageDraw, ImageFont
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
import edge_tts
from google import genai

API_KEY = os.environ.get("GEMINI_API_KEY")
YT_CLIENT_ID = os.environ.get("YOUTUBE_CLIENT_ID")
YT_CLIENT_SECRET = os.environ.get("YOUTUBE_CLIENT_SECRET")
YT_REFRESH_TOKEN = os.environ.get("YOUTUBE_REFRESH_TOKEN")

client = genai.Client(api_key=API_KEY) if API_KEY else None
VOICE = "en-US-GuyNeural" # soft cute male

def get_story():
    topics = ["Lion and Turtle best friends save forest","Honest woodcutter golden axe","Greedy crow learns sharing","Little turtle never gives up race","Kind girl helps injured lion cub"]
    topic = random.choice(topics)
    prompt = f"Write 500 word kids moral story about: {topic}. Title first line. Then 6 paragraphs each 3 sentences. Simple English dialogues. Happy ending. Moral at end."
    MODELS = ["gemini-2.5-flash","gemini-2.5-pro","gemini-2.0-flash","gemini-1.5-flash"]
    text = None
    for m in MODELS:
        try:
            r = client.models.generate_content(model=m, contents=prompt)
            text = r.text.strip()
            if len(text) > 300: break
        except Exception as e:
            print(f"Fail {m}: {e}"); time.sleep(1)
    if not text or len(text) < 300:
        text = "Title: Brave Turtle and Lion\nOnce Timmy turtle met Leo lion. Leo was sad alone. Timmy said I will be friend. They played. Fire came in forest. They helped all animals with water. All cheered. Moral: Friendship is great." * 5

    title = topic
    try:
        if "Title:" in text:
            t = text.split("Title:")[1].split("\n")[0].replace("*","").strip()[:80]
            if len(t)>4: title = t
    except: pass
    paras = [p.strip() for p in re.split(r'\n\s*\n', text) if len(p.strip())>20]
    if len(paras) < 6:
        sents = re.split(r'(?<=[.!?])\s+', text)
        chunk = max(2, len(sents)//6)
        paras = [" ".join(sents[i:i+chunk]) for i in range(0, len(sents), chunk)][:6]
    while len(paras)<6: paras.append(paras[-1])
    paras = paras[:6]
    return title, paras, " ".join(paras)

async def make_voice(text, out="voice.mp3"):
    clean = text.replace("Moral:", "And the moral is,")
    comm = edge_tts.Communicate(clean, VOICE, rate="-8%", pitch="+1Hz")
    await comm.save(out)

def download_image(prompt, path):
    safe = urllib.parse.quote(f"cute pixar 3d cartoon {prompt}, kids storybook, vibrant, happy animals, forest")
    url = f"https://image.pollinations.ai/prompt/{safe}?width=1080&height=1920&nologo=true&seed={random.randint(0,9999999)}"
    try:
        r = requests.get(url, timeout=40)
        if r.status_code==200 and len(r.content)>8000:
            open(path,'wb').write(r.content)
            return True
    except Exception as e:
        print(f"Img fail {e}")
    return False

def make_video_pro(paras, title):
    asyncio.run(make_voice(" ".join(paras)))
    audio = AudioFileClip("voice.mp3")
    print(f"Audio {audio.duration:.1f}s")
    if audio.duration < 50:
        asyncio.run(make_voice(" ".join(paras) + " " + paras[-1], "voice.mp3"))
        audio = AudioFileClip("voice.mp3")

    per_scene = audio.duration / len(paras)
    clips = []
    for i, para in enumerate(paras):
        img_path = f"img_{i}.jpg"
        ok = download_image(para[:120], img_path)
        if not ok:
            Image.new('RGB',(1080,1920),(255,230,100)).save(img_path)
        # add text overlay - no zoom to avoid ANTIALIAS bug
        try:
            base = Image.open(img_path).convert('RGBA').resize((1080,1920))
            txt = Image.new('RGBA',(1080,1920),(0,0,0,0))
            d = ImageDraw.Draw(txt)
            try:
                f_big = ImageFont.truetype("DejaVuSans-Bold.ttf", 50)
                f_small = ImageFont.truetype("DejaVuSans.ttf", 36)
            except:
                f_big = ImageFont.load_default()
                f_small = ImageFont.load_default()
            d.rectangle([(0,1280),(1080,1920)], fill=(0,0,0,170))
            if i==0:
                wt = "\n".join(textwrap.wrap(title.upper(), 18))
                d.multiline_text((50,80), wt, font=f_big, fill=(255,255,255), stroke_width=3, stroke_fill=(0,0,0))
            wrapped = "\n".join(textwrap.wrap(para[:200], 32))
            d.multiline_text((40,1320), wrapped, font=f_small, fill=(255,255,255), spacing=6)
            final_path = f"final_{i}.jpg"
            Image.alpha_composite(base, txt).convert('RGB').save(final_path)
            clip = ImageClip(final_path).set_duration(per_scene)
        except Exception as e:
            print(f"Overlay fail {e}")
            clip = ImageClip(img_path).set_duration(per_scene)
        clips.append(clip)

    final = concatenate_videoclips(clips, method="compose").set_audio(audio)
    final.write_videofile("video.mp4", fps=24, codec='libx264', audio_codec='aac')
    return "video.mp4"

def get_token():
    if not all([YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN]): return None
    r = requests.post("https://oauth2.googleapis.com/token", data={"client_id": YT_CLIENT_ID, "client_secret": YT_CLIENT_SECRET, "refresh_token": YT_REFRESH_TOKEN, "grant_type": "refresh_token"})
    return r.json().get("access_token")

def upload(video_path, title, story_text):
    token = get_token()
    if not token: return False
    desc = story_text[:4000] + "\n\n#kidsstories #moralstories"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    body = {"snippet": {"title": (title + " | Kids Moral Story")[:95], "description": desc, "categoryId": "27"}, "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": True}}
    init = requests.post("https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status", headers=headers, data=json.dumps(body))
    print(f"Init {init.status_code}")
    url = init.headers.get("Location")
    if not url:
        print(init.text[:600]); return False
    with open(video_path, "rb") as f:
        up = requests.put(url, data=f, headers={"Content-Type":"video/*"})
    print(f"Upload {up.status_code}")
    print(up.text[:400])
    return up.status_code in [200,201]

if __name__ == "__main__":
    title, paras, full_text = get_story()
    vp = make_video_pro(paras, title)
    upload(vp, title, full_text)
