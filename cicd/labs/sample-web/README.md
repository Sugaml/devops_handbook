# sample-web — CI/CD handbook lab app

Minimal Flask API used across Jenkins, GitHub Actions, GitLab CI, and Bitbucket Pipelines tracks.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -v
python src/app.py   # http://localhost:8080
docker build -t sample-web:local .
```
