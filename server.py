import http.server
import socketserver
import json
import os
import boto3
import base64
import random
import traceback

PORT = 8000
REGION = 'us-east-1'
PROFILE = 'kiro-arcade'

# --- Ranking file storage ---
RANKINGS_DIR = os.path.join(os.path.dirname(__file__), 'rankings')
os.makedirs(RANKINGS_DIR, exist_ok=True)

RANKING_KEYS = {
    'flappy':     'flappyKiroRanking',
    'fruit-ninja':'fruitNinjaRanking',
    'rps':        'rpsRanking',
    'ghost-dodge':'ghostDodgeRanking',
}

def ranking_path(game):
    return os.path.join(RANKINGS_DIR, f'{game}.json')

def load_ranking_file(game):
    try:
        with open(ranking_path(game), 'r') as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_ranking_file(game, entries):
    with open(ranking_path(game), 'w') as f:
        json.dump(entries[:5], f, indent=2)

def reset_ranking_file(game):
    save_ranking_file(game, [])

session = None
bedrock = None
polly = None

def _get_bedrock():
    global session, bedrock
    if bedrock:
        return bedrock
    try:
        session = boto3.Session(profile_name=PROFILE, region_name=REGION)
        bedrock = session.client('bedrock-runtime', region_name=REGION)
        return bedrock
    except Exception as e:
        print(f"[AWS] Bedrock unavailable: {e}")
        return None

def _get_polly():
    global polly
    if polly:
        return polly
    try:
        s = boto3.Session(profile_name=PROFILE, region_name=REGION)
        polly = s.client('polly', region_name=REGION)
        return polly
    except Exception as e:
        print(f"[AWS] Polly unavailable: {e}")
        return None

# --- AI Comment Generation (Nova Lite) ---
# IMPORTANT: All prompts must generate CLEAN, FAMILY-FRIENDLY content. No swearing, no insults.
COMMENT_BASE_RULE = "REGLA IMPORTANTE: El comentario debe ser respetuoso, sin palabrotas ni insultos. Puedes usar 'bro' de forma amigable."
COMMENT_BASE_RULE_EN = "IMPORTANT RULE: The comment must be respectful, no swearing or insults. You can use 'bro' in a friendly way."

