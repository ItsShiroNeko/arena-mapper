"""Object catalogue: kinds, palette groups, drawing order and mission tokens."""

KINDS = {
    "qual_gate": dict(label="Qual Gate", color="#ff8c00", shape="bar", size=1.5, h=0.0, depth=0.64, group="Gerbang", heading=90.0),
    "gate": dict(label="Gate Utama", color="#e8e8e8", shape="gate", size=3.0, h=0.0, depth=1.0, group="Gerbang", heading=0.0),
    "qstart": dict(label="Qual Start", color="#d4a017", shape="bar", size=1.5, h=0.0, depth=1.0, group="Gerbang", heading=90.0),
    "flare_orange": dict(label="Flare Oranye", color="#ff8c00", shape="circle", size=0.5, h=0.0, depth=1.0, group="Flare", heading=0.0),
    "flare_yellow": dict(label="Flare Kuning", color="#f5c800", shape="circle", size=0.5, h=0.0, depth=1.0, group="Flare", heading=0.0),
    "flare_red": dict(label="Flare Merah", color="#e03030", shape="circle", size=0.5, h=0.0, depth=1.0, group="Flare", heading=0.0),
    "flare_blue": dict(label="Flare Biru", color="#2f7be0", shape="circle", size=0.5, h=0.0, depth=1.0, group="Flare", heading=0.0),
    "drum_red": dict(label="Drum Merah", color="#c42323", shape="circle", size=0.9, h=0.0, depth=1.2, group="Drum", heading=0.0),
    "drum_blue": dict(label="Drum Biru", color="#1f5fbf", shape="circle", size=0.9, h=0.0, depth=1.2, group="Drum", heading=0.0),
    "surface": dict(label="Surfacing Square", color="#9aa5b1", shape="rect", size=2.0, h=2.0, depth=0.0, group="Zona", heading=0.0, alpha=0.55),
    "start": dict(label="Start Zone", color="#b0b8c4", shape="rect", size=1.4, h=1.4, depth=1.0, group="Zona", heading=0.0, alpha=0.55),
    "target": dict(label="Target Zone", color="#4c9a2a", shape="rect", size=8.0, h=2.0, depth=1.2, group="Zona", heading=0.0, alpha=0.6),
    "zone": dict(label="Zona Kustom", color="#e0a030", shape="rect", size=4.0, h=4.0, depth=1.0, group="Zona", heading=0.0, alpha=0.5),
    "obstacle": dict(label="Rintangan", color="#8b5a3c", shape="rect", size=1.0, h=1.0, depth=1.0, group="Lainnya", heading=0.0, alpha=1.0),
    "marker": dict(label="Marker / Buoy", color="#c792ea", shape="circle", size=0.6, h=0.0, depth=1.0, group="Lainnya", heading=0.0),
    "text": dict(label="Label Teks", color="#c5d8ec", shape="text", size=1.0, h=0.0, depth=0.0, group="Lainnya", heading=0.0),
}
GROUPS = ["Gerbang", "Flare", "Drum", "Zona", "Lainnya"]
SHAPE_Z = {"rect": 0, "text": 1, "bar": 2, "gate": 3, "circle": 4}

TOKENS = {"qual": "qual_gate", "gate": "gate", "orange": "flare_orange", "yellow": "flare_yellow",
          "red": "flare_red", "blue": "flare_blue", "surface": "surface", "target": "target",
          "marker": "marker", "zone": "zone"}
TOKENS.update({k: k for k in KINDS})
TOKEN_CHOICES = ["gate", "qual", "orange", "yellow", "red", "blue", "drum_red", "drum_blue",
                 "surface", "target", "marker", "zone", "goto:x,y,z"]
