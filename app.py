class IGDownloader:
    def __init__(self, username):
        self.username = username
        self.L = instaloader.Instaloader(
            # ... (configuración previa)
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36" 
            # IMPORTANTE: Usa el User-Agent de TU navegador actual
        )