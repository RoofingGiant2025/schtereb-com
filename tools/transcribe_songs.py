#!/usr/bin/env python3
"""Transcribe the released songs' local masters with on-device Whisper (mlx-whisper, Apple silicon).
Output: content/songs/transcripts/<apple_id>.json + .txt
Lines are Whisper segments; a pause > 1.6 s starts a new stanza. These are DRAFTS for the author's proofreading."""
import os, json, subprocess, sys, time
import soundfile as sf, mlx_whisper

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "content", "songs", "transcripts")
os.makedirs(OUT, exist_ok=True)
songs = json.load(open(os.path.join(ROOT, "content", "songs", "apple-catalog.json")))
masters = json.load(open(os.path.join(ROOT, "content", "songs", "local-masters.json")))
MODEL = "mlx-community/whisper-large-v3-turbo"
HINT = {"Aquí y Ahora": "es", "Uno Perdido": "es", "C****n": "es", "NUMÉRO UN": "fr"}
only = set(sys.argv[1:])

for s in songs:
    f = masters.get(s["title"])
    if not f or (only and str(s["apple_id"]) not in only):
        continue
    dst = os.path.join(OUT, f'{s["apple_id"]}.json')
    if os.path.exists(dst):
        continue
    wav = "/tmp/claude-501/tr16k.wav"
    subprocess.run(["afconvert", "-f", "WAVE", "-d", "LEI16@16000", "-c", "1", f, wav], check=True, capture_output=True)
    audio, sr = sf.read(wav, dtype="float32")
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    t0 = time.time()
    r = mlx_whisper.transcribe(audio, path_or_hf_repo=MODEL, language=HINT.get(s["title"]),
                               condition_on_previous_text=False, no_speech_threshold=0.5,
                               compression_ratio_threshold=2.2, temperature=(0.0, 0.2, 0.4))
    segs = [{"start": round(x["start"], 2), "end": round(x["end"], 2), "text": x["text"].strip()}
            for x in r["segments"] if x["text"].strip()]
    lines, prev_end = [], None
    for x in segs:
        if prev_end is not None and x["start"] - prev_end > 1.6:
            lines.append("")
        lines.append(x["text"])
        prev_end = x["end"]
    json.dump({"apple_id": s["apple_id"], "title": s["title"], "released": s["released"], "source_file": f,
               "language": r.get("language"), "model": MODEL, "segments": segs, "lines": lines},
              open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    open(dst[:-5] + ".txt", "w", encoding="utf-8").write(s["title"] + "\n\n" + "\n".join(lines) + "\n")
    print(f'{s["title"]} | {r.get("language")} | {len(segs)} segs | {time.time() - t0:.0f}s', flush=True)
print("done")
