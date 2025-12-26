import streamlit as st
import instaloader
import os
import time
import random
import json
from datetime import datetime
from pathlib import Path

# --- CONFIGURACIÓN ESTRATÉGICA ---
BASE_DIR = Path("descargas_instagram")
LOG_FILE = "posts_descargados.log"
QUOTA_FILE = "cuota_diaria.json"
MAX_FILES_PER_DAY = 400  # Límite conservador para evitar baneo

if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR)

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
            with open(LOG_FILE, "r") as f:
                return set(line.strip() for line in f)
        return set()

    def _registrar_post(self, post_id):
        with open(LOG_FILE, "a") as f:
            f.write(f"{post_id}\n")
        self.processed_ids.add(post_id)

    def _cargar_cuota(self):
        hoy = datetime.now().strftime("%Y-%m-%d")
        if os.path.exists(QUOTA_FILE):
            with open(QUOTA_FILE, "r") as f:
                data = json.load(f)
                if data.get("fecha") == hoy:
                    return data.get("cantidad", 0)
        return 0

    def _actualizar_cuota(self, n):
        hoy = datetime.now().strftime("%Y-%m-%d")
        self.daily_count += n
        with open(QUOTA_FILE, "w") as f:
            json.dump({"fecha": hoy, "cantidad": self.daily_count}, f)

    def cargar_sesion_inyectada(self):
        try:
            self.L.load_session_from_file(self.username)
            return True
        except Exception:
            return False

    def descargar_colecciones(self):
        try:
            profile = instaloader.Profile.from_username(self.L.context, self.username)
            st.info(f"Cuota hoy: {self.daily_count}/{MAX_FILES_PER_DAY} archivos.")

            for post in profile.get_saved_posts():
                # 1. Verificar límite diario
                if self.daily_count >= MAX_FILES_PER_DAY:
                    st.error("⚠️ LÍMITE DIARIO ALCANZADO. Deteniendo para proteger tu cuenta.")
                    break

                # 2. Saltar si ya se descargó
                if post.shortcode in self.processed_ids:
                    continue

                # 3. Pausa aleatoria cada 100 posts
                if self.post_count > 0 and self.post_count % 100 == 0:
                    espera = random.randint(300, 420)
                    st.warning(f"Simulando comportamiento humano... Pausa de {espera}s.")
                    time.sleep(espera)

                # 4. Proceso de descarga
                target_path = BASE_DIR / post.owner_username
                n_items = post.mediacount if post.typename == 'GraphSidecar' else 1
                
                # Verificar que no superaremos la cuota con este post
                if self.daily_count + n_items > MAX_FILES_PER_DAY:
                    st.warning("El siguiente post excede la cuota diaria. Finalizando.")
                    break

                try:
                    self.L.download_post(post, target=str(target_path))
                    self._registrar_post(post.shortcode)
                    self._actualizar_cuota(n_items)
                    self.total_files_session += n_items
                    self.post_count += 1
                    
                    st.write(f"📥 {self.post_count}. [{post.owner_username}] +{n_items} (Total hoy: {self.daily_count})")
                except Exception as e:
                    st.error(f"Error en post {post.shortcode}: {e}")
                    time.sleep(5) # Pausa breve ante error

        except Exception as e:
            st.error(f"Fallo crítico: {e}")

# --- UI STREAMLIT ---
st.title("Asesor Brutal: Scraper Seguro")

user = st.text_input("Usuario de Instagram")

if st.button("Iniciar Extracción"):
    if user:
        downloader = IGDownloader(user)
        if downloader.cargar_sesion_inyectada():
            downloader.descargar_colecciones()
            st.metric("Descargados en esta sesión", downloader.total_files_session)
        else:
            st.error("No se encontró el archivo de sesión. Ejecuta 'instaloader -l tu_usuario' primero.")
    else:
        st.error("Usuario requerido.")