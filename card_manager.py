import os
import json
import threading
from github import Github

DATA_FILE = "characters.json"
chars_cache = {}

def load_data():
    """開機時主動從 GitHub 下載最新存檔 (自動相容 master/main)"""
    global chars_cache
    gh_token = os.environ.get("GITHUB_TOKEN")
    repo_name = os.environ.get("GITHUB_REPO")
    
    if gh_token and repo_name:
        try:
            g = Github(gh_token)
            repo = g.get_repo(repo_name.strip())
            
            # 💡 聰明分支判斷：優先看 main，沒有再看 master
            branch = "main"
            try:
                repo.get_contents(DATA_FILE, ref="main")
            except:
                branch = "master"
                
            contents = repo.get_contents(DATA_FILE, ref=branch)
            chars_cache = json.loads(contents.decoded_content.decode('utf-8'))
            print("【成功】成功從 GitHub 雲端同步角色卡數據！", flush=True)
            return
        except Exception as e:
            print(f"【注意】雲端無存檔或讀取失敗，改用本機讀取: {e}", flush=True)
            
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                chars_cache = json.load(f)
        except:
            chars_cache = {}

def _push_to_github():
    """在背景偷偷執行的 GitHub 上傳任務"""
    gh_token = os.environ.get("GITHUB_TOKEN")
    repo_name = os.environ.get("GITHUB_REPO")
    
    if gh_token and repo_name:
        try:
            g = Github(gh_token)
            repo = g.get_repo(repo_name.strip())
            
            # 💡 自動探查目前倉庫的分支名稱
            branch = "main"
            try:
                repo.get_branches()
                branches = [b.name for b in repo.get_branches()]
                branch = "main" if "main" in branches else "master"
            except:
                branch = "master"

            with open(DATA_FILE, "r", encoding="utf-8") as f:
                updated_content = f.read()
            
            try:
                contents = repo.get_contents(DATA_FILE, ref=branch)
                repo.update_file(DATA_FILE, "🤖 同步最新角色卡數據庫 (無痕覆蓋)", updated_content, contents.sha, branch=branch)
                print("【日誌】角色卡更新成功！", flush=True)
            except:
                repo.create_file(DATA_FILE, "🤖 首次建立角色卡數據庫", updated_content, branch=branch)
                print("【日誌】角色卡【首次建立】成功！", flush=True)
                
        except Exception as e:
            # 💡 加上強制沖刷，萬一失敗，這行一定會秒噴在 Render 上！
            print(f"【🚨 大警報】背景備份至 GitHub 失敗: {str(e)}", flush=True)

def save_data():
    """先存入本機快取，並啟動背景線程上傳"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(chars_cache, f, ensure_ascii=False)
    threading.Thread(target=_push_to_github).start()
