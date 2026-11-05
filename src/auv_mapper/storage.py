"""Persistent JSON stores (settings and recent-projects list)."""
import json
import os

from .constants import LEGACY_RECENT, MAX_RECENT, RECENT_FILE
from .utils import now_iso


class JsonStore:
    def __init__(self, path, default, legacy=None):
        self.path, self.data = path, default
        for p in [path] + ([legacy] if legacy else []):
            try:
                with open(p, encoding="utf-8") as f:
                    self.data = json.load(f)
                break
            except (OSError, ValueError):
                continue

    def save(self):
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except OSError:
            pass


class RecentStore(JsonStore):
    def __init__(self):
        super().__init__(RECENT_FILE, [], LEGACY_RECENT)
        self.items = [i for i in self.data if isinstance(i, dict) and "path" in i] \
            if isinstance(self.data, list) else []

    def _save(self):
        self.data = self.items[:MAX_RECENT]
        self.save()

    def add(self, path, name):
        path = os.path.abspath(path)
        self.items = [i for i in self.items if i["path"] != path]
        self.items.insert(0, {"path": path, "name": name, "opened": now_iso()})
        self.items = self.items[:MAX_RECENT]
        self._save()

    def remove(self, path):
        self.items = [i for i in self.items if i["path"] != path]
        self._save()
