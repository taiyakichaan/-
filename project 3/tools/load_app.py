"""元の app.py を読み込むための共通処理。起動時の先読み（天気取得・全ページ生成）は止めて、計算部分だけ使う。
使い方: from load_app import load; app = load("<元アプリのフォルダ>")"""
import os, sys, threading

def load(app_dir):
    app_dir = os.path.abspath(app_dir)
    os.chdir(app_dir); sys.path.insert(0, app_dir)
    _start = threading.Thread.start
    def start(self):
        if getattr(self, "_target", None) is not None and getattr(self._target, "__name__", "") == "_prewarm": return
        return _start(self)
    threading.Thread.start = start
    try:
        import app
    finally:
        threading.Thread.start = _start
    return app
