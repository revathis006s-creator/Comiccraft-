# ComicCraft

AI Comic Story Creator using Gemini and image generation.

## Windows setup

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Edit `.env` and set `GEMINI_API_KEY`.

For the first test keep:

```env
IMAGE_PROVIDER=placeholder
```

Run:

```powershell
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000

API docs: http://127.0.0.1:8000/docs

Health: http://127.0.0.1:8000/health

Tests:

```powershell
pytest -q
```

For real Stable Diffusion images, set `IMAGE_PROVIDER=diffusers`.
