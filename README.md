# Dialed

A radio-style player on top of YouTube's own player, so it uses the same catalogue and video IDs as music.youtube.com. Pick genres, tune in, and the station never runs out.

## Run it

1. Unzip the folder anywhere.
2. Start the local server. Windows: double-click `start.bat`. Mac/Linux: run `./start.sh`. Both run `serve.py`, a tiny local server built on Python 3's standard library, so you need Python 3.
3. Open **http://localhost:8765** in Brave. Don't double-click `index.html`: YouTube refuses to play for pages opened from disk.
4. Pick a few genres and press Start. No keys are needed. (Settings has an optional Anthropic key for the AI DJ.)

## Song search (no key needed)

By default Dialed finds songs with **keyless search**: it asks YouTube Music's own web search for songs, playlists and track details, from your computer, through the small local server (`serve.py`). There is nothing to sign up for and no daily quota to run out of. Playback still goes through YouTube's own embedded player.

**Please know what this is.** YouTube Music has no public API, so keyless search uses the same private web endpoints its website uses. That is not an official or supported route, and it goes against YouTube's terms of service. It can stop working at any time if YouTube changes things, and YouTube could limit your connection if it were abused (Dialed spaces out and caches its requests to stay gentle). Use it at your own risk. Settings > Song search > **Test search**, or `http://localhost:8765/check.html`, tells you whether it is working right now.

**Official route (optional backup).** For the supported option, make a free YouTube Data API key: Google Cloud console > create a project > APIs & Services > Library > "YouTube Data API v3" > Enable > Credentials > Create credentials > API key. Paste it in Settings, then either choose Official as the song search, or leave Keyless selected: with a key saved, Dialed switches to it automatically whenever keyless search fails. The free quota is 10,000 units a day and a search costs 100, so starting a three-genre station uses about 300; it resets at midnight Pacific.

## Keys

**Anthropic API key** (optional, for the AI DJ). console.anthropic.com > API keys. Billed per use; DJ lines on Haiku 5.5 cost a fraction of a cent each. Without a key the DJ still talks, using built-in lines.

Keys are stored in this browser only and sent only to the service they belong to. Keyless search sends only your search words to music.youtube.com, from your computer.

## The DJ's voice and persona

**Voice.** By default the DJ uses a natural voice that runs on your own computer: an open-source neural speech model (Kokoro-82M) with no account, no key and no per-line cost. The first time Dialed opens, it downloads the model once (about 90 MB from Hugging Face) and your browser keeps it, so later launches are quick. Nothing you type or play is sent anywhere for this voice. Until the download finishes he falls back to your browser's built-in voice, which sounds robotic.

Settings > DJ voice has:

- **Voice:** 22 voices (US and UK, male and female). The default, **Deep & smooth**, is a blend of two of the deepest male voices, and **Velvet baritone** is another blend. I measured the default at a median pitch of about 102 Hz, against about 112 Hz for the voice it replaced. Press **Hear the DJ** to audition them. They are standard US and UK English voices: none has a particular regional or cultural accent, and none imitates a real person.
- **Depth:** lowers the voice further, from natural pitch to Deepest. The default (Deep) takes the default voice to roughly 91 Hz and slows his delivery a touch.
- **Sound:** Silky (default: rumble filtered out, a little warmth, a soft top end and a touch of room), Radio (brighter and punchier) or Plain.
- **Pace:** a little slower, normal, or a little faster.

Lines are prepared ahead of time while the previous song plays, and the station greeting is made as soon as the voice loads, so he comes in on cue. On a slow computer the first line of a session can arrive a little late.

**Persona.** Settings > DJ persona holds who he is and how he talks. The default is DJ Dial, an original character: soul, R&B, hip-hop and jazz in one house, with big-hearted morning-show warmth, quick comic timing, playful banter and a deep, unhurried delivery when the groove calls for it. Radio-clean, and he never imitates a real person. Edit it freely; it shapes every line and every pick Claude writes (needs the Anthropic key; the built-in lines use the default style).

**ElevenLabs (optional).** For a cloud voice with more range and character:

1. Make an ElevenLabs account and copy an API key (your profile > API keys).
2. In Dialed open Settings > DJ voice, choose ElevenLabs, paste the key and press Load my voices.
3. Pick a voice and press Hear the DJ.

To find a voice that fits him, search ElevenLabs' Voice Library (Voices > Explore) or design one (Voices > Add a new voice > Voice Design) by describing the DJ in your own words. Voice Library voices need a paid ElevenLabs plan to work through the API; free accounts can use ElevenLabs' built-in voices. Each DJ line uses about 150 characters of your monthly allowance, so set "DJ talks" to every 2nd or 3rd song to stretch it. With ElevenLabs on, the text of each DJ line is sent to ElevenLabs.

## On your phone (Android and iPhone)

Dialed has a phone layout: a Radio / Search / Library tab bar, a mini player, and a full Now Playing screen with big controls. It runs in your phone's browser (Chrome, Brave or Safari). It is a web app, not an App Store or Play Store app.

**Connect your phone**

1. On your computer, start Dialed with `start-phone.bat` (Windows) or `./start-phone.sh` (Mac/Linux) instead of `start.bat`. Windows may ask to let Python through the firewall: allow it on Private networks.
2. On the computer, open `http://localhost:8765/phone.html`. It shows a QR code and the address to use.
3. On your phone, on the same Wi-Fi, scan the code or type the address.
4. Optional: add it to your home screen for a full-screen icon (iPhone: Share > Add to Home Screen. Android: browser menu > Add to Home screen or Install app).

