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

# --- CONFIGURACIÓN ---
MAX_FILES_PER_DAY = 400
BASE_DIR = Path("descargas_instagram")
if not os.path.exists(BASE_DIR): os.makedirs(BASE_DIR)

class IGDownloader:
    def __init__(self, username):
        self.username = username
        # AJUSTA ESTO: Pon tu User-Agent real aquí (Búscalo en Google)
        self.ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        
        self.L = instaloader.Instaloader(
            download_videos=True,
            download_video_thumbnails=False,
            save_metadata=False,
            user_agent=self.ua
        )
        
        # Headers de "Navegador Real"
        self.L.context._session.headers.update({
            'Accept': '*/*',
            'Accept-Language': 'es-ES,es;q=0.9',
            'X-IG-App-ID': '936619743392459', # ID oficial Web IG
            'X-ASBD-ID': '129477',            # Requerido para GraphQL
            'X-IG-WWW-Claim': '0',
            'Origin': 'https://www.instagram.com',
            'Referer': 'https://www.instagram.com/',
            'X-Requested-With': 'XMLHttpRequest'
        })

    def inyectar_cookies_reforzado(self, file_path):
        try:
            cj = http.cookiejar.MozillaCookieJar(file_path)
            cj.load(ignore_discard=True, ignore_expires=True)
            self.L.context._session.cookies.update(cj)
            
            # Extraer CSRF para el Header
            csrf_token = None
            for cookie in cj:
                if cookie.name == 'csrftoken':
                    csrf_token = cookie.value
                    break
            
            if csrf_token:
                self.L.context._session.headers.update({'X-CSRFToken': csrf_token})
            else:
                st.warning("⚠️ No se encontró 'csrftoken' en las cookies. Esto podría causar el error 400.")

            # Prueba de fuego
            try:
                logged_user = self.L.test_login()
                if logged_user == self.username:
                    return True
                else:
                    st.error(f"Sesión detectada para {logged_user}, pero pediste {self.username}.")
                    return False
            except Exception as e:
                st.error(f"Instagram rechazó la sesión reforzada: {e}")
                return False
        except Exception as e:
            st.error(f"Error al leer el archivo: {e}")
            return False

    def descargar_colecciones(self):
        try:
            profile = instaloader.Profile.from_username(self.L.context, self.username)
            st.success("🔥 Sesión Blindada Iniciada.")
            
            # Aquí va el loop de descarga (con pausas de 5-7 min y límite de 400)
            # [El código del loop se mantiene igual a las versiones anteriores]
            # ... 
            st.info("Iniciando escaneo de publicaciones guardadas...")
            # (Ejecutar loop de guardados aquí)
            
        except Exception as e:
            st.error(f"Error al acceder a guardados: {e}")

# --- INTERFAZ ---
st.title("Refuerzo de Sesión GraphQL")
user = st.text_input("Usuario de Instagram")
uploaded_file = st.file_uploader("Sube instagram.com_cookies.txt", type=["txt"])

if st.button("Ejecutar con Refuerzo"):
    if user and uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
            tmp.write(uploaded_file.getvalue())
            path = tmp.name
        
        downloader = IGDownloader(user)
        if downloader.inyectar_cookies_reforzado(path):
            downloader.descargar_colecciones()
    else:
        st.error("Faltan datos.")