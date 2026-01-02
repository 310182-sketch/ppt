# AI PPT for Canva — Extension

This Chrome extension injects a small UI into Canva pages to request outline/image/PPT generation from your backend and helps insert generated assets into the Canva editor.

Quick steps

1. Install the extension in developer mode: `chrome://extensions` → Load unpacked → select `extension/` folder.
2. Open the extension options and set `Backend URL` to your backend (e.g. `http://localhost:8000`).
3. Open Canva, click the floating `AI PPT` button, generate outline or images.

Notes

- The extension does not contain API keys. All AI calls are proxied via your backend.
- Automatic insertion to Canva is best-effort (tries file input and drag-drop). For robust integration consider building a Canva App.

Security & privacy

- Do NOT store sensitive API keys in extension storage. Use server-side secret management.
