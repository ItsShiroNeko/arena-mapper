"""Selection model: what is selected and how to resolve it to project objects."""


class SelectionMixin:
    @property
    def selected(self):
        return self.sel[0] if len(self.sel) == 1 else None

    def set_sel(self, items, src=None):
        new = []
        for i in items:
            if i not in new:
                new.append(i)
        self.sel = new
        self.refresh_props()
        self.sync_trees(src)
        if new and self.nb.index(self.nb.select()) == self.nb.index(self.tab_project):
            self.nb.select(self.tab_props)
        self.redraw()
        self.draw_profile()
        self.update_status()

    def select(self, item):
        self.set_sel([item] if item else [])

    def tgt(self, s):
        if s[0] == "obj":
            return self.proj.obj(s[1])
        if s[0] == "wp":
            return self.proj.waypoints[s[1]] if s[1] < len(self.proj.waypoints) else None
        return self.proj.auv

    def target(self):
        s = self.selected
        return self.tgt(s) if s else None

    def sel_objs(self):
        return [o for s in self.sel if s[0] == "obj" for o in [self.proj.obj(s[1])] if o]

    def select_all(self):
        self.set_sel([("obj", o.id) for o in self.proj.objects if not o.hidden])