COMMENT_THEMES = {
    'flappy': {
        'es': [
            f"Eres un narrador gamer amigable que dice 'bro' mucho. {COMMENT_BASE_RULE} UNA frase corta y positiva (max 12 palabras). Score: {{score}}. Evento: {{event}}. Solo la frase, sin comillas.",
            f"Eres un fantasma simpático animando al jugador. {COMMENT_BASE_RULE} UNA frase corta motivadora (max 12 palabras). Score: {{score}}. Evento: {{event}}. Solo la frase.",
            f"Eres un robot adorable que aprende sobre videojuegos. {COMMENT_BASE_RULE} UNA frase tierna y graciosa (max 12 palabras). Score: {{score}}. Evento: {{event}}. Solo la frase.",
        ],
        'en': [
            f"You're a friendly gamer narrator who says 'bro' a lot. {COMMENT_BASE_RULE_EN} ONE short positive phrase (max 12 words). Score: {{score}}. Event: {{event}}. Just the phrase, no quotes.",
            f"You're a cute ghost cheering the player on. {COMMENT_BASE_RULE_EN} ONE short motivating phrase (max 12 words). Score: {{score}}. Event: {{event}}. Just the phrase.",
            f"You're an adorable robot learning about video games. {COMMENT_BASE_RULE_EN} ONE cute funny phrase (max 12 words). Score: {{score}}. Event: {{event}}. Just the phrase.",
        ]
    },
    'ghost-dodge': {
        'es': [
            f"Eres un fantasmita simpático narrando un juego de esquivar. {COMMENT_BASE_RULE} UNA frase corta y divertida (max 12 palabras). Score: {{score}}. Evento: {{event}}. Solo la frase, sin comillas.",
            f"Eres un narrador deportivo entusiasta pero educado. {COMMENT_BASE_RULE} UNA frase corta emocionante (max 12 palabras). Score: {{score}}. Evento: {{event}}. Solo la frase.",
            f"Eres un pingüino animador que dice 'bro' y anima al jugador. {COMMENT_BASE_RULE} UNA frase positiva (max 12 palabras). Score: {{score}}. Evento: {{event}}. Solo la frase.",
        ],
        'en': [
            f"You're a friendly ghost narrating a dodge game. {COMMENT_BASE_RULE_EN} ONE short fun phrase (max 12 words). Score: {{score}}. Event: {{event}}. Just the phrase, no quotes.",
            f"You're an enthusiastic but polite sports narrator. {COMMENT_BASE_RULE_EN} ONE short exciting phrase (max 12 words). Score: {{score}}. Event: {{event}}. Just the phrase.",
            f"You're a cheerful penguin who says 'bro' and cheers the player. {COMMENT_BASE_RULE_EN} ONE positive phrase (max 12 words). Score: {{score}}. Event: {{event}}. Just the phrase.",
        ]
    },
    'fruit-ninja': {
        'es': [
            f"Eres un ninja amigable comentando cortes de fruta. {COMMENT_BASE_RULE} UNA frase corta y divertida (max 12 palabras), usa 'bro'. Score: {{score}}. Evento: {{event}}. Solo la frase, sin comillas.",
            f"Eres un chef entusiasta que narra cortes de fruta como si fuera un show de cocina. {COMMENT_BASE_RULE} UNA frase positiva (max 12 palabras). Score: {{score}}. Evento: {{event}}. Solo la frase.",
            f"Eres un gato samurái educado que comenta la técnica de corte. {COMMENT_BASE_RULE} UNA frase graciosa (max 12 palabras). Score: {{score}}. Evento: {{event}}. Solo la frase.",
        ],
        'en': [
            f"You're a friendly ninja commenting on fruit slicing. {COMMENT_BASE_RULE_EN} ONE short fun phrase (max 12 words), use 'bro'. Score: {{score}}. Event: {{event}}. Just the phrase, no quotes.",
            f"You're an enthusiastic chef narrating fruit cuts like a cooking show. {COMMENT_BASE_RULE_EN} ONE positive phrase (max 12 words). Score: {{score}}. Event: {{event}}. Just the phrase.",
            f"You're a polite samurai cat commenting on slicing technique. {COMMENT_BASE_RULE_EN} ONE funny phrase (max 12 words). Score: {{score}}. Event: {{event}}. Just the phrase.",
        ]
    },
    'rps': {
        'es': [
            f"Eres un narrador amigable de piedra papel tijera que dice 'bro'. {COMMENT_BASE_RULE} UNA frase corta y divertida (max 12 palabras). Score: {{score}}. Evento: {{event}}. Solo la frase, sin comillas.",
            f"Eres un mago simpático que predice jugadas con humor. {COMMENT_BASE_RULE} UNA frase graciosa (max 12 palabras). Score: {{score}}. Evento: {{event}}. Solo la frase.",
            f"Eres un emoji viviente que reacciona de forma exagerada pero educada. {COMMENT_BASE_RULE} UNA frase positiva (max 12 palabras). Score: {{score}}. Evento: {{event}}. Solo la frase.",
        ],
        'en': [
            f"You're a friendly rock paper scissors narrator who says 'bro'. {COMMENT_BASE_RULE_EN} ONE short fun phrase (max 12 words). Score: {{score}}. Event: {{event}}. Just the phrase, no quotes.",
            f"You're a friendly magician who predicts plays with humor. {COMMENT_BASE_RULE_EN} ONE funny phrase (max 12 words). Score: {{score}}. Event: {{event}}. Just the phrase.",
            f"You're a living emoji who overreacts politely. {COMMENT_BASE_RULE_EN} ONE positive phrase (max 12 words). Score: {{score}}. Event: {{event}}. Just the phrase.",
        ]
    }
}

