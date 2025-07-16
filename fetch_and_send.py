name: V2Ray Config Scraper

on:
  schedule:
    - cron: '0 */3 * * *'  # هر 3 ساعت یک بار
  workflow_dispatch:

jobs:
  run-scraper:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.x'

      - name: Install dependencies
        run: pip install requests

      - name: Run fetch_and_send
        run: python fetch_and_send.py

      - name: Commit sent_configs
        run: |
          git config --global user.email "bot@example.com"
          git config --global user.name "Zenora Bot"
          git add sent_configs.txt
          git commit -m "Update sent configs"
          git push
