import os
import json
import threading
from github import Github

DATA_FILE = "characters.json"
chars_cache = {}

def load_data():
    """開機時主動從 GitHub 下載最新存檔"""
    global chars_cache
    gh_token = os.environ.get("GITHUB_TOKEN")
    if gh_token:
        try:
            g = Github(gh_token)
            repo_name = os.environ.get("RENDER_GIT_REPO", "").split("://github.com")[-1].replace(".git", "")
            if repo_name:
                repo = g.get_repo(repo_name)
                contents = repo.get_contents(DATA_FILE, ref="master")
                chars_cache = json.loads(contents.decoded_content.decode('utf-8'))
                print("成功從 GitHub 雲端同步角色卡數據！")
                return
        except Exception as e:
            print(f"雲端無存檔或讀取失敗，改用本機讀取: {e}")
            
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                chars_cache = json.load(f)
        except:
            chars_cache = {}

def _push_to_github():
    """在背景偷偷執行的 GitHub 上傳任務，完全不卡主程式"""
    gh_token = os.environ.get("GITHUB_TOKEN")
    if gh_token:
        try:
            g = Github(gh_token)
            repo_name = os.environ.get("RENDER_GIT_REPO", "").split("://github.com")[-1].replace(".git", "")
            if repo_name:
                repo = g.get_repo(repo_name)
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    updated_content = f.read()
                try:
                    contents = repo.get_contents(DATA_FILE, ref="master")
                    repo.update_file(DATA_FILE, "🤖 機器人自動同步角色卡變更", updated_content, contents.sha, branch="master")
                except:
                    repo.create_file(DATA_FILE, "🤖 機器人首次建立角色卡存檔", updated_content, branch="master")
                print("角色卡背景備份成功！")
        except Exception as e:
            print(f"背景備份至 GitHub 失敗: {e}")

def save_data():
    """先存入本機快取，並啟動背景線程上傳"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(chars_cache, f, ensure_ascii=False, indent=4)
    threading.Thread(target=_push_to_github).start()
