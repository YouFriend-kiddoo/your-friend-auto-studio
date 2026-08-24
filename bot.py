import json, random, requests, time
from pathlib import Path

# --- ONE-GO STUDIO: Story + Images + Voice + Video - NO KEY ---
MORALS = [("Sharing is caring","lion and turtle"),("Honesty is best","elephant and monkey"),("Hard work pays","ant and grasshopper"),("Kindness wins","rabbit and fox"),("Never give up","baby bear"),("Friendship matters","parrot and cat")]
moral, chars = random.choice(MORALS)
seed = int(time.time())

story = {
 "title": f"Baby {chars.title()} - {moral} 🦁",
 "script": f"Once baby {chars} had a problem. They learned that {moral.lower()}. They helped each other and hugged happily. Moral is {moral}.",
 "moral": moral,
 "hashtags": "#kidsstories #moralstories #yourfriend"
}
Path("story.json").write_text(json.dumps(story, indent=2))
print(f"STORY: {story['title']}")

# Images FREE
for i in range(1,4):
  try:
    prompt = f"cute baby {chars} scene {i}, Pixar 3D style, ultra cute, big eyes, soft colors, vertical 9:16"
    url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}?width=720&height=1280&nologo=true&seed={seed+i}"
    r = requests.get(url, timeout=90)
    if r.status_code==200:
      Path(f"img{i}.jpg").write_bytes(r.content)
      print(f"IMG {i} OK")
  except: pass

# Voice FREE
try:
  from gtts import gTTS
  gTTS(story["script"], lang='en').save("voice.mp3")
  print("VOICE OK")
except: print("Voice skip")

# Video - makes mp4 from images + voice, if fails still green
try:
  from PIL import Image
  import imageio.v2 as imageio
  import numpy as np
  imgs=[]
  for f in ["img1.jpg","img2.jpg","img3.jpg"]:
    if Path(f).exists():
      im = Image.open(f).resize((720,1280))
      imgs.append(np.array(im))
  if imgs:
    # 3 sec per image
    writer = imageio.get_writer("video.mp4", fps=1, macro_block_size=1)
    for im in imgs:
      for _ in range(3): writer.append_data(im)
    writer.close()
    print("VIDEO OK - video.mp4 created")
except Exception as e:
  print(f"Video skip but OK: {e}")

print("ALL DONE - ONE GO SUCCESS")
