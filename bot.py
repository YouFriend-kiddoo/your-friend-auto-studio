import os, json, random, textwrap, requests, time, asyncio, re
from PIL import Image
if not hasattr(Image, 'ANTIALIAS'): Image.ANTIALIAS = Image.LANCZOS
from PIL import ImageDraw, ImageFont
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip
import edge_tts
from google import genai

API_KEY = os.environ.get("GEMINI_API_KEY")
PEXELS_KEY = os.environ.get("PEXELS_API_KEY")
YT_CLIENT_ID = os.environ.get("YOUTUBE_CLIENT_ID")
YT_CLIENT_SECRET = os.environ.get("YOUTUBE_CLIENT_SECRET")
YT_REFRESH_TOKEN = os.environ.get("YOUTUBE_REFRESH_TOKEN")

client = genai.Client(api_key=API_KEY)
VOICE = "en-US-GuyNeural"

def get_story():
    prompt = """
    Write a 650 word LONG kids moral story. Must be 600+ words, not short.
    Topic: Choose one cute real animal friendship story: lion and turtle, elephant and dog, monkey and parrot.
    Structure:
    Title: 6 words max
    Paragraph 1: Introduction of characters (100 words)
    Paragraph 2: Problem arises (100 words)
    Paragraph 3: They try to solve (100 words)
    Paragraph 4: Big adventure / climax (100 words)
    Paragraph 5: Happy ending (100 words)
    Paragraph 6: Moral
    Each paragraph must be 90-120 words. Simple English, lots of dialogues like "Let's go!", "We can do it!".
    Do NOT repeat sentences. Make it long.
    """
    MODELS = ["gemini-2.5-pro","gemini-2.5-flash","gemini-2.0-flash"]
    text = None
    for m in MODELS:
        try:
            r = client.models.generate_content(model=m, contents=prompt)
            text = r.text.strip()
            if len(text.split()) > 400: # ensure long
                print(f"Got {len(text.split())} words from {m}")
                break
        except Exception as e:
            print(f"Fail {m}: {e}")

    if not text or len(text.split()) < 350:
        # fallback long story manually 500 words
        text = """
        Title: Lion and Turtle Save Forest
        Leo the lion lived in a big forest. He was strong but lonely. Timmy the small turtle was slow but very clever. One day they met near the river. "Hello! Why are you sad?" asked Timmy. Leo said "I have no friends, everyone is scared of me". Timmy smiled and said "I will be your friend forever". From that day they played together everyday. They shared fruits and laughed.
        One hot summer, a big fire started in the forest. All animals ran away shouting "Fire! Fire!". Birds flew, rabbits hopped. Leo and Timmy saw the fire near the old oak tree. "We must help everyone" said Timmy bravely. Leo roared loudly "Everyone come to the river!". But the fire was spreading fast towards the baby animals trapped near the bush.
        Timmy had an idea. He said "Leo, you are strong, you can carry water from river with big leaves. I will guide the baby animals". Leo nodded. He ran to river, filled giant leaves with water. He poured water on fire again and again. Timmy slowly led the baby rabbits, squirrels out safely. It was very hard work. They were tired but did not stop. "We can do it!" shouted Timmy.
        Suddenly wind made fire bigger. All animals were scared. Leo stood in front and roared very loudly. He pushed a big tree branch to stop fire spreading. Timmy called elephant for help. Elephant came with trunk full of water. Together lion, turtle, elephant poured water for one hour. Finally fire became small and stopped. Forest was safe but smoky. Everyone coughed but was happy.
        All animals gathered and cheered "Hooray for Leo and Timmy! They are heroes". The owl gave them medals made of flowers. The monkey gave bananas. The little baby rabbits hugged Timmy. Leo was not lonely anymore, everyone wanted to be his friend now. They had a big party near river with music and dance. Timmy and Leo danced together. It was the best day in forest.
        Moral: True friendship, courage and helping others makes you a real hero.
        """

    title = "Brave Friends Story"
    try:
        if "Title:" in text:
            t = text.split("Title:")[1].split("\n")[0].replace("*","").strip()[:80]
            if len(t)>4: title = t
    except: pass

    paras = [p.strip() for p in re.split(r'\n\s*\n', text) if len(p.strip())>40][:6]
    # Ensure 6 paras
    while len(paras)<6: paras.append(paras[-1])
    full = " ".join(paras)
    print(f"Final story: {len(full.split())} words")
    return title, paras, full

