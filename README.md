# 🎮 Kiro Arcade

> 🇬🇧 [English version](README_en.md)

Una arcade en el navegador creada para el workshop de Kiro AI. Los jugadores eligen entre 4 minijuegos usando gestos de mano a través de la webcam, impulsado por detección de manos con MediaPipe e IA de AWS Bedrock.

## Juegos

- **Flappy Kiro** ☝️ — Clon de Flappy Bird con el logo de Kiro como personaje
- **Fruit Ninja** ✊ — Corta frutas antes de que caigan de la pantalla
- **Piedra Papel Tijera** 👌 — Juega contra la IA de Kiro usando gestos de mano
- **Ghost Dodge** 🖐️ — Esquiva fantasmas entrantes el mayor tiempo posible

## Funcionalidades

- Selección de juego por gestos de mano (sin teclado)
- Clasificaciones por juego almacenadas como archivos JSON en el servidor
- Comentarios e imágenes generados por IA con AWS Bedrock (Nova Lite + Nova Canvas)
- Texto a voz con Amazon Polly
- Modal "Aprende Kiro" con introducción, demo guiada y guía de aprendizaje jugando
- Interfaz bilingüe (español / inglés)

## Requisitos

- Python 3.8+
- Firefox (navegador recomendado — necesario para compatibilidad con webcam/MediaPipe)
- Puerto 8000 disponible en tu máquina
- Credenciales AWS configuradas con acceso a Bedrock y Polly (perfil: `kiro-arcade`)

## Cómo arrancar

1. Instala las dependencias:

```bash
pip install -r requirements.txt
```

2. Inicia el servidor:

```bash
python server.py
```

3. Abre [http://localhost:8000](http://localhost:8000) en Firefox.

## Estructura del proyecto

```
/
├── index.html        # Menú principal de la arcade
├── server.py         # Servidor de archivos estáticos + endpoints de IA
├── src/              # Archivos de juegos (flappy, fruit-ninja, rps, ghost-dodge)
├── images/           # Sprites y assets
├── videos/           # Vídeos de demo y tutoriales
├── docs/             # Playbook y documentación del proyecto
└── rankings/         # Archivos JSON de clasificaciones por juego
```

## Aviso legal

Este proyecto es una demo independiente creada con fines educativos y para workshops. No está afiliado, respaldado ni es representativo de Amazon Web Services (AWS) ni de ninguno de sus productos. El uso de los servicios de AWS (Amazon Bedrock, Amazon Polly, etc.) es responsabilidad exclusiva del usuario. AWS no es responsable del contenido, la funcionalidad ni de ningún resultado derivado del uso de este proyecto.
