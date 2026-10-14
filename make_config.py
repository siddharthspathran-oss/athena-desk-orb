"""Write include/athena.h: where Athena is, and the orb's key.

    python make_config.py            # then: pio run -t upload
    python make_config.py --leds 16  # once the WS2812B ring is connected (its LED count)

The key comes from Athena (data/orb_key.txt - read state, press listen,
nothing else). athena.h is in .gitignore: it holds that key.
"""
import socket
import sys
from pathlib import Path

sys.path.insert(0, r"C:\claude code\jarvis")
from jarvis.ui.web import orb_key  # noqa: E402


def lan_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("192.168.1.1", 9))      # no packet is sent; it only picks the Wi-Fi interface
        return s.getsockname()[0]
    finally:
        s.close()


leds = int(sys.argv[sys.argv.index("--leds") + 1]) if "--leds" in sys.argv else 0
out = Path(__file__).parent / "include" / "athena.h"
out.parent.mkdir(exist_ok=True)
out.write_text(
    "// Made by make_config.py - do not commit (it holds the orb key).\n#pragma once\n"
    f'#define ATHENA_HOST "{socket.gethostname()}"\n'
    f'#define ATHENA_IP "{lan_ip()}"\n'
    f'#define ORB_KEY "{orb_key()}"\n'
    f"#define LEDS {leds}\n", encoding="utf-8")
print(f"Wrote {out}: Athena on {socket.gethostname()} / {lan_ip()}, {leds} LEDs.")
