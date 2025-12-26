# 📸 IG Saved Content Downloader

### ⚠️ ADVERTENCIA DE SEGURIDAD
Este script es una herramienta de automatización que interactúa con la API privada de Instagram. El uso excesivo puede resultar en el bloqueo temporal o permanente de tu cuenta. Úsalo con moderación.

## 🚀 Propósito
Extractor de contenido guardado diseñado para ser invisible ante los sistemas de detección de bots, utilizando inyección de cookies y límites de cuota diaria.

---

## 📋 Requisitos de Sesión (Dos Métodos)

Para que el script funcione, necesitas un archivo de sesión. Instagram bloqueará cualquier intento de login directo con usuario/contraseña desde Streamlit.

### Método 1: Vía Navegador (Get cookies.txt LOCALLY) - RECOMENDADO
Este método es el más seguro si tienes problemas de `Checkpoint`.

1. Instala la extensión **"Get cookies.txt LOCALLY"** en tu navegador (Chrome o Edge).
2. Entra en [Instagram.com](https://www.instagram.com) y asegúrate de estar logueado.
3. Haz clic en la extensión y pulsa **"Export"** para descargar el archivo `instagram.com_cookies.txt`.
4. **Conversión:** Instaloader requiere su propio formato. Para convertir tus cookies del navegador a un archivo de sesión de Instaloader, usa este comando en tu terminal:
   ```bash
   instaloader --cookiefile instagram.com_cookies.txt -l TU_USUARIO_IG