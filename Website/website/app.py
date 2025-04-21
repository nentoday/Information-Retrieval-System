import mysql.connector
import requests
import time
import re
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Apollo99!",
    database="cyberleninka"
)

# DeepL API details
api_key = ''
url = 'https://api-free.deepl.com/v2/translate'

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/search")
def search():
    keyword = request.args.get("q")
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT DISTINCT id, title, article_text FROM cyberleninka_articles WHERE article_text LIKE %s", (f"%{keyword}%",))
    results = cursor.fetchall()
    return jsonify(results)


# Split text into chunks of ~300 characters
def split_text(text, max_length=300):
    words = text.split()
    chunks = []
    current_chunk = []

    for word in words:
        if len(" ".join(current_chunk + [word])) > max_length:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
        else:
            current_chunk.append(word)

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks

def clean_chunk(text):
    # Remove HTML tags (optional, depending on your content)
    text = re.sub(r'<[^>]+>', '', text)

    # Replace problematic characters and condense whitespace
    text = text.replace('\n', ' ').replace('\r', ' ')
    text = re.sub(r'\s+', ' ', text).strip()

    return text

# Retry a single chunk if it fails
def translate_chunk_with_retry(chunk, retries=2, delay=1):
    cleaned = clean_chunk(chunk)

    for attempt in range(retries):
        try:
            response = requests.post(url, data={
                'auth_key': api_key,
                'text': cleaned,
                'source_lang': "RU",
                'target_lang': "EN"
            })

            if response.status_code == 200:
                result = response.json()
                return result['translations'][0]['text']
            else:
                print(f"❌ Retry {attempt+1} failed - HTTP {response.status_code}")
                print("Response:", response.text)
        except Exception as e:
            print(f"💥 Retry {attempt+1} error: {e}")

        time.sleep(delay)

    print("⚠️ Returning original chunk as fallback.")
    return chunk  # fallback

# Full translation function for full article or title
def translate_text(text, source_lang="RU", target_lang="EN"):
    if not api_key:
        print("⚠️ DeepL API key is not set.")
        return text, 0

    chunks = split_text(text)
    print(f"🧩 Translating text in {len(chunks)} chunks...")

    translated_parts = []
    fallback_count = 0

    for i, chunk in enumerate(chunks):
        print(f"🔄 Translating chunk {i+1}/{len(chunks)}...")

        translated = translate_chunk_with_retry(chunk)
        if translated.strip() == chunk.strip():
            fallback_count += 1
            print(f"⚠️ Chunk {i+1} fallback used (untranslated).")

        translated_parts.append(translated)

    final_result = " ".join(translated_parts)
    print(f"✅ Translation complete. Final length: {len(final_result)} chars. Fallbacks: {fallback_count}")
    return final_result, fallback_count

@app.route("/translate", methods=["POST"])
def translate_article():
    data = request.get_json()
    title = data["title"]
    article_text = data["text"]

    translated_title = translate_text(title)
    translated_text = translate_text(article_text)

    return jsonify({
        "translated_title": translated_title,
        "translated_text": translated_text
    })

@app.route("/article/<int:article_id>")
def article_detail(article_id):
    lang = request.args.get("lang", "original")

    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM cyberleninka_articles WHERE id = %s", (article_id,))
    article = cursor.fetchone()

    if article:
        fallback_chunks = 0  # default

        if lang == "en":
            article["title"], _ = translate_text(article["title"])
            article["article_text"], fallback_chunks = translate_text(article["article_text"])
        
        return render_template("article.html", article=article, lang=lang, fallback_chunks=fallback_chunks)

    return "Article not found", 404



if __name__ == "__main__":
    app.run(debug=True)
