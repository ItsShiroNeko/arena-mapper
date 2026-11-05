"""In-app help / shortcut reference."""
from .constants import MOD

HELP_TEXT = f"""\
BERKAS
  {MOD}+N / {MOD}+O        Proyek baru / Buka
  {MOD}+S / {MOD}+Shift+S  Simpan / Simpan sebagai
  {MOD}+W                Tutup proyek (ke Beranda)
  {MOD}+E / {MOD}+Shift+E  Ekspor CSV / SVG
  {MOD}+Q                Keluar

EDIT
  {MOD}+Z                Undo
  {MOD}+Y / {MOD}+Shift+Z  Redo
  {MOD}+X / C / V        Potong / Salin / Tempel
  {MOD}+D                Duplikat
  {MOD}+A                Pilih semua objek
  Delete / Backspace    Hapus terpilih
  R / Shift+R           Putar +15 / -15 derajat
  + / -                 Ukuran objek       [ / ]  Kedalaman -/+ 0.1 m
  Panah                 Geser satu langkah snap (Shift = 5x)
  {MOD}+L                Kunci / buka kunci
  {MOD}+H                Sembunyikan / tampilkan

TAMPILAN
  {MOD}+0 atau F         Fit ke kolam
  {MOD}+ + / {MOD}+ -      Zoom (atau scroll mouse)
  Spasi (tahan)         Geser tampilan sementara
  Klik tengah (seret)   Geser tampilan;  Shift+scroll = geser horizontal
  G / N / L             Grid / Snap / Label
  F11                   Layar penuh

TOOL
  V Pilih   H Tangan   W Waypoint   A Posisi AUV   M Ukur jarak
  Esc       Kembali ke Pilih / batal pilihan

PILIH
  Klik          pilih          Shift+klik     tambah/kurangi pilihan
  Seret kosong  kotak pilih    Klik kanan     menu konteks

MISI
  P / {MOD}+Enter        Generate waypoint dari urutan misi
  F5                    Simulasi: play / pause      Shift+F5  Stop
  F6                    Validasi misi
  F1                    Bantuan ini
"""
