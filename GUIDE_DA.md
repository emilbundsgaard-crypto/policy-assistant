# Guide: fra kode til aflevering

## 1. Kør testen (på din Mac)
```
cd ~/policy-assistant
python3 -m pip install -r requirements.txt
python3 evaluate.py
```
Den kører 21 spørgsmål × 3 metoder og tager et par minutter. Til sidst printer den en opsummering og laver `results.json`.
**Send opsummeringen til Claude**, så bliver de to afsnit skrevet ud fra dine rigtige tal.

## 2. Læg koden på GitHub
1. Gå til github.com → **New repository** → navn `policy-assistant` → **Public** → Create.
2. I Terminal (i `~/policy-assistant`):
```
git init
git add .
git commit -m "Company policy assistant"
git branch -M main
git remote add origin https://github.com/DIT-BRUGERNAVN/policy-assistant.git
git push -u origin main
```
Tjek på GitHub, at `.env` **ikke** er kommet med (den er udelukket via `.gitignore`). `results.json` og `embeddings.json` skal med.

## 3. Deploy på Render
1. render.com → log ind med GitHub.
2. **New → Blueprint** → vælg dit `policy-assistant`-repo. Render læser `render.yaml`.
3. Den beder om `GEMINI_API_KEY` → indsæt din nøgle → **Apply**.
4. Efter build får du et link som `https://policy-assistant-xxxx.onrender.com`. Det er dit website-link.

Gratis-planen sover efter 15 min uden trafik, og første besøg tager ca. 1 min. Det er fint til aflevering.

## 4. Slack
**Workspace og kanal**
1. slack.com → **Create a new workspace**. Giv det et navn med dit navn, fx `Emil Sørensen AI Accounting`.
2. Opret kanalen `#emil-sorensen-policy-bot`.

**Botten**
1. api.slack.com/apps → **Create New App → From a manifest** → vælg dit workspace → indsæt indholdet af `slack_manifest.yml` → Create.
2. **Install App** → Install to workspace → kopiér **Bot User OAuth Token** (`xoxb-...`).
3. **Basic Information → App-Level Tokens → Generate** → giv den scope `connections:write` → kopiér (`xapp-...`).
4. Indsæt begge tokens i `.env`:
```
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...
```
5. Start botten: `python3 slack_bot.py`. Lad Terminal stå åben.
6. I kanalen skriver du: `/invite @Policy Assistant`
7. Test: `@Policy Assistant How many vacation days do I get?` → **tag screenshot**.

**Inviter underviser**
Invitér `raz@sdu.dk` til workspacet og kanalen: kanalnavn øverst → **Add people**.

## 5. Aflever
- Link til Render-siden
- De to afsnit (står også på siden)
- Link til GitHub-repoet
- Screenshot fra Slack