def get_real_video(keyword, save_path):
    """Download REAL stock video from Pexels"""
    if not PEXELS_KEY:
        print("No PEXELS_KEY, using placeholder")
        return False
    headers = {"Authorization": PEXELS_KEY}
    try:
        url = f"https://api.pexels.com/videos/search?query={keyword}&per_page=5&orientation=portrait&size=medium"
        r = requests.get(url, headers=headers, timeout=15)
        data = r.json()
        if data.get('videos'):
            # pick random video
            vid = random.choice(data['videos'])
            # get best quality file (720p)
            file_url = None
            for f in vid['video_files']:
                if f['width'] >= 720 and f['width'] <= 1280:
                    file_url = f['link']
                    break
            if not file_url: file_url = vid['video_files'][0]['link']
            print(f"Pexels found for {keyword}: {file_url[:60]}")
            vr = requests.get(file_url, timeout=30)
            open(save_path, 'wb').write(vr.content)
            return True
    except Exception as e:
        print(f"Pexels fail {keyword}: {e}")
    return False

async def make_voice(text, out="voice.mp3"):
    clean = text.replace("Moral:", "And the moral of the story is,")
    comm = edge_tts.Communicate(clean, VOICE, rate="-5%", pitch="+1Hz")
    await comm.save(out)

def make_video_real(paras, title):
    asyncio.run(make_voice(" ".join(paras)))
    audio = AudioFileClip("voice.mp3")
    print(f"Audio duration {audio.duration:.1f}s, words {len(' '.join(paras).split())}")
    per_scene = audio.duration / len(paras)

    keywords = ["lion forest", "turtle cute", "forest fire", "animals helping", "forest celebration", "lion turtle friends"]

    clips = []
    for i, para in enumerate(paras):
        vid_path = f"clip_{i}.mp4"
        kw = keywords[i] if i < len(keywords) else "forest animals"
        ok = get_real_video(kw, vid_path)

        if not ok:
            # fallback if no key: create color
            from moviepy.editor import ColorClip
            clip = ColorClip((1080,1920), color=(100, 200, 100)).set_duration(per_scene)
        else:
            clip = VideoFileClip(vid_path).subclip(0, min(per_scene+1, 8))
            clip = clip.resize((1080,1920)).set_duration(per_scene)
            # loop if short
            if clip.duration < per_scene:
                clip = clip.loop(duration=per_scene)

        # Add text overlay as image on top
        try:
            txt_clip_path = f"text_{i}.png"
            img = Image.new('RGBA', (1080, 1920), (0,0,0,0))
            d = ImageDraw.Draw(img)
            try:
                f_big = ImageFont.truetype("DejaVuSans-Bold.ttf", 52)
                f_small = ImageFont.truetype("DejaVuSans.ttf", 38)
            except:
                f_big = ImageFont.load_default()
                f_small = ImageFont.load_default()
            d.rectangle([(0,1260),(1080,1920)], fill=(0,0,0,180))
            if i==0:
                d.multiline_text((40,60), "\n".join(textwrap.wrap(title.upper(),18)), font=f_big, fill=(255,255,255), stroke_width=4, stroke_fill=(0,0,0))
            d.multiline_text((40,1300), "\n".join(textwrap.wrap(para[:220],32)), font=f_small, fill=(255,255,255), spacing=7)
            img.save(txt_clip_path)
            from moviepy.editor import ImageClip
            txt_c = ImageClip(txt_clip_path).set_duration(per_scene)
            clip = CompositeVideoClip([clip, txt_c])
        except Exception as e:
            print(f"Text fail {e}")

        clips.append(clip)

    final = concatenate_videoclips(clips, method="compose").set_audio(audio)
    final.write_videofile("video.mp4", fps=24, codec='libx264', audio_codec='aac')
    print(f"REAL VIDEO DONE {final.duration}s")
    return "video.mp4"

def get_token():
    if not all([YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN]): return None
    r = requests.post("https://oauth2.googleapis.com/token", data={"client_id": YT_CLIENT_ID, "client_secret": YT_CLIENT_SECRET, "refresh_token": YT_REFRESH_TOKEN, "grant_type": "refresh_token"})
    return r.json().get("access_token")

def upload(vp, title, story):
    token = get_token()
    if not token: return False
    desc = story[:4000] + "\n\n#kids #moralstories #realanimals #forest"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    body = {"snippet": {"title": (title + " | Real Animal Moral Story")[:95], "description": desc, "categoryId": "27"}, "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": True}}
    init = requests.post("https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status", headers=headers, data=json.dumps(body))
    url = init.headers.get("Location")
    if not url:
        print(init.text[:600]); return False
    with open(vp, "rb") as f:
        up = requests.put(url, data=f, headers={"Content-Type":"video/*"})
    print(f"Upload {up.status_code} {up.text[:400]}")
    return up.status_code in [200,201]

if __name__ == "__main__":
    title, paras, full = get_story()
    vp = make_video_real(paras, title)
    upload(vp, title, full)
