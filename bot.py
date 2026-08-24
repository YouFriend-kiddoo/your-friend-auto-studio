import os, json

# V1 - Test version - No API key needed, generates sample story automatically
# Later we plug your real Gemini key

story = {
  "title": "Baby Lion Learns to Share 🦁",
  "script": "Baby lion had many toys. Baby turtle had none. Lion felt sad seeing turtle sad. So lion shared one toy. Turtle smiled big! Sharing makes friendship strong. Moral: Sharing is caring.",
  "imagePrompt1": "cute baby lion with many toys, Pixar 3D style, soft colors, 9:16",
  "imagePrompt2": "cute baby turtle sad with no toys, Pixar 3D style, soft colors, 9:16",
  "imagePrompt3": "baby lion sharing toy with baby turtle hugging, happy, Pixar 3D style, 9:16",
  "hashtags": "#kidsstories #moralstories #yourfriend #sharingiscaring",
  "moral": "Sharing is caring"
}

with open("story.json","w") as f:
    json.dump(story, f, indent=2)

print(f"Generated: {story['title']} - No API key needed!")