Phone mode lets other devices on your Wi-Fi reach Dialed, so use it on networks you trust, and close the window when you are done. Plain `start.bat` still keeps Dialed to this computer only.

**What is different on a phone**

- **Keep the screen on, with Dialed in front.** YouTube pauses its embedded player when a phone's screen locks or the app goes to the background, on both iPhone and Android. Dialed asks the phone to stay awake while music plays.
- **iPhone has no crossfade.** iOS does not let a web page change volume at all, so Dialed plays songs back to back and the DJ talks between them instead of over the next song.
- **Android keeps crossfade and DJ ducking.** If your phone will not let Dialed start the second player by itself, Dialed notices after a few seconds, switches crossfade off, and says so.
- **Tap to play.** Phones sometimes refuse to start music until you tap. If nothing starts, the play button pulses and says "Tap the play button to start".
- **The DJ uses your phone's own voice by default.** The big on-device voice is optional and heavy for a phone. The equalizer needs the desktop extension, so it is not on phones. Use the phone's volume buttons.
- **The video** is a small thumbnail in the mini player and full width in Now Playing.
- Phone behaviour was tested with emulated phones and a stand-in for YouTube's player, not on real devices, so what you see may differ. YouTube's own rules for embedded players decide a lot here.

## Ad-free

Dialed embeds YouTube's own player and doesn't change what's inside it (a web page can't). Ad blocking is your browser's job: run Dialed in Brave with Shields on at its default (Standard) setting. Brave blocks YouTube's ad requests at the network level and updates its filters when YouTube changes things. That can't be guaranteed forever. If an ad does get through, the crossfade timing for that song can be off. Aggressive mode can block YouTube's player script itself, which stops Dialed from starting (see Troubleshooting).

## Equalizer

Browsers don't let a page touch the audio inside a YouTube frame, so the EQ lives in a small companion extension (`eq-extension/content.js`, short enough to read in a couple of minutes):

1. In Brave open `brave://extensions` and switch on Developer mode.
2. Click Load unpacked and choose the `eq-extension` folder.
3. Reload Dialed, open the EQ tab and switch it on.

The extension only runs inside player frames embedded by a page on localhost, and it doesn't touch the audio until you switch the EQ on. The EQ tab tells you if it can't find the extension.

## What it does

- **Radio:** 30 genres on a tuning dial, an era filter, quick mixes and saved mixes. "DJ picks the songs" lets Claude choose each batch.
- **Crossfade:** 0 to 30 seconds (default 30), equal-power, with the video dissolving too. A blend never exceeds 40% of a song's length.
- **AI DJ:** spoken links over each transition (voice and frequency in Settings), music ducks while it talks, and the DJ tab takes requests ("something mellow for focus").
- **Equalizer:** 10 bands, preamp, presets and a live spectrum (needs the extension).
- **Library:** search, paste any music.youtube.com link (song or playlist), likes, playlists, recently played, and a song radio from any track.
- **Player:** queue with play next, add and drag to reorder; shuffle, repeat, sleep timer, media keys.
- **Keys:** Space play/pause, Shift+Left/Right previous/next, Up/Down volume, M mute, L like, S shuffle, R repeat, / search.

Not included: lyrics, offline downloads, multi-device control, social features, podcasts, account sync. Volume and crossfade don't work on iPhone or iPad, which ignore volume set by a page.

## Troubleshooting

- **The video panel says "Loading YouTube's player", "Still waiting for YouTube's player script" or "frames aren't answering":** open **http://localhost:8765/check.html**. It tests YouTube's player on its own, step by step, on both YouTube hosts, and says what's wrong. In Brave, click the lion icon and turn Shields down for localhost, then reload. If only the youtube.com frame fails and the youtube-nocookie.com one works, set Settings > "YouTube player host" to youtube-nocookie.com and reload.
- **"Video player configuration error" (153):** the page was opened from disk or through something that strips the Referer. Use the localhost address.
- **A song is skipped with "YouTube won't play it here":** some videos block embedding or are region-locked. Normal; Dialed moves on.
- **Black stage and no sound:** press play once more, and check nothing is blocking youtube.com.
- **EQ says "Connected, but the browser is holding the audio back":** click once inside the video, or pause and play.
- **Keyless search says it isn't working, or stations come back empty:** open **http://localhost:8765/check.html** and press Run search test. "Refused (blocked)" means YouTube Music is limiting your connection for a while; "changed shape" means YouTube changed its pages and Dialed needs an update. Either way, adding a YouTube Data API key in Settings makes Dialed use the official route automatically.
- **"Keyless search needs the new server":** you are running an old server window. Close it and start Dialed with `start.bat` or `start.sh` from this folder.
- **The DJ still sounds robotic:** open Settings > DJ voice. It should say "Natural voice on this computer", and the status under it should say Ready. While it says Downloading, he uses the browser voice. If it says it couldn't load: make sure you opened Dialed through `start.bat` or `start.sh` (not by double-clicking `index.html`), check that Brave Shields or a firewall isn't blocking `huggingface.co`, and press **Try again**. If your network blocks it, choose ElevenLabs or the browser voice instead.
- **No DJ voice at all:** check the DJ mic button in the player bar is on.

## Credits

Fonts: Barlow Semi Condensed and Doto, SIL Open Font License (see `fonts/`).
Keyless search follows the request format of the open-source ytmusicapi project (MIT). Dialed is not affiliated with YouTube or Google.
Voice: Kokoro-82M by hexgrad, run in the browser with kokoro-js and Transformers.js (Apache-2.0), ONNX Runtime Web (MIT) and eSpeak NG (GPL-3.0, embedded in the phonemizer package). Full notices in `NOTICES.txt`; license files in `tts/licenses/`.
