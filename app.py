import streamlit as st
import instaloader
import os
import time
import random
import json
import http.cookiejar
from datetime import datetime
from pathlib import Path

# --- CONFIGURACIÓN ---
BASE_DIR = Path("descargas_instagram")
LOG_FILE = "posts_descargados.log"
QUOTA_FILE = "cuota_diaria.json"
COOKIE_FILE = "instagram.com_cookies.txt" # El archivo de la extensión
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
            dirname_pattern="{target}"
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

    def inyectar_cookies_txt(self):
        """Lee el archivo .txt de la extensión e inyecta las cookies en Instaloader."""
        if not os.path.exists(COOKIE_FILE):
            st.error(f"No se encontró el archivo {COOKIE_FILE}")
            return False
        
        try:
            cj = http.cookiejar.MozillaCookieJar(COOKIE_FILE)
            cj.load(ignore_discard=True, ignore_expires=True)
            self.L.context._session.cookies.update(cj)
            
            # Validar si las cookies funcionan intentando obtener el perfil propio
            self.L.test_login() 
            return True
        except Exception as e:
            st.error(f"Error al procesar cookies: {e}")
            return False

    def descargar_colecciones(self):
        try:
            profile = instaloader.Profile.from_username(self.L.context, self.username)
            st.success(f"Sesión validada para: {self.username}")

            for post in profile.get_saved_posts():
                if self.daily_count >= MAX_FILES_PER_DAY:
                    st.error("Límite diario alcanzado.")
                    break

                if post.shortcode in self.processed_ids:
                    continue

                if self.post_count > 0 and self.post_count % 100 == 0:
                    espera = random.randint(300, 420)
                    st.warning(f"Pausa antideteción: {espera}s...")
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
                    st.write(f"📥 [{post.owner_username}] +{n_items} (Hoy: {self.daily_count})")
                except Exception as e:
                    st.error(f"Error en post: {e}")
                    time.sleep(5)

        except Exception as e:
            st.error(f"Error de sesión: {e}. ¿Estás logueado en el navegador?")

# --- UI ---
st.title("IG Downloader: Edición Cookies Directas")
st.info(f"Asegúrate de que '{COOKIE_FILE}' esté en la carpeta del script.")

user = st.text_input("Tu nombre de usuario de Instagram")

if st.button("Iniciar con Cookies.txt"):
    if user:
        downloader = IGDownloader(user)
        if downloader.inyectar_cookies_txt():
            downloader.descargar_colecciones()
        else:
            st.warning("Fallo al inyectar cookies. Revisa el archivo .txt")