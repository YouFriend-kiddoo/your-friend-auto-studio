import json, random, requests, time
from pathlib import Path

MORALS = [
  ("Sharing is caring", "lion and turtle"),
  ("Honesty is best", "elephant and monkey"),
  ("Hard work pays", "ant and grasshopper"),
  ("Kindness wins", "rabbit and fox"),
  ("Never give up", "bear climbing"),
  ("Friendship matters", "parrot and cat"),
]

moral, chars = random.choice(MORALS)
seed = int(time.time())

story = {"title": f"Baby {chars.title()} - {moral}","script": f"Baby {chars} learned {moral.lower()}. Moral: {moral}.","moral": moral}

Path("story.json").write_text(json.dumps(story, indent=2))
print(f"Story: {story['title']}")

for i in range(1,4):
  try:
    p = f"cute baby {chars} Pixar 3D ultra cute big eyes vertical 9:16 seed {seed+i}"
    url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(p)}?width=720&height=1280&nologo=true"
    r = requests.get(url, timeout=90)
    if r.ok:
      Path(f"img{i}.jpg").write_bytes(r.content)
      print(f"img{i} OK")
  except Exception as e:
    print(e)
print("DONE")
