"""Undo / redo, edit transactions and status messages."""
from contextlib import contextmanager

from ...constants import MAX_UNDO


class HistoryMixin:
    @contextmanager
    def edit(self):
        before = self.proj.state()
        yield
        self.commit(before)

    def commit(self, before):
        if self.proj.state() != before:
            self.undo.append(before)
            del self.undo[:-MAX_UNDO]
            self.redo.clear()
            self.stop_sim()
            self.refresh_all()

    def do_undo(self):
        if not self.undo:
            return
        self.redo.append(self.proj.state())
        self.proj.load_state(self.undo.pop())
        self.stop_sim()
        self.say("Undo")
        self.refresh_all()

    def do_redo(self):
        if not self.redo:
            return
        self.undo.append(self.proj.state())
        self.proj.load_state(self.redo.pop())
        self.stop_sim()
        self.say("Redo")
        self.refresh_all()

    def is_dirty(self):
        return self.proj.state() != self.saved_state

    def say(self, msg):
        self.sv_hint.set(msg)

    def adopt(self, old):
        """Take over state from a previous Editor (used when switching theme)."""
        self.undo, self.redo, self.saved_state = old.undo, old.redo, old.saved_state
        self.clip, self.paste_n = old.clip, old.paste_n
        self.grid_on.set(old.grid_on.get())
        self.snap_on.set(old.snap_on.get())
        self.labels_on.set(old.labels_on.get())
        self.tool_var.set(old.tool_var.get())
        self.sel = list(old.sel)
        self.refresh_all()
