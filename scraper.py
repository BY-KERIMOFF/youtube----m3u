name: Update 720izle M3U

on:
  workflow_dispatch:

  schedule:
    - cron: "0 * * * *"

permissions:
  contents: write

jobs:
  update:
    runs-on: ubuntu-latest

    steps:
      - name: Repository-ni yüklə
        uses: actions/checkout@v4

      - name: Python qur
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Paketləri quraşdır
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Scraper-i işə sal
        run: |
          python scraper.py

      - name: M3U yoxla
        run: |
          echo "=============================="
          echo "M3U FILE"
          echo "=============================="

          if [ -f films.m3u ]; then
            wc -l films.m3u
            head -20 films.m3u
          else
            echo "films.m3u tapılmadı"
            exit 1
          fi

      - name: Git commit
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"

          git add films.m3u

          if git diff --cached --quiet; then
            echo "Dəyişiklik yoxdur."
          else
            git commit -m "Update 720izle films"
            git push
          fi
