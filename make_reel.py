#!/usr/bin/env python3
"""Make the Instagram Reel version of a carousel (1080x1920 MP4, silent).

Usage: python3 make_reel.py posts/YYYY-MM-DD/<id>
Needs the story frames first (python3 make_stories.py posts/YYYY-MM-DD/<id>).
Writes posts/YYYY-MM-DD/<id>_reel.mp4: all six story frames in order, 3 seconds each
(the business card holds 4 seconds), with a short crossfade between frames.

The file has a silent audio track on purpose. The music is the trending Instagram audio
the Brain picks (spec field "music"), attached by Metricool at scheduling time through
instagramData.audioConfiguration. Never bake a song into this file.
"""
import glob, os, subprocess, sys

prefix = sys.argv[1]
frames = sorted(glob.glob(prefix + "_story_[0-9]*of*.jpg"),
                key=lambda f: int(f.rsplit("_", 1)[1].split("of")[0]))
if not frames:
    sys.exit("No story frames found. Run make_stories.py first.")

HOLD, LAST_HOLD, FADE, FPS = 3.0, 4.0, 0.4, 30
durs = [HOLD] * (len(frames) - 1) + [LAST_HOLD]

cmd = ["ffmpeg", "-loglevel", "error", "-y"]
for f, d in zip(frames, durs):
    cmd += ["-loop", "1", "-t", f"{d + FADE:.2f}", "-framerate", str(FPS), "-i", f]
cmd += ["-f", "lavfi", "-t", f"{sum(durs) + FADE:.2f}", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"]

# chain crossfades: [0][1]xfade -> v1, [v1][2]xfade -> v2, ...
parts, prev, offset = [], "0:v", 0.0
for i in range(1, len(frames)):
    offset += durs[i - 1]
    out = f"v{i}"
    parts.append(f"[{prev}][{i}:v]xfade=transition=fade:duration={FADE}:offset={offset:.2f}[{out}]")
    prev = out
# xfade offsets are measured on the output timeline; each fade overlaps the next input
# by FADE seconds, so pad each input by FADE (done above with -t d+FADE) and keep offsets
# at the cumulative hold times.
parts.append(f"[{prev}]format=yuv420p,scale=1080:1920,setsar=1[vout]")
cmd += ["-filter_complex", ";".join(parts), "-map", "[vout]", "-map", f"{len(frames)}:a",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-r", str(FPS),
        "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart",
        prefix + "_reel.mp4"]
subprocess.run(cmd, check=True)
print(prefix + "_reel.mp4")
