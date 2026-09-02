import sys
import os
import getpass
from dulwich import porcelain

repo_path = os.path.dirname(os.path.abspath(__file__))
DEFAULT_URL = "https://github.com/YB-439/p38Web_Ui.git"

print("=" * 65)
print("  p38α MAPK QSAR Predictor: GitHub Deployment Uploader")
print("  Target: https://github.com/YB-439/p38Web_Ui")
print("=" * 65)

token = None
if len(sys.argv) > 1:
    arg = sys.argv[1].strip()
    if "github.com" in arg:
        DEFAULT_URL = arg
    else:
        token = arg

if len(sys.argv) > 2 and token is None:
    token = sys.argv[2].strip()

# If token not passed as arg, ask
if not token and "@" not in DEFAULT_URL:
    print("\nGitHub requires authentication to push to repositories.")
    print("You can generate a token at: https://github.com/settings/tokens (select 'repo' scope)")
    try:
        token = input("Enter your GitHub Personal Access Token (or paste it here): ").strip()
    except Exception:
        token = None

target_url = DEFAULT_URL
if token:
    # Insert token into HTTPS URL
    if "https://" in target_url and "@" not in target_url:
        target_url = target_url.replace("https://", f"https://{token}@")

repo = porcelain.open_repo(repo_path)
print(f"\nSetting remote 'origin' to {DEFAULT_URL}...")
try:
    porcelain.remote_add(repo, "origin", target_url)
except Exception:
    try:
        # Update existing origin
        config = repo.get_config()
        config.set(("remote", "origin"), "url", target_url.encode("utf-8"))
        config.write_to_path()
    except Exception as e:
        pass

print("Pushing 'main' branch to GitHub...")
try:
    # Push master to main
    porcelain.push(repo, remote_location=target_url, refspecs=["refs/heads/master:refs/heads/main"])
    print("\n🎉 SUCCESS! Your code has been pushed to https://github.com/YB-439/p38Web_Ui")
    print("You can now go to https://share.streamlit.io to deploy your app!")
except Exception as e:
    err_str = str(e)
    print(f"\n❌ Push failed: {err_str}")
    if "403" in err_str or "credentials" in err_str.lower():
        print("Tip: Make sure your GitHub token has 'repo' (read/write) permissions enabled.")
    print("\nAlternative options:")
    print("1. Run with token:")
    print("   python push_to_github.py <YOUR_GITHUB_TOKEN>")
    print("2. Or use GitHub Desktop (File -> Add Local Repository -> Publish)")
