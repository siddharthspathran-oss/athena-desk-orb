// Athena's desk orb: shows what Athena is doing, and its button makes her listen.
//
//   ESP32 board alone  - the on-board blue LED: on while listening, fast blink
//                        while thinking, flicker while speaking, a short blip
//                        every two seconds when idle, nothing if Athena is off.
//   + WS2812B ring     - data pin to GPIO 13 (5V/GND to the ring): the full orb,
//                        in the HUD's colours. Set LEDS in athena.h to its size.
//   BOOT button        - press: "Athena, listen" (same as the HUD's mic button).
//
// First boot: no Wi-Fi saved, so the orb opens its own network "Athena-Orb".
// Join it from your phone; a page opens where YOU pick your Wi-Fi and type its
// password - it is kept on the orb only, never in this code. Hold BOOT while
// powering on to forget it and choose again.
//
// It talks to Athena's web interface (port 8420) with its own key, which can
// only read her state and press listen (jarvis/ui/web.py /orb).
#include <Arduino.h>
#include <ArduinoJson.h>
#include <ESPmDNS.h>
#include <FastLED.h>
#include <HTTPClient.h>
#include <WiFi.h>
#include <WiFiManager.h>

#include "athena.h"   // ATHENA_HOST, ATHENA_IP, ORB_KEY, LEDS - made by make_config.py

#define LED_PIN 13
#define ONBOARD 2
#define BUTTON 0

CRGB ring[LEDS > 0 ? LEDS : 1];
String state = "offline";
float level = 0;
unsigned long lastOk = 0, lastPoll = 0, pressedAt = 0;
String base;  // http://host:8420

// The HUD's colours (FACE_COL in hud.html).
CRGB colourOf(const String &s) {
  if (s == "listening") return CRGB(0xF7, 0xA4, 0x43);
  if (s == "thinking") return CRGB(0x8F, 0x72, 0xFF);
  if (s == "speaking") return CRGB(0xFF, 0x5F, 0xB8);
  if (s == "muted") return CRGB(0xFF, 0x8C, 0x00);
  if (s == "offline" || s == "stopped") return CRGB(0x60, 0x00, 0x00);
  return CRGB(0xC4, 0xA8, 0xFF);  // idle
}

String findAthena() {
  // The PC by name first (its address can change), then the address it had.
  IPAddress ip = MDNS.queryHost(ATHENA_HOST, 2000);
  if (ip != IPAddress(0, 0, 0, 0)) return "http://" + ip.toString() + ":8420";
  return String("http://") + ATHENA_IP + ":8420";
}

void poll() {
  HTTPClient http;
  http.setTimeout(800);
  http.begin(base + "/orb");
  http.addHeader("X-Orb-Key", ORB_KEY);
  int code = http.GET();
  if (code == 200) {
    JsonDocument j;
    if (!deserializeJson(j, http.getString())) {
      state = j["s"] | "idle";
      level = j["l"] | 0.0f;
      lastOk = millis();
    }
  } else if (code == 401) {
    Serial.println("Athena refused the orb key - run make_config.py again and re-upload.");
  }
  http.end();
  if (millis() - lastOk > 4000) {
    state = "offline";
    if (millis() - lastOk > 15000) {  // the PC may have a new address
      base = findAthena();
      lastOk = millis() - 4001;
    }
  }
}

void listen() {
  HTTPClient http;
  http.begin(base + "/orb/listen");
  http.addHeader("X-Orb-Key", ORB_KEY);
  int code = http.POST("");
  http.end();
  Serial.printf("listen -> %d\n", code);
}

void drawRing(unsigned long t) {
  if (LEDS == 0) return;
  CRGB c = colourOf(state);
  float breathe = 0.5f + 0.5f * sinf(t / 900.0f);
  for (int i = 0; i < LEDS; i++) {
    CRGB p = c;
    if (state == "idle") p.nscale8(30 + 60 * breathe);
    else if (state == "listening") p.nscale8(90 + min(165.0f, level * 260));
    else if (state == "thinking") {  // a comet going round
      int head = (t / 60) % LEDS, d = (head - i + LEDS) % LEDS;
      p.nscale8(d < 5 ? 255 - d * 50 : 12);
    } else if (state == "speaking") p.nscale8(120 + 120 * (0.5f + 0.5f * sinf(t / 90.0f + i)));
    else p.nscale8(10 + 30 * breathe);  // offline / muted / stopped: dim
    ring[i] = p;
  }
  if (millis() - pressedAt < 300) fill_solid(ring, LEDS, CRGB::White);  // your press, seen
  FastLED.show();
}

void drawOnboard(unsigned long t) {
  bool on;
  if (millis() - pressedAt < 300) on = true;
  else if (state == "listening") on = true;
  else if (state == "thinking") on = (t / 120) % 2;
  else if (state == "speaking") on = random(3) > 0;
  else if (state == "idle") on = (t % 2000) < 60;
  else on = false;  // Athena not running
  digitalWrite(ONBOARD, on);
}

void setup() {
  Serial.begin(115200);
  pinMode(ONBOARD, OUTPUT);
  pinMode(BUTTON, INPUT_PULLUP);
  if (LEDS > 0) {
    FastLED.addLeds<WS2812B, LED_PIN, GRB>(ring, LEDS);
    FastLED.setBrightness(120);
    fill_solid(ring, LEDS, CRGB(0x20, 0x10, 0x40));
    FastLED.show();
  }
  WiFiManager wm;
  if (digitalRead(BUTTON) == LOW) wm.resetSettings();  // BOOT held at power-on: choose Wi-Fi again
  wm.setConfigPortalTimeout(300);
  if (!wm.autoConnect("Athena-Orb")) ESP.restart();
  Serial.printf("Wi-Fi ok: %s\n", WiFi.localIP().toString().c_str());
  MDNS.begin("athena-orb");
  base = findAthena();
  Serial.println("Athena at " + base);
}

void loop() {
  unsigned long t = millis();
  static bool wasDown = false;
  bool down = digitalRead(BUTTON) == LOW;
  if (down && !wasDown && t - pressedAt > 600) {
    pressedAt = t;
    listen();
  }
  wasDown = down;
  if (t - lastPoll > 150) {
    lastPoll = t;
    poll();
  }
  drawRing(t);
  drawOnboard(t);
  delay(15);
}
