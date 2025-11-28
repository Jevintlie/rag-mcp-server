# scripts/refresh_all.py
import subprocess, sys, shlex

def run(cmd):
    print(f"\n$ {cmd}")
    proc = subprocess.run(shlex.split(cmd), check=True)
    return proc.returncode

if __name__ == "__main__":
    # 1) make/refresh all JSONs from every HTML in data/html/
    run("python scripts/sync_batch.py --glob data/html/*.html")
    # 2) rebuild/ups ert the index (Chroma PersistentClient persists on disk)
    run("python scripts/build_index.py")
    print("\nAll done. Collection refreshed.")
