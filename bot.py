import os, json, google.generativeai as genai
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

prompt = """
You are script writer for kids channel 'Your Friend - Kids Moral Stories'.
Characters always: cute baby lion and baby turtle.
Write ONE story. Output ONLY JSON:
{
"title": "Catchy title with emoji, under 50 chars",
"script": "30 sec simple English story for 3yr old, 70 words",
"imagePrompt1": "Pixar style, baby lion... 9:16",
"imagePrompt2": "Pixar style...",
"imagePrompt3": "Pixar style...",
"hashtags": "#kidsstories #moralstories #yourfriend",
"moral": "One line moral"
}
"""

response = model.generate_content(prompt)
text = response.text.replace("```json","").replace("```","")
data = json.loads(text)

# Save for video maker
with open("story.json","w") as f:
    f.write(json.dumps(data, indent=2))

print(f"Generated: {data['title']}")
