import json
import csv
import logging
import uuid
from pathlib import Path

from app.models.schemas import FAQItem, Language
from app.config import settings

logger = logging.getLogger(__name__)


class FAQIngestion:
    def __init__(self):
        self.data_dir = Path(settings.faq_data_dir)

    def load_from_json(self, file_path: str) -> list[FAQItem]:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        items = []
        for entry in data:
            lang = Language(entry.get("language", "en"))
            items.append(FAQItem(
                id=entry.get("id", str(uuid.uuid4())),
                question=entry["question"],
                answer=entry["answer"],
                category=entry.get("category", ""),
                language=lang,
            ))
        logger.info(f"Loaded {len(items)} FAQ items from {file_path}")
        return items

    def load_from_csv(self, file_path: str) -> list[FAQItem]:
        items = []
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                lang = Language(row.get("language", "en"))
                items.append(FAQItem(
                    id=row.get("id", str(uuid.uuid4())),
                    question=row["question"],
                    answer=row["answer"],
                    category=row.get("category", ""),
                    language=lang,
                ))
        logger.info(f"Loaded {len(items)} FAQ items from {file_path}")
        return items

    def load_from_markdown(self, file_path: str) -> list[FAQItem]:
        items = []
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        sections = content.split("\n## ")
        for section in sections[1:]:
            lines = section.strip().split("\n")
            if len(lines) >= 2:
                question = lines[0].strip()
                answer = "\n".join(lines[1:]).strip()
                items.append(FAQItem(
                    id=str(uuid.uuid4()),
                    question=question,
                    answer=answer,
                    category="general",
                    language=Language.ENGLISH,
                ))
        logger.info(f"Loaded {len(items)} FAQ items from {file_path}")
        return items

    def load_from_text(self, file_path: str) -> list[FAQItem]:
        items = []
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        pairs = content.split("\n\n")
        for pair in pairs:
            lines = pair.strip().split("\n")
            if len(lines) >= 2:
                question = lines[0].strip().replace("Q: ", "")
                answer = lines[1].strip().replace("A: ", "")
                items.append(FAQItem(
                    id=str(uuid.uuid4()),
                    question=question,
                    answer=answer,
                    category="general",
                    language=Language.ENGLISH,
                ))
        logger.info(f"Loaded {len(items)} FAQ items from {file_path}")
        return items

    def load_all(self) -> list[FAQItem]:
        all_items = []
        if not self.data_dir.exists():
            self.data_dir.mkdir(parents=True, exist_ok=True)
            return all_items

        for file_path in self.data_dir.glob("*"):
            if file_path.suffix == ".json":
                all_items.extend(self.load_from_json(str(file_path)))
            elif file_path.suffix == ".csv":
                all_items.extend(self.load_from_csv(str(file_path)))
            elif file_path.suffix == ".md":
                all_items.extend(self.load_from_markdown(str(file_path)))
            elif file_path.suffix == ".txt":
                all_items.extend(self.load_from_text(str(file_path)))

        logger.info(f"Total FAQ items loaded: {len(all_items)}")
        return all_items

    def load_file(self, file_path: str) -> list[FAQItem]:
        path = Path(file_path)
        if path.suffix == ".json":
            return self.load_from_json(file_path)
        elif path.suffix == ".csv":
            return self.load_from_csv(file_path)
        elif path.suffix == ".md":
            return self.load_from_markdown(file_path)
        elif path.suffix == ".txt":
            return self.load_from_text(file_path)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")