def generate_comment(game, score, event, lang='es'):
    try:
        client = _get_bedrock()
        if not client:
            return None
        themes = COMMENT_THEMES.get(game, COMMENT_THEMES['flappy'])
        prompts = themes.get(lang, themes['es'])
        prompt = random.choice(prompts).format(score=score, event=event)
        body = json.dumps({
            "messages": [{"role": "user", "content": [{"text": prompt}]}],
            "inferenceConfig": {"maxTokens": 60, "temperature": 0.7, "topP": 0.9}
        })
        resp = client.invoke_model(
            modelId='us.amazon.nova-lite-v1:0',
            contentType='application/json',
            accept='application/json',
            body=body
        )
        result = json.loads(resp['body'].read())
        text = result['output']['message']['content'][0]['text'].strip().strip('"').strip("'")
        if len(text) > 80:
            text = text[:77] + '...'
        return text
    except Exception as e:
        print(f"[Comment Error] {e}")
        return None


# --- AI Image Generation (Nova Canvas) ---
IMAGE_THEMES_ES = [
    "Un retrato épico estilo anime de un jugador gamer con el logo de Kiro (púrpura brillante) como capa de superhéroe, celebrando una victoria, fondo de neón púrpura y negro, estilo cyberpunk",
    "Una pintura renacentista dramática de un pájaro púrpura majestuoso (mascota Kiro) coronado como rey, con tubos dorados como columnas de un palacio, estilo barroco",
    "Un póster de película de acción con un pájaro púrpura (Kiro) volando entre explosiones y tubos gigantes, estilo retro años 80, colores neón púrpura y verde",
    "Un mural callejero estilo graffiti de un pájaro púrpura (Kiro) con gafas de sol, haciendo skateboard entre tubos, colores vibrantes púrpura y dorado",
    "Una ilustración kawaii japonesa de un pájaro púrpura redondo (Kiro) rodeado de estrellas y arcoíris, estilo chibi adorable, fondo pastel con detalles púrpura",
    "Un cartel de circo vintage con un pájaro púrpura (Kiro) como acróbata estrella volando entre aros de fuego púrpura, estilo art nouveau",
    "Una escena espacial con un pájaro púrpura (Kiro) como astronauta flotando entre planetas con forma de tubo, nebulosas púrpuras, estilo sci-fi retro",
    "Un pájaro púrpura (Kiro) como detective noir con sombrero y gabardina, en una ciudad lluviosa de neón púrpura, estilo film noir",
    "Una portada de cómic con un pájaro púrpura (Kiro) como superhéroe con capa, volando sobre una ciudad, estilo Marvel pop art",
    "Un pájaro púrpura (Kiro) como samurái con armadura dorada y katana, en un jardín japonés con flores de cerezo púrpuras, estilo ukiyo-e moderno"
]

IMAGE_THEMES_EN = [
    "An epic anime-style portrait of a gamer player with the Kiro logo (bright purple) as a superhero cape, celebrating victory, neon purple and black background, cyberpunk style",
    "A dramatic Renaissance painting of a majestic purple bird (Kiro mascot) crowned as king, with golden pipes as palace columns, baroque style",
    "An action movie poster with a purple bird (Kiro) flying through explosions and giant pipes, retro 80s style, neon purple and green colors",
    "A street art graffiti mural of a purple bird (Kiro) wearing sunglasses, skateboarding between pipes, vibrant purple and gold colors",
    "A kawaii Japanese illustration of a round purple bird (Kiro) surrounded by stars and rainbows, adorable chibi style, pastel background with purple details",
    "A vintage circus poster with a purple bird (Kiro) as star acrobat flying through purple fire rings, art nouveau style",
    "A space scene with a purple bird (Kiro) as astronaut floating among pipe-shaped planets, purple nebulas, retro sci-fi style",
    "A purple bird (Kiro) as noir detective with hat and trenchcoat, in a rainy neon purple city, film noir style",
    "A comic book cover with a purple bird (Kiro) as superhero with cape, flying over a city, Marvel pop art style",
    "A purple bird (Kiro) as samurai with golden armor and katana, in a Japanese garden with purple cherry blossoms, modern ukiyo-e style"
]

