"""Kinematic AUV simulation (play / pause / stop)."""
import math
import tkinter as tk

from ...constants import ACCEPT_RADIUS, SIM_DT, SIM_STEPS_PER_TICK, TURN_RATE_DEG_S
from ...geometry import auv_poly, bearing, vec, wrap180
from ...icons import ico, states
from ...render.sinks import TkSink
from ...theme import T
from ...utils import fmt_time


class SimulationMixin:
    def update_sim_ui(self):
        running = bool(self.sim and self.sim.get("running") and not self.sim_paused)
        name = "pause" if running else "play"
        self.btn_play.configure(image=states(name))
        self.btn_play2.configure(image=ico(name))

    def toggle_sim(self):
        if self.sim and self.sim.get("running"):
            self.sim_paused = not self.sim_paused
            self.update_sim_ui()
            if self.sim_paused:
                self.say("Simulasi dijeda. F5 untuk melanjutkan.")
            else:
                self.say("Simulasi berjalan.")
                self.sim_tick()
            return
        if not self.proj.waypoints:
            self.say("Belum ada waypoint. Tekan P (Generate) atau tambahkan dengan tool Waypoint.")
            return
        self.stop_sim()
        a = self.proj.auv
        self.sim = dict(x=a.x, y=a.y, h=a.heading, i=0, trail=[(a.x, a.y)], running=True, wait=0.0, t=0.0)
        self.sim_paused = False
        self.update_sim_ui()
        self.say("Simulasi berjalan. F5 jeda, Shift+F5 berhenti.")
        self.sim_tick()

    def stop_sim(self):
        if self.sim_job:
            try:
                self.after_cancel(self.sim_job)
            except tk.TclError:
                pass
        self.sim_job = None
        self.sim = None
        self.sim_paused = False
        try:
            self.canvas.delete("sim")
            self.update_sim_ui()
        except (tk.TclError, AttributeError):
            pass

    def sim_tick(self):
        s = self.sim
        if not s or self.sim_paused:
            return
        self.sim_job = None
        wps = self.proj.waypoints
        for _ in range(max(1, int(SIM_STEPS_PER_TICK * self.sim_mult))):
            if s["i"] >= len(wps):
                break
            s["t"] += SIM_DT
            if s["wait"] > 0:
                s["wait"] -= SIM_DT
                continue
            w = wps[s["i"]]
            dx, dy = w.x - s["x"], w.y - s["y"]
            d = math.hypot(dx, dy)
            if d < ACCEPT_RADIUS:
                s["wait"] = w.hold
                s["i"] += 1
                continue
            err = wrap180(bearing(dx, dy) - s["h"])
            mt = TURN_RATE_DEG_S * SIM_DT
            s["h"] = (s["h"] + max(-mt, min(mt, err))) % 360.0
            v = self.proj.speed * math.cos(math.radians(min(abs(err), 89.0))) ** 2
            v = min(v, max(0.05, math.radians(TURN_RATE_DEG_S) * d /
                           (2 * max(math.sin(math.radians(min(abs(err), 90.0))), 0.05))))
            step = min(v * SIM_DT, d)
            f = vec(s["h"])
            s["x"] += f[0] * step
            s["y"] += f[1] * step
            s["trail"].append((s["x"], s["y"]))
        self.draw_sim()
        if s["i"] >= len(wps) and s["wait"] <= 0:
            s["running"] = False
            self.sim_job = None
            self.update_sim_ui()
            self.say(f"Simulasi selesai dalam {fmt_time(s['t'])} (mm:ss).")
        else:
            self.say(f"Simulasi: waypoint {min(s['i'] + 1, len(wps))}/{len(wps)}   t = {fmt_time(s['t'])}")
            self.sim_job = self.after(40, self.sim_tick)

    def draw_sim(self):
        s = self.sim
        c = self.canvas
        c.delete("sim")
        if not s or self.view is None:
            return
        sink = TkSink(c, "sim")
        if len(s["trail"]) > 1:
            sink.line([self.w2s(*p) for p in s["trail"]], fill=T["sim"], width=2)
        sink.polygon([self.w2s(*p) for p in auv_poly(s["x"], s["y"], s["h"], 1.1)], fill=T["sim"],
                     outline="#ffffff", width=1)
