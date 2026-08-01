import asyncio, os, sys, time, tempfile, base64

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.chdir(BASE_DIR)

import numpy as np
import sounddevice as sd
import httpx

LANG_CHOICES = {"1": "en", "2": "ar"}
SAMPLE_RATE = 16000
SERVER = "http://127.0.0.1:8000"


async def play_pcm(data: bytes, sample_rate: int = 24000):
    import soundfile as sf
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        path = f.name
    try:
        sf.write(path, np.frombuffer(data, dtype=np.int16), sample_rate)
        data_sf, rate = sf.read(path)
        sd.play(data_sf, rate)
        sd.wait()
    finally:
        os.remove(path)


async def record_until_silence(samplerate: int = SAMPLE_RATE, max_duration: float = 8.0,
                               silence_after: float = 0.9):
    block = int(0.2 * samplerate)
    chunks = []
    silent_secs = 0.0
    started = False
    total = 0.0
    peak = 0
    with sd.InputStream(samplerate=samplerate, channels=1, dtype="int16", blocksize=block) as stream:
        while total < max_duration:
            data, _ = stream.read(block)
            frame = data[:, 0]
            total += 0.2
            amp = np.abs(frame.astype(np.int16))
            peak = max(peak, int(amp.max()))
            if np.sqrt(np.mean(amp.astype(np.float64) ** 2)) > 80:
                started = True
                silent_secs = 0.0
            else:
                silent_secs += 0.2
            chunks.append(frame.copy())
            if started and silent_secs >= silence_after:
                break
    if not started:
        return None, peak
    audio = np.concatenate(chunks)
    idx = np.where(np.abs(audio) > 80)[0]
    return audio[idx[0]:idx[-1] + 1], peak


async def main():
    print("=" * 50)
    print("  AI CALL CENTER - LOCAL VOICE TEST")
    print("  Press ENTER to talk, then speak.")
    print("  Say 'quit' to exit.")
    print("=" * 50)

    lang = "en"
    while True:
        choice = input("Language: 1=English 2=Arabic [1]: ").strip() or "1"
        if choice in LANG_CHOICES:
            lang = LANG_CHOICES[choice]
            break
        print("Invalid, try again")

    while True:
        prompt = input("\n[ENTER] to speak, 'q' to quit: ").strip()
        if prompt.lower() == "q":
            print("bye")
            break

        print("Listening... (talk, stops when you pause)")
        audio, peak = await record_until_silence()
        if audio is None or len(audio) < SAMPLE_RATE * 0.3:
            print(f"(nothing heard - mic level {peak})")
            continue

        t0 = time.time()
        audio_bytes = audio.astype(np.int16).tobytes()
        r = httpx.post(f"{SERVER}/api/stt",
                       json={"audio": base64.b64encode(audio_bytes).decode("ascii"),
                             "language": lang, "sample_rate": SAMPLE_RATE}, timeout=120)
        text = r.json().get("text", "")
        if not text.strip():
            print("(could not understand)")
            continue
        print(f"YOU: {text}")

        if text.strip().lower() == "quit":
            print("bye")
            break

        r = httpx.post(f"{SERVER}/api/test-call",
                       json={"message": text, "language": lang}, timeout=120)
        answer = r.json()["response"]
        print(f"AI:  {answer}  ({time.time()-t0:.0f}s)")

        r = httpx.post(f"{SERVER}/api/tts",
                       json={"text": answer, "language": lang}, timeout=60)
        audio_data = base64.b64decode(r.json()["audio"])
        await play_pcm(audio_data)


if __name__ == "__main__":
    asyncio.run(main())