CARTOON_PROMPTS_ES = [
    "Caricatura graciosa y exagerada estilo cartoon con colores vibrantes, ojos enormes y expresión chistosa, fondo de neón púrpura, estilo meme divertido para niños",
    "Retrato cartoon súper gracioso con proporciones exageradas, cabeza gigante, sonrisa enorme, estilo caricatura de parque de diversiones, colores brillantes púrpura y neón",
    "Caricatura cómica estilo chibi con expresión ridícula y divertida, ojos de anime enormes, fondo de estrellas y arcoíris púrpura, estilo kawaii gracioso",
    "Retrato estilo cartoon de los 90s, colores locos, expresión exagerada y chistosa, fondo de graffiti púrpura neón, vibes de meme viral",
    "Caricatura estilo Pixar pero más exagerada y graciosa, con expresión de sorpresa cómica, fondo de videojuego retro púrpura, súper colorido",
]

CARTOON_PROMPTS_EN = [
    "Hilarious exaggerated cartoon caricature with vibrant colors, huge eyes and funny expression, neon purple background, fun meme style for kids",
    "Super funny cartoon portrait with exaggerated proportions, giant head, huge smile, amusement park caricature style, bright purple and neon colors",
    "Comic chibi-style caricature with ridiculous funny expression, huge anime eyes, purple stars and rainbow background, funny kawaii style",
    "90s cartoon style portrait, crazy colors, exaggerated funny expression, neon purple graffiti background, viral meme vibes",
    "Pixar-style caricature but more exaggerated and hilarious, with comic surprise expression, retro purple videogame background, super colorful",
]

def generate_image(game, score, lang='es', photo_b64=None):
    try:
        client = _get_bedrock()
        if not client:
            return None
        # If photo provided, use IMAGE_VARIATION to make a cartoon version
        if photo_b64:
            prompts = CARTOON_PROMPTS_ES if lang == 'es' else CARTOON_PROMPTS_EN
            prompt = random.choice(prompts)
            body = json.dumps({
                "taskType": "IMAGE_VARIATION",
                "imageVariationParams": {
                    "text": prompt,
                    "images": [photo_b64],
                    "similarityStrength": 0.4
                },
                "imageGenerationConfig": {
                    "numberOfImages": 1,
                    "height": 512,
                    "width": 512,
                    "cfgScale": 8.0
                }
            })
        else:
            # Fallback: text-to-image with random theme
            themes = IMAGE_THEMES_ES if lang == 'es' else IMAGE_THEMES_EN
            prompt = random.choice(themes)
            if lang == 'es':
                prompt += f". Incluir el número {score} de forma prominente como puntuación."
            else:
                prompt += f". Include the number {score} prominently as a score."
            body = json.dumps({
                "taskType": "TEXT_IMAGE",
                "textToImageParams": {
                    "text": prompt
                },
                "imageGenerationConfig": {
                    "numberOfImages": 1,
                    "height": 512,
                    "width": 512,
                    "cfgScale": 8.0
                }
            })

        resp = client.invoke_model(
            modelId='amazon.nova-canvas-v1:0',
            contentType='application/json',
            accept='application/json',
            body=body
        )
        result = json.loads(resp['body'].read())
        img_b64 = result['images'][0]
        return img_b64
    except Exception as e:
        print(f"[Image Error] {e}")
        traceback.print_exc()
        return None


# --- TTS with Polly ---
POLLY_VOICES = {'es': 'Lucia', 'en': 'Joanna'}

