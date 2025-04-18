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

# Update search to include 'id'
@app.route("/search")
def search():
    keyword = request.args.get("q")
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT id, title, article_text FROM cyberleninka_articles WHERE article_text LIKE %s", (f"%{keyword}%",))
    results = cursor.fetchall()
    return jsonify(results)

# New article detail route
@app.route("/article/<int:article_id>")
def article_detail(article_id):
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM cyberleninka_articles WHERE id = %s", (article_id,))
    article = cursor.fetchone()
    if article:
        return render_template("article.html", article=article)
    return "Article not found", 404

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
