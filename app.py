from flask import Flask, request, jsonify, send_from_directory, abort
from flask_cors import CORS
import yt_dlp
import os
import re
import logging

app = Flask(__name__)
CORS(app)

# Downloads qovluğunu yaradın
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Statik YouTube hesabı məlumatları (istəyə görə dəyişdirin)
STATIC_USERNAME = "bygithubapp@gmail.com"
STATIC_PASSWORD = "your_password_here"  # Güvənli saxlayın!

# Logger qurulması
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("yt_dlp_flask")

# Fayl adı üçün təhlükəsiz string generatoru
def sanitize_filename(name):
    # Sadə regex ilə təhlükəsiz fayl adı yaradılır
    return re.sub(r'[^a-zA-Z0-9_\-\. ]', '_', name)

# yt_dlp opsiyalarını qaytaran funksiya
def get_yt_dlp_options(filename_template, is_mp3=False, resolution=None):
    options = {
        "outtmpl": filename_template,
        "quiet": True,
        "username": STATIC_USERNAME,
        "password": STATIC_PASSWORD,
        "nocheckcertificate": True,  # SSL problemlərinə qarşı (istəyə bağlı)
        "noprogress": True,
        "ignoreerrors": False,
        "retries": 3,
        "fragment_retries": 3,
    }

    if is_mp3:
        options.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "320",
            }],
            "postprocessor_args": ["-ar", "44100"],
        })
    else:
        options.update({
            "format": f"bestvideo[height<={resolution}]+bestaudio/best",
            "merge_output_format": "mp4",
            "nooverwrites": True,
        })

    return options

# Ana səhifə
@app.route("/")
def index():
    return "YouTube Downloader API is running."

# MP3 yükləmə endpointi
@app.route("/download_mp3", methods=["POST"])
def download_mp3():
    url = request.form.get("url", "").strip()
    if not url:
        return jsonify({"error": "URL is required"}), 400

    ydl_opts = get_yt_dlp_options(
        os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s"),
        is_mp3=True
    )

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                raise Exception("Video info not found")

            filename = ydl.prepare_filename(info).rsplit(".", 1)[0] + ".mp3"
            safe_filename = sanitize_filename(os.path.basename(filename))
            safe_filepath = os.path.join(DOWNLOAD_DIR, safe_filename)

            # Faylın adını təhlükəsiz formada dəyişirik (əgər fərqlidirsə)
            if filename != safe_filepath:
                os.rename(filename, safe_filepath)

            logger.info(f"MP3 downloaded: {safe_filepath}")
            return jsonify({"file_url": f"/downloads/{safe_filename}"})
    except Exception as e:
        logger.error(f"MP3 download error: {e}")
        return jsonify({"error": str(e)}), 500

# MP4 yükləmə endpointi
@app.route("/download_mp4", methods=["POST"])
def download_mp4():
    url = request.form.get("url", "").strip()
    resolution = request.form.get("resolution", "").strip()

    if not url or not resolution:
        return jsonify({"error": "URL and resolution are required"}), 400

    try:
        res_int = int(resolution)
        if res_int <= 0:
            raise ValueError
    except ValueError:
        return jsonify({"error": "Invalid resolution"}), 400

    ydl_opts = get_yt_dlp_options(
        os.path.join(DOWNLOAD_DIR, f"%(title)s_{res_int}p.%(ext)s"),
        resolution=res_int
    )

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                raise Exception("Video info not found")

            filename = os.path.join(DOWNLOAD_DIR, f'{info["title"]}_{res_int}p.mp4')
            safe_filename = sanitize_filename(os.path.basename(filename))
            safe_filepath = os.path.join(DOWNLOAD_DIR, safe_filename)

            if filename != safe_filepath:
                os.rename(filename, safe_filepath)

            logger.info(f"MP4 downloaded: {safe_filepath}")
            return jsonify({"file_url": f"/downloads/{safe_filename}"})
    except Exception as e:
        logger.error(f"MP4 download error: {e}")
        return jsonify({"error": str(e)}), 500

# Yüklənmiş faylları xidmət edin
@app.route("/downloads/<path:filename>")
def download_file(filename):
    safe_filename = sanitize_filename(filename)
    file_path = os.path.join(DOWNLOAD_DIR, safe_filename)
    if not os.path.isfile(file_path):
        abort(404)
    return send_from_directory(DOWNLOAD_DIR, safe_filename, as_attachment=True)

# Serveri işə salın
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
