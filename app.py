from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import yt_dlp
import os

app = Flask(__name__)
CORS(app)

# Downloads qovluğunu yaradın
os.makedirs("downloads", exist_ok=True)

# Ana səhifəni xidmət edin
@app.route("/")
def index():
    return send_file("index.html")

# yt_dlp üçün opsiyalar yaradan funksiya (username/password əlavə edildi)
def get_yt_dlp_options(filename_template, is_mp3=False, resolution=None, username=None, password=None):
    options = {
        "outtmpl": filename_template,
        "quiet": True,
    }

    # İstifadəçi adı və şifrə varsa, əlavə edin
    if username and password:
        options["username"] = username
        options["password"] = password

    if is_mp3:
        options["format"] = "bestaudio/best"
        options["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "320",
        }]
    else:
        options["format"] = f"bestvideo[height<={resolution}]+bestaudio/best"
        options["merge_output_format"] = "mp4"
        options["nooverwrites"] = True

    return options

# MP3 yükləmə endpointi (username/password formdan alınır)
@app.route("/download_mp3", methods=["POST"])
def download_mp3():
    url = request.form.get("url")
    username = request.form.get("username")
    password = request.form.get("password")

    if not url:
        return jsonify({"error": "URL is required"}), 400

    ydl_opts = get_yt_dlp_options(
        "downloads/%(title)s.%(ext)s",
        is_mp3=True,
        username=username,
        password=password
    )

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info).rsplit(".", 1)[0] + ".mp3"
            return jsonify({"file_url": "/" + filename})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# MP4 yükləmə endpointi (username/password formdan alınır)
@app.route("/download_mp4", methods=["POST"])
def download_mp4():
    url = request.form.get("url")
    resolution = request.form.get("resolution")
    username = request.form.get("username")
    password = request.form.get("password")

    if not url or not resolution:
        return jsonify({"error": "URL and resolution are required"}), 400

    try:
        res_int = int(resolution)
    except ValueError:
        return jsonify({"error": "Invalid resolution"}), 400

    ydl_opts = get_yt_dlp_options(
        f"downloads/%(title)s_{res_int}p.%(ext)s",
        resolution=res_int,
        username=username,
        password=password
    )

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = f'downloads/{info["title"]}_{res_int}p.mp4'
            return jsonify({"file_url": "/" + filename})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Yüklənmiş faylları xidmət edin
@app.route("/downloads/<path:filename>")
def download_file(filename):
    return send_from_directory("downloads", filename, as_attachment=True)

# Serveri işə salın
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
