import mysql.connector
import requests
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="newpassword",
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
    cursor.execute("SELECT DISTINCT title, article_text FROM cyberleninka_articles WHERE article_text LIKE %s", (f"%{keyword}%",))
    results = cursor.fetchall()
    return jsonify(results)


def split_text(text, max_length=500):
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


def translate_text(text, source_lang="RU", target_lang="EN"):
    translated_parts = []
    chunks = split_text(text)

    for chunk in chunks:
        try:
            data = {
                'auth_key': api_key,
                'text': chunk,
                'source_lang': source_lang,
                'target_lang': target_lang
            }
            response = requests.post(url, data=data)

            if response.status_code != 200:
                print(f"Translation HTTP error {response.status_code}: {response.text}")
                translated_parts.append(chunk)
                continue

            try:
                result = response.json()
                translated_parts.append(result['translations'][0]['text'])
            except ValueError:
                print("Invalid JSON response:", response.text)
                translated_parts.append(chunk)

        except Exception as e:
            print("Translation error:", e)
            translated_parts.append(chunk)

    return " ".join(translated_parts)


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


if __name__ == "__main__":
    app.run(debug=True)