def generate_tts(text, lang='es'):
    try:
        client = _get_polly()
        if not client:
            return None
        voice = POLLY_VOICES.get(lang, 'Lucia')

        # Try neural first, fall back to standard if not supported
        for engine in ['neural', 'standard']:
            try:
                resp = client.synthesize_speech(
                    Text=text,
                    OutputFormat='mp3',
                    VoiceId=voice,
                    Engine=engine
                )
                audio_bytes = resp['AudioStream'].read()
                print(f"[Polly] OK — voice={voice}, engine={engine}, lang={lang}, bytes={len(audio_bytes)}")
                return base64.b64encode(audio_bytes).decode('utf-8')
            except Exception as eng_err:
                print(f"[Polly] Engine '{engine}' failed for {voice}: {eng_err}")
                continue

        print(f"[Polly] All engines failed for voice={voice}")
        return None
    except Exception as e:
        print(f"[Polly Error] {e}")
        return None


# --- HTTP Handler ---
class GameHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        # GET /api/ranking?game=flappy
        if self.path.startswith('/api/ranking'):
            self._handle_ranking_get()
        else:
            super().do_GET()

    def do_DELETE(self):
        # DELETE /api/ranking?game=flappy  or  /api/ranking?game=all
        if self.path.startswith('/api/ranking'):
            self._handle_ranking_reset()
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/api/comment':
            self._handle_comment()
        elif self.path == '/api/image':
            self._handle_image()
        elif self.path == '/api/tts':
            self._handle_tts()
        elif self.path.startswith('/api/ranking'):
            self._handle_ranking_post()
        else:
            self.send_response(404)
            self.end_headers()

    def _handle_ranking_get(self):
        from urllib.parse import urlparse, parse_qs
        qs = parse_qs(urlparse(self.path).query)
        game = qs.get('game', ['flappy'])[0]
        entries = load_ranking_file(game)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(entries).encode())

    def _handle_ranking_post(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length))
            game = data.get('game', 'flappy')
            score = data.get('score', 0)
            name = (data.get('name') or '???').strip()[:20]
            date = data.get('date', '')
            entries = load_ranking_file(game)
            entries.append({'score': score, 'name': name, 'date': date})
            entries.sort(key=lambda x: x['score'], reverse=True)
            top5 = entries[:5]
            save_ranking_file(game, top5)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(top5).encode())
        except Exception as e:
            print(f"[Ranking POST Error] {e}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())

    def _handle_ranking_reset(self):
        from urllib.parse import urlparse, parse_qs
        qs = parse_qs(urlparse(self.path).query)
        game = qs.get('game', ['all'])[0]
        if game == 'all':
            for g in RANKING_KEYS:
                reset_ranking_file(g)
        else:
            reset_ranking_file(game)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'ok': True}).encode())

    def _handle_comment(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length))
            game = data.get('game', 'flappy')
            score = data.get('score', 0)
            event = data.get('event', 'playing')
            lang = data.get('lang', 'es')
            comment = generate_comment(game, score, event, lang)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'comment': comment}).encode())
        except Exception as e:
            print(f"[API Error] {e}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())

    def _handle_image(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length))
            game = data.get('game', 'flappy')
            score = data.get('score', 0)
            lang = data.get('lang', 'es')
            photo_b64 = data.get('photo', None)
            img_b64 = generate_image(game, score, lang, photo_b64)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'image': img_b64}).encode())
        except Exception as e:
            print(f"[Image API Error] {e}")
            traceback.print_exc()
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())

    def _handle_tts(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length))
            text = data.get('text', '')
            lang = data.get('lang', 'es')
            if not text:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'no text'}).encode())
                return
            audio_b64 = generate_tts(text, lang)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'audio': audio_b64}).encode())
        except BrokenPipeError:
            pass  # Client disconnected, ignore
        except Exception as e:
            print(f"[TTS API Error] {e}")
            try:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())
            except BrokenPipeError:
                pass


class ThreadedServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True

with ThreadedServer(("", PORT), GameHandler) as httpd:
    print(f"🎮 Kiro Arcade running at http://localhost:{PORT}")
    print(f"🤖 Bedrock AI enabled (Nova Lite + Nova Canvas + Polly TTS) — Region: {REGION}")
    httpd.serve_forever()
