import os, json, random, requests, time
from pathlib import Path

# V2 - FULL AUTO VIDEO ENGINE - NO API KEY NEEDED
# Generates different story daily + 3 images + voice + video

MORALS = [
  ("Sharing is caring", "lion and turtle", "sharing toys"),
  ("Honesty is best", "elephant and monkey", "telling truth"),
  ("Hard work pays", "ant and grasshopper", "working hard"),
  ("Kindness wins", "rabbit and fox", "being kind"),
  ("Never give up", "little bear climbing mountain", "trying again"),
  ("Friendship matters", "parrot and cat", "helping friends"),
  ("Patience is power", "baby elephant waiting", "being patient"),
]

title_moral, chars, lesson = random.choice(MORALS)
day_seed = int(time.time() // 86400) # changes daily
random.seed(day_seed)

story = {
  "title": f"Baby {chars.title()} Learns {title_moral} 🦁✨",
  "script": f"Baby {chars} wanted to play. One day {chars.split(' and ')[0]} had a problem. {chars.split(' and ')[1]} helped with {lesson}. They learned together that {title_moral.lower()}. So they hugged and played happily. Moral: {title_moral}.",
  "moral": title_moral,
  "hashtags": "#kidsstories #moralstories #yourfriend #cartoon #kids",
  "imagePrompt1": f"cute baby {chars.split(' and ')[0]} alone sad, Pixar 3D style, soft pastel colors, vertical 9:16, ultra cute, big eyes --seed {day_seed}",
  "imagePrompt2": f"cute baby {chars.split(' and ')[1]} helping, Pixar 3D style, soft pastel colors, vertical 9:16, ultra cute --seed {day_seed+1}",
  "imagePrompt3": f"cute baby {chars} hugging happy ending, Pixar 3D style, soft pastel colors, vertical 9:16, celebration --seed {day_seed+2}"
}

# Save story.json
with open("story.json","w") as f:
    json.dump(story, f, indent=2)

print(f"Story: {story['title']}")

# --- FREE IMAGE GENERATION (No key) ---
def gen_image(prompt, filename):
    try:
        url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}?width=720&height=1280&nologo=true"
        r = requests.get(url, timeout=60)
        if r.status_code == 200:
            Path(filename).write_bytes(r.content)
            print(f"Image saved {filename}")
            return True
    except Exception as e:
        print(f"Image fail {e}")
    return False

gen_image(story["imagePrompt1"], "img1.jpg")
gen_image(story["imagePrompt2"], "img2.jpg")
gen_image(story["imagePrompt3"], "img3.jpg")

# --- FREE VOICE + VIDEO ---
try:
    from gtts import gTTS
    from PIL import Image
    # create audio
    tts = gTTS(story["script"], lang='en', slow=False)
    tts.save("voice.mp3")
    print("Voice done")

    # create video using moviepy if available
    try:
        from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip
        clips = []
        for img in ["img1.jpg","img2.jpg","img3.jpg"]:
            if Path(img).exists():
                clips.append(ImageClip(img).set_duration(4))
        if clips:
            video = concatenate_videoclips(clips, method="compose")
            if Path("voice.mp3").exists():
                audio = AudioFileClip("voice.mp3")
                video = video.set_audio(audio)
                video = video.set_duration(audio.duration + 1)
            video.write_videofile("video.mp4
