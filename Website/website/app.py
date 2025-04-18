from flask import Flask, request, jsonify, render_template
import mysql.connector
import requests

app = Flask(__name__)

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="yourpassword",
    database="cyberleninka"
)

def translate_text(text, source_lang="ru", target_lang="en"):
    try:
        response = requests.post(
            "https://libretranslate.de/translate",
            headers={"Content-Type": "application/json"},
            json={
                "q": text,
                "source": source_lang,
                "target": target_lang,
                "format": "text"
            }
        )
        return response.json().get("translatedText", text)
    except Exception:
        return text

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/search")
def search():
    keyword = request.args.get("q")
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT title, article_text  FROM cyberleninka_articles WHERE article_text LIKE %s", (f"%{keyword}%",))
    results = cursor.fetchall()
    return jsonify(results)

@app.route("/translate", methods=["POST"])
def translate():
    data = request.get_json()
    title = data.get("title", "")
    text = data.get("text", "")
    translated_title = translate_text(title)
    translated_text = translate_text(text)
    return jsonify({
        "translated_title": translated_title,
        "translated_text": translated_text
    })

if __name__ == "__main__":
    app.run(debug=True)
