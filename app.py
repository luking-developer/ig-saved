import streamlit as st
import instaloader
import os
import time
import random
import json
import http.cookiejar
from datetime import datetime
from pathlib import Path
import tempfile

# --- CONFIGURACIÓN ESTRATÉGICA ---
BASE_DIR = Path("descargas_instagram")
LOG_FILE = "posts_descargados.log"
QUOTA_FILE = "cuota_diaria.json"
MAX_FILES_PER_DAY = 400 

if not os.path.exists(BASE_DIR): os.makedirs(BASE_DIR)

class IGDownloader:
    def __init__(self, username):
        self.username = username
        self.L = instaloader.Instaloader(
            download_videos=True,
            download_video_thumbnails=False,
            save_metadata=False,
            post_metadata_txt_pattern="",
            dirname_pattern="{target}",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        self.total_files_session = 0
        self.post_count = 0
        self.processed_ids = self._cargar_logs()
        self.daily_count = self._cargar_cuota()

    def _cargar_logs(self):
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f: return set(line.strip() for line in f)
        return set()

    def _cargar_cuota(self):
        hoy = datetime.now().strftime("%Y-%m-%d")
        if os.path.exists(QUOTA_FILE):
            with open(QUOTA_FILE, "r") as f:
                data = json.load(f)
                if data.get("fecha") == hoy: return data.get("cantidad", 0)
        return 0

    def _actualizar_cuota(self, n):
        hoy = datetime.now().strftime("%Y-%m-%d")
        self.daily_count += n
        with open(QUOTA_FILE, "w") as f:
            json.dump({"fecha": hoy, "cantidad": self.daily_count}, f)

    def inyectar_cookies(self, cookie_file_path):
        try:
            cj = http.cookiejar.MozillaCookieJar(cookie_file_path)
            cj.load(ignore_discard=True, ignore_expires=True)
            self.L.context._session.cookies.update(cj)
            
            # --- REFUERZO DE SEGURIDAD ---
            # Extraemos el csrftoken de las cookies cargadas para los headers
            csrf_token = None
            for cookie in cj:
                if cookie.name == 'csrftoken':
                    csrf_token = cookie.value
                    break
            
            if csrf_token:
                # Forzamos el header que Instagram exige en GraphQL
                self.L.context._session.headers.update({
                    'x-csrftoken': csrf_token,
                    'referer': 'https://www.instagram.com/',
                    'x-ig-app-id': '936619743392459' # ID estándar de la web de IG
                })
            
            # Validamos no solo la conexión, sino la identidad
            try:
                username_check = self.L.test_login()
                if not username_check or username_check != self.username:
                    st.error(f"Sesión inválida. Se esperaba a {self.username} pero se detectó a {username_check}")
                    return False
                return True
            except Exception:
                st.error("Instagram rechazó la sesión. Las cookies han expirado o son insuficientes.")
                return False

        except Exception as e:
            st.error(f"Error procesando el archivo: {e}")
            return False

    def descargar_colecciones(self):
        try:
            profile = instaloader.Profile.from_username(self.L.context, self.username)
            st.success(f"Sesión validada para: {self.username}")

            for post in profile.get_saved_posts():
                if self.daily_count >= MAX_FILES_PER_DAY:
                    st.error("LÍMITE DIARIO ALCANZADO. Abortando para proteger la cuenta.")
                    break

                if post.shortcode in self.processed_ids:
                    continue

                if self.post_count > 0 and self.post_count % 100 == 0:
                    espera = random.randint(300, 420)
                    st.warning(f"Protocolo de seguridad: Pausa de {espera}s...")
                    time.sleep(espera)

                target_path = BASE_DIR / post.owner_username
                n_items = post.mediacount if post.typename == 'GraphSidecar' else 1
                
                if self.daily_count + n_items > MAX_FILES_PER_DAY: break

                try:
                    self.L.download_post(post, target=str(target_path))
                    with open(LOG_FILE, "a") as f: f.write(f"{post.shortcode}\n")
                    self.processed_ids.add(post.shortcode)
                    self._actualizar_cuota(n_items)
                    self.total_files_session += n_items
                    self.post_count += 1
                    st.write(f"📥 [{post.owner_username}] +{n_items} items (Total hoy: {self.daily_count})")
                except Exception as e:
                    st.error(f"Error en post {post.shortcode}: {e}")
                    time.sleep(5)

        except Exception as e:
            st.error(f"Error de sesión: {e}")

# --- INTERFAZ STREAMLIT ---
st.set_page_config(page_title="IG Deep Scraper", page_icon="🕵️")
st.title("🕵️ IG Saved Downloader (Cookie Edition)")

user = st.text_input("Tu nombre de usuario de Instagram")

# Lógica de carga de archivos
cookie_source = None
DEFAULT_COOKIE_PATH = "instagram.com_cookies.txt"

if os.path.exists(DEFAULT_COOKIE_PATH):
    st.info(f"✅ Archivo '{DEFAULT_COOKIE_PATH}' detectado localmente.")
    cookie_source = DEFAULT_COOKIE_PATH
else:
    st.warning("No se detectó archivo de cookies en la carpeta.")
    uploaded_file = st.file_uploader("Sube tu archivo 'instagram.com_cookies.txt'", type=["txt"])
    if uploaded_file is not None:
        # Guardar temporalmente el archivo subido
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            cookie_source = tmp_file.name

if st.button("Iniciar Extracción Inteligente"):
    if not user:
        st.error("Debes ingresar tu nombre de usuario.")
    elif not cookie_source:
        st.error("Debes subir un archivo de cookies válido.")
    else:
        downloader = IGDownloader(user)
        if downloader.inyectar_cookies(cookie_source):
            downloader.descargar_colecciones()
            st.balloons()