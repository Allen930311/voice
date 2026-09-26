"""
Migrate profiles from dev data dir to App data dir.
Copies both SQLite records and WAV files.
"""
import sqlite3
import shutil
from pathlib import Path

DEV_DB = Path("C:/Users/Allen/OneDrive/Desktop/Voicebox/data/voicebox.db")
APP_DB = Path("C:/Users/Allen/AppData/Roaming/sh.voicebox.app/voicebox.db")
DEV_PROFILES = Path("C:/Users/Allen/OneDrive/Desktop/Voicebox/data/profiles")
APP_PROFILES = Path("C:/Users/Allen/AppData/Roaming/sh.voicebox.app/profiles")

dev = sqlite3.connect(DEV_DB)
dev.row_factory = sqlite3.Row
app = sqlite3.connect(APP_DB)
app.row_factory = sqlite3.Row

# Get existing App profile IDs to avoid duplication
existing = {r["id"] for r in app.execute("SELECT id FROM profiles")}
print(f"App already has {len(existing)} profiles: {existing}\n")

# Get dev profiles schema columns (intersect with app schema)
dev_cols = [r[1] for r in dev.execute("PRAGMA table_info(profiles)")]
app_cols = [r[1] for r in app.execute("PRAGMA table_info(profiles)")]
common_cols = [c for c in dev_cols if c in app_cols]
print(f"Common profile columns: {common_cols}\n")

dev_profiles = dev.execute("SELECT * FROM profiles").fetchall()
migrated = []
skipped = []

for p in dev_profiles:
    pid = p["id"]
    if pid in existing:
        skipped.append((pid, p["name"]))
        continue

    # Insert profile record using only common columns
    vals = {c: p[c] for c in common_cols}
    placeholders = ", ".join(f":{c}" for c in common_cols)
    cols_str = ", ".join(common_cols)
    app.execute(f"INSERT INTO profiles ({cols_str}) VALUES ({placeholders})", vals)

    # Copy WAV files
    src_dir = DEV_PROFILES / pid
    dst_dir = APP_PROFILES / pid
    if src_dir.exists():
        shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)
        wav_count = len(list(dst_dir.glob("*.wav")))
        print(f"  [OK] {p['name']} ({pid[:8]}...) — {wav_count} WAV copied")
    else:
        print(f"  [WARN] {p['name']} ({pid[:8]}...) — no WAV folder found")

    migrated.append(pid)

# Migrate profile_samples for migrated profiles
if migrated:
    dev_scols = [r[1] for r in dev.execute("PRAGMA table_info(profile_samples)")]
    app_scols = [r[1] for r in app.execute("PRAGMA table_info(profile_samples)")]
    common_scols = [c for c in dev_scols if c in app_scols]

    placeholders = ", ".join(f":{c}" for c in common_scols)
    cols_str = ", ".join(common_scols)
    for pid in migrated:
        samples = dev.execute(
            "SELECT * FROM profile_samples WHERE profile_id = ?", (pid,)
        ).fetchall()
        for s in samples:
            vals = {c: s[c] for c in common_scols}
            app.execute(
                f"INSERT OR IGNORE INTO profile_samples ({cols_str}) VALUES ({placeholders})",
                vals,
            )

app.commit()
dev.close()
app.close()

print(f"\nDone. Migrated: {len(migrated)}, Skipped (already exists): {len(skipped)}")
if skipped:
    for pid, name in skipped:
        print(f"  skip: {name} ({pid[:8]}...)")
