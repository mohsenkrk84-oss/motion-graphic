"""Mix ElevenLabs voiceover, music and SFX for the HPV reel (timed from timing.json)."""
import json, os, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
A = os.environ.get("AUD", "/home/claude/hpv_audio")
T = json.load(open(os.path.join(HERE, "timing.json")))
sc, cr = T["scenes"], T["cross"]

events = [("pop", 0.0, 0.55)]
events += [("whoosh", sc[i] - 0.08, 0.5) for i in (1, 2, 3, 5)]
events += [("scribble", c, 0.55) for c in cr]
events += [("pop", cr[1] + 0.2, 0.4)]
events += [("doorbell", sc[4] + 0.02, 0.5), ("chime", sc[5] + 0.15, 0.6)]

inputs = ["-i", f"{A}/vo_edit.wav", "-i", f"{A}/music.mp3"]
f = ["[0:a]aformat=sample_rates=44100:channel_layouts=stereo,apad=whole_dur=20,asplit=2[vo][sc]",
     "[1:a]aformat=sample_rates=44100:channel_layouts=stereo,atrim=0:20,volume=0.32,afade=t=out:st=18.8:d=1.2[mus]",
     "[mus][sc]sidechaincompress=threshold=0.04:ratio=6:attack=20:release=300[duck]"]
labels = ["[vo]", "[duck]"]
for j, (name, t, vol) in enumerate(events):
    inputs += ["-i", f"{A}/{name}.mp3"]
    ms = int(max(0, t) * 1000)
    f.append(f"[{j + 2}:a]aformat=sample_rates=44100:channel_layouts=stereo,volume={vol},adelay={ms}|{ms}[e{j}]")
    labels.append(f"[e{j}]")
f.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0,atrim=0:20,loudnorm=I=-14:TP=-1.5[out]")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(f),
                "-map", "[out]", "-ar", "44100", f"{A}/mix.wav"], check=True)
print("mix ok", events)
