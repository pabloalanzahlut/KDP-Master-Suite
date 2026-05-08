import re
from pathlib import Path
from core.main import KDPMaster

BASE_DIR = Path(__file__).resolve().parent.parent
SUBTITLES_DIR = BASE_DIR / "subs"
OUTPUT_KNOWLEDGE_FILE = BASE_DIR / "knowledge_units" / "kdp_patterns.md"


def clean_text(text: str) -> str:
    text = re.sub(r"\d+\n", "", text)
    text = re.sub(r"\d{2}:\d{2}:\d{2}.*?\n", "", text)
    text = re.sub(r"<.*?>", "", text)
    text = re.sub(r"\n+", "\n", text)
    return text.strip()


def main():
    print("🔍 Procesando subtítulos...")

    if not SUBTITLES_DIR.exists():
        print(f"❌ Carpeta no encontrada: {SUBTITLES_DIR}")
        return

    master = KDPMaster()

    processed = 0

    for file in SUBTITLES_DIR.iterdir():
        if file.suffix.lower() not in [".srt", ".vtt", ".txt"]:
            continue

        raw_text = file.read_text(encoding="utf-8", errors="ignore")
        clean = clean_text(raw_text)

        if len(clean) < 200:
            continue

        identifier = file.stem

        master.process_transcription(
            identifier=identifier,
            content=clean
        )

        # APPEND a la base de conocimiento
        OUTPUT_KNOWLEDGE_FILE.parent.mkdir(parents=True, exist_ok=True)

        with open(OUTPUT_KNOWLEDGE_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n\n## Fuente: {identifier}\n\n")
            f.write(clean[:3000])
            f.write("\n\n---\n")

        processed += 1

    print(f"✅ Transcripciones procesadas: {processed}")


if __name__ == "__main__":
    main()
