// Copy to athena.h (or run make_config.py, which writes it for you).
// athena.h is git-ignored: it holds the orb's key.
#pragma once
#define ATHENA_HOST "MY-PC"          // the PC's hostname (found over mDNS first)
#define ATHENA_IP "192.168.1.10"     // fallback LAN IP of the PC running Athena
#define ORB_KEY "paste-the-orb-key"  // Athena's data/orb_key.txt: read state + press listen only
#define LEDS 16                      // WS2812B ring size; 0 = on-board LED only
