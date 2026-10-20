"""Produce a native procedural sample shot as lossless PPM frames."""
from pathlib import Path
from .core import Director
from .stage import RetroStage


def main():
    d = Director(RetroStage())
    d.spawn_actor("detective", -100, 0)
    d.spawn_actor("stranger", 100, 0)
    d.direct_actor("detective", 0, 100, -20, 0)
    d.direct_actor("stranger", 20, 110, 25, 0)
    dest = Path("output/demo")
    dest.mkdir(parents=True, exist_ok=True)
    for i in range(144):
        (dest / f"shot_{i:04d}.ppm").write_bytes(d.render_frame(i))
    print("Created 144 frames in output/demo. Encode with FFmpeg (see README).")


if __name__ == "__main__":
    main()
