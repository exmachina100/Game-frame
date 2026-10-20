"""Procedural PPM retro game stage, using no third-party game assets."""
from .core import Actor, Camera


class RetroStage:
    width = 320
    height = 180

    def info(self) -> dict:
        return {"id": "retro-stage-v1", "scenes": ["retro_stage"],
                "capabilities": ["spawn_actor", "direct_actor", "static_camera", "capture"],
                "width": self.width, "height": self.height}

    def render(self, actors: dict[str, Actor], camera: Camera, frame: int) -> bytes:
        w, h = self.width, self.height
        pixels = bytearray(w * h * 3)
        for y in range(h):
            for x in range(w):
                color = ((12, 19, 32) if y < 100 else
                         (20, 27, 39) if y < 140 else (36, 46, 55))
                if y < 100 and x % 62 in (1, 2, 3):
                    color = (39, 51, 70)
                idx = (y * w + x) * 3
                pixels[idx:idx + 3] = bytes(color)

        def rect(x: int, y: int, width: int, height: int, color: tuple[int, int, int]):
            for yy in range(max(0, y), min(h, y + height)):
                for xx in range(max(0, x), min(w, x + width)):
                    idx = (yy * w + xx) * 3
                    pixels[idx:idx + 3] = bytes(color)

        for a in actors.values():
            x = int((a.x - camera.x) * camera.zoom + w / 2)
            y = int((a.y - camera.y) * camera.zoom + 119)
            rect(x - 7, y - 14, 14, 17, (236, 181, 88))
            rect(x - 5, y - 23, 10, 9, (228, 187, 144))
            rect(x - 6, y + 3, 5, 9, (18, 21, 29))
            rect(x + 1, y + 3, 5, 9, (18, 21, 29))
        return f"P6\n{w} {h}\n255\n".encode() + pixels
