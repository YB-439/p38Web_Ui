import sys
import os
from dulwich import porcelain

repo_path = os.path.dirname(os.path.abspath(__file__))

if len(sys.argv) < 2:
    print("=================================================================")
    print("  p38α MAPK Predictor: GitHub Uploader")
    print("=================================================================")
    print("Usage: python push_to_github.py <GITHUB_REPO_URL>")
    print("Example: python push_to_github.py https://github.com/username/p38a-mapk-predictor.git")
    sys.exit(1)

remote_url = sys.argv[1].strip()

repo = porcelain.open_repo(repo_path)
print(f"Setting remote 'origin' to {remote_url}...")
try:
    porcelain.remote_add(repo, "origin", remote_url)
except Exception:
    pass

print("Pushing to GitHub...")
try:
    porcelain.push(repo, remote_location=remote_url, refspecs=["refs/heads/master:refs/heads/main"])
    print("✅ Successfully pushed to GitHub!")
except Exception as e:
    print(f"Push status: {e}")
    print("
Alternative (using Git CLI or GitHub Desktop):")
    print(f"  git remote add origin {remote_url}")
    print("  git branch -M main")
    print("  git push -u origin main")
