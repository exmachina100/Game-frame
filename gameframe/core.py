"""Adapter-neutral, frame-accurate 2D cinematic direction."""
from dataclasses import dataclass, field
import math


@dataclass(frozen=True)
class Action:
    actor: str
    start: int
    end: int
    x: float
    y: float


@dataclass
class Actor:
    name: str
    x: float
    y: float


@dataclass
class Camera:
    x: float = 0.0
    y: float = 0.0
    zoom: float = 1.0


@dataclass
class Director:
    adapter: object
    fps: int = 12
    scene: str = "retro_stage"
    actors: dict[str, Actor] = field(default_factory=dict)
    actions: list[Action] = field(default_factory=list)
    camera: Camera = field(default_factory=Camera)

    def load_scene(self, scene: str) -> dict:
        if scene not in self.adapter.info()["scenes"]:
            raise ValueError("Unsupported scene")
        self.scene = scene
        self.actors.clear()
        self.actions.clear()
        self.camera = Camera()
        return {"scene": scene}

    def spawn_actor(self, name: str, x: float, y: float) -> dict:
        if not name or name in self.actors or not all(map(math.isfinite, (x, y))):
            raise ValueError("Invalid or duplicate actor")
        self.actors[name] = Actor(name, x, y)
        return {"name": name, "x": x, "y": y}

    def direct_actor(self, actor: str, start: int, end: int, x: float, y: float) -> dict:
        if actor not in self.actors or start < 0 or end <= start or end > self.fps * 600:
            raise ValueError("Unknown actor or invalid frame interval")
        if not all(map(math.isfinite, (x, y))):
            raise ValueError("Invalid coordinates")
        if any(a.actor == actor and start < a.end and end > a.start for a in self.actions):
            raise ValueError("Overlapping actor actions")
        self.actions.append(Action(actor, start, end, x, y))
        return {"actor": actor, "start": start, "end": end, "destination": [x, y]}

    def actors_at(self, frame: int) -> dict[str, Actor]:
        if frame < 0:
            raise ValueError("Frame must be nonnegative")
        result = {key: Actor(v.name, v.x, v.y) for key, v in self.actors.items()}
        for name, actor in result.items():
            for action in sorted((a for a in self.actions if a.actor == name), key=lambda a: a.start):
                if frame < action.start:
                    break
                origin_x, origin_y = actor.x, actor.y
                fraction = min(1.0, (frame - action.start) / (action.end - action.start))
                actor.x = origin_x + (action.x - origin_x) * fraction
                actor.y = origin_y + (action.y - origin_y) * fraction
                if frame <= action.end:
                    break
        return result

    def render_frame(self, frame: int) -> bytes:
        return self.adapter.render(self.actors_at(frame), self.camera, frame)

    def manifest(self, frames: int) -> dict:
        if not isinstance(frames, int) or frames < 1 or frames > self.fps * 600:
            raise ValueError("Frames outside allowed range")
        return {"scene": self.scene, "fps": self.fps, "frames": frames,
                "actors": sorted(self.actors), "actions": [vars(a) for a in self.actions],
                "camera": vars(self.camera), "adapter": self.adapter.info()["id"]}
