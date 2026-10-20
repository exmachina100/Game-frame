"""V4 capture transport for custom ioquake3 client patched with capture support."""
import re
from .ioquake3_render_camera import IoQuake3RenderCamera

class IoQuake3ProductionBridge(IoQuake3RenderCamera):
    def capture(self,name):
        if not isinstance(name,str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,96}",name):
            raise ValueError("Capture name must be alphanumeric, underscore or hyphen")
        ack=self._send("gfcapture "+name)
        return {**ack,"name":name,"file_verified":False}
