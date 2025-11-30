import os
import subprocess
import sys
from datetime import datetime


BASE = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE, "logs")
os.makedirs(LOG_DIR, exist_ok=True)


def log_path(name):
    t = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return os.path.join(LOG_DIR, f"{name}_{t}.log")


def run_step(name, command, cwd=None):
    print("\n" + "="*60)
    print(f"[RUN] {name}")
    print("="*60)

    logfile = log_path(name)
    with open(logfile, "w", encoding="utf-8") as f:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            stdout=f,
            stderr=f,
            shell=True
        )
        process.wait()

    if process.returncode != 0:
        print(f"❌ FAILED: {name}")
        print(f"📝 See log: {logfile}")
        sys.exit(1)

    print(f"✔ DONE: {name}")
    print(f"📝 Log saved to {logfile}")


def main():
    print("="*60)
    print("   Fake News Detection - Full Pipeline Runner")
    print("="*60)

    # Step 1 — Crawl ISNA
    run_step(
        name="crawler",
        command="python persian_crawler.py",
        cwd=os.path.join(BASE, "crawler")
    )

    # Step 2 — Clean Content
    run_step(
        name="content_cleaner",
        command="python content_cleaner.py",
        cwd=os.path.join(BASE, "parser")
    )

    # Step 3 — Build Inverted Index
    run_step(
        name="index_builder",
        command="python index_builder.py",
        cwd=os.path.join(BASE, "index")
    )

    # Step 4 — Build Graph (incoming/outgoing links + HITS)
    run_step(
        name="graph_builder",
        command="python graph_builder.py",
        cwd=os.path.join(BASE, "graph")
    )

    # Step 5 — Generate Embeddings
    run_step(
        name="embeddings",
        command="python embedder.py",
        cwd=os.path.join(BASE, "llm")
    )

    # Step 6 — Run Fake News Detector
    run_step(
        name="fake_news_test",
        command="python test_fake_news.py",
        cwd=os.path.join(BASE, "test")
    )

    print("\n" + "="*60)
    print("🎉 Pipeline executed successfully! All modules completed.")
    print("="*60)


if __name__ == "__main__":
    main()
