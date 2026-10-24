import csv
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup
import pymupdf
from docx import Document

from app.config import settings


@dataclass
class ParsedSource:
    source: dict[str, Any]
    source_hash: str
    units: list[dict[str, Any]]


def load_manifest(dataset_dir: Path | None = None) -> tuple[Path, dict[str, Any]]:
    root = (dataset_dir or settings.dataset_path).resolve()
    manifest_path = root / "metadata" / "source_manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Dataset manifest not found: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest.get("sources"), list):
        raise ValueError("Dataset manifest must contain a sources list")
    return root, manifest


def _safe_source_path(root: Path, relative_path: str) -> Path:
    path = (root / relative_path).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"Manifest path escapes the dataset directory: {relative_path}") from exc
    if not path.is_file():
        raise FileNotFoundError(f"Manifest source does not exist: {relative_path}")
    if path.stat().st_size > settings.MAX_SOURCE_FILE_BYTES:
        raise ValueError(f"Source exceeds MAX_SOURCE_FILE_BYTES: {relative_path}")
    return path


def _source_hash(path: Path, declared_hash: str | None) -> str:
    raw_content = path.read_bytes()
    raw_hash = hashlib.sha256(raw_content).hexdigest()
    if path.suffix.lower() in {".html", ".htm", ".vtt", ".txt", ".md", ".json", ".csv"}:
        normalized_hash = hashlib.sha256(raw_content.replace(b"\r\n", b"\n")).hexdigest()
    else:
        normalized_hash = raw_hash
    if declared_hash:
        if declared_hash not in {raw_hash, normalized_hash}:
            raise ValueError(f"Source content hash does not match the manifest: {path.name}")
        return declared_hash
    return normalized_hash


def _text_unit(text: str, locator: dict[str, Any], **metadata: Any) -> dict[str, Any] | None:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return None
    return {"text": cleaned, "locator": locator, "metadata": metadata}


def _parse_pdf(path: Path) -> list[dict[str, Any]]:
    units: list[dict[str, Any]] = []
    with pymupdf.open(path) as document:
        for page_number, page in enumerate(document, start=1):
            unit = _text_unit(page.get_text("text"), {"page": page_number})
            if unit:
                units.append(unit)
    return units


def _parse_docx(path: Path) -> list[dict[str, Any]]:
    document = Document(path)
    units: list[dict[str, Any]] = []
    section = "Document"
    for paragraph_number, paragraph in enumerate(document.paragraphs, start=1):
        text = paragraph.text.strip()
        if not text:
            continue
        if paragraph.style.name.startswith("Heading"):
            section = text
        unit = _text_unit(
            text,
            {"section": section, "paragraph": paragraph_number},
        )
        if unit:
            units.append(unit)
    for table_number, table in enumerate(document.tables, start=1):
        for row_number, row in enumerate(table.rows, start=1):
            values = [cell.text.strip() for cell in row.cells]
            unit = _text_unit(
                " | ".join(value for value in values if value),
                {"section": f"Table {table_number}", "row": row_number},
            )
            if unit:
                units.append(unit)
    return units


def _parse_markdown(path: Path) -> list[dict[str, Any]]:
    units: list[dict[str, Any]] = []
    section = "Document"
    for line_number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        clean = line.strip()
        if not clean:
            continue
        heading = re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", clean)
        if heading:
            section = heading.group(1).strip()
            content = section
        else:
            content = clean
        unit = _text_unit(content, {"section": section, "line": line_number})
        if unit:
            units.append(unit)
    return units


def _parse_html(path: Path) -> list[dict[str, Any]]:
    soup = BeautifulSoup(path.read_text(encoding="utf-8", errors="replace"), "html.parser")
    for element in soup(["script", "style", "nav", "footer", "header", "noscript", "svg"]):
        element.decompose()
    main = soup.find("main") or soup.find("article") or soup.body or soup
    elements = main.find_all(["h1", "h2", "h3", "h4", "p", "li", "pre", "blockquote", "table"])
    page_title = soup.title.get_text(" ", strip=True) if soup.title else ""
    h1 = main.find("h1")
    intro_section = h1.get_text(" ", strip=True) if h1 else page_title

    def element_text(element: Any) -> str:
        if element.name == "table":
            return " | ".join(
                cell.get_text(" ", strip=True)
                for cell in element.find_all(["th", "td"])
            )
        return element.get_text(" ", strip=True)

    def section_unit(
        text_parts: list[str],
        section: str,
        html_id: str,
    ) -> dict[str, Any] | None:
        return _text_unit(
            " ".join(part for part in text_parts if part),
            {"section": section or "Webpage content", "html_id": html_id},
        )

    h2_elements = [element for element in elements if element.name == "h2"]
    if not h2_elements:
        unit = section_unit(
            [element_text(element) for element in elements],
            intro_section,
            "intro",
        )
        return [unit] if unit else []

    units: list[dict[str, Any]] = []
    current_group: list[Any] = []
    current_heading = ""
    current_id = ""

    def add_group() -> None:
        unit = section_unit(
            [element_text(element) for element in current_group],
            current_heading,
            current_id,
        )
        if unit:
            units.append(unit)

    for element in elements:
        if element.name == "h2":
            if current_heading:
                add_group()
            current_heading = element_text(element)
            current_id = element.get("id") or re.sub(
                r"\s+",
                "-",
                re.sub(r"[^a-z0-9 ]", "", current_heading.lower()),
            )
            current_group = [element]
        elif current_heading:
            current_group.append(element)

    if current_heading:
        add_group()

    first_h2_index = next(
        index for index, element in enumerate(elements)
        if element is h2_elements[0]
    )
    intro_elements = elements[:first_h2_index]
    intro_texts = [element_text(element) for element in intro_elements]
    intro_content = [
        text for element, text in zip(intro_elements, intro_texts)
        if element is not h1 and text
    ]
    if intro_content:
        intro_unit = section_unit(intro_texts, intro_section, "intro")
        if intro_unit:
            units.insert(0, intro_unit)

    return units


def _parse_vtt(path: Path) -> list[dict[str, Any]]:
    content = path.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
    blocks = re.split(r"\n\s*\n", content)
    units: list[dict[str, Any]] = []
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        timing_index = next((i for i, line in enumerate(lines) if "-->" in line), None)
        if timing_index is None:
            continue
        cue_id = lines[timing_index - 1] if timing_index > 0 else None
        timing = lines[timing_index].split("-->", 1)
        start = timing[0].strip().split(" ", 1)[0]
        end = timing[1].strip().split(" ", 1)[0]
        body = " ".join(lines[timing_index + 1:])
        # WebVTT voice tag "<v Name>text" first, then the plain "Name: text" style.
        speaker_match = (
            re.match(r"^<v(?:\.[\w.-]+)?\s+([^>]+)>(.*?)(?:</v>)?$", body)
            or re.match(r"^([A-Za-z][A-Za-z0-9 _.-]{0,40}):\s*(.*)$", body)
        )
        speaker = speaker_match.group(1).strip() if speaker_match else None
        if speaker_match:
            body = speaker_match.group(2)
        unit = _text_unit(body, {"cue_id": cue_id, "start": start, "end": end}, speaker=speaker)
        if unit:
            units.append(unit)
    return units


def _parse_text(path: Path) -> list[dict[str, Any]]:
    units: list[dict[str, Any]] = []
    section = "Transcript"
    for line_number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        clean = line.strip()
        if not clean:
            continue
        if len(clean) < 100 and clean.upper() == clean and re.search(r"[A-Z]", clean):
            section = clean
        unit = _text_unit(clean, {"section": section, "line": line_number})
        if unit:
            units.append(unit)
    return units


def _structured_records(value: Any) -> list[tuple[str, dict[str, Any]]]:
    records: list[tuple[str, dict[str, Any]]] = []
    if isinstance(value, list):
        candidates = [("record", item) for item in value if isinstance(item, dict)]
    elif isinstance(value, dict):
        candidates = []
        for key, child in value.items():
            if isinstance(child, list):
                candidates.extend((key, item) for item in child if isinstance(item, dict))
        if not candidates:
            candidates = [("record", value)]
    else:
        candidates = [("record", {"value": value})]
    for collection_name, item in candidates:
        identifier_key = next(
            (key for key in ("log_id", "event_id", "record_id", "dependency_id", "service_id", "id")
             if item.get(key) is not None),
            None,
        )
        identifier = str(item[identifier_key]) if identifier_key else f"{collection_name}-{len(records) + 1}"
        records.append((identifier, item))
    return records


def _parse_json(path: Path) -> list[dict[str, Any]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    units: list[dict[str, Any]] = []
    for record_id, record in _structured_records(value):
        text = " | ".join(
            f"{key}: {json.dumps(item, ensure_ascii=False) if isinstance(item, (dict, list)) else item}"
            for key, item in record.items()
        )
        timestamp = next(
            (record[key] for key in ("timestamp", "created_at", "received_at") if record.get(key)),
            None,
        )
        locator_key = next(
            (key for key in ("log_id", "event_id", "record_id", "dependency_id", "service_id", "id")
             if record.get(key) is not None),
            "record_id",
        )
        locator_value = record.get(locator_key, record_id)
        unit = _text_unit(
            text,
            {locator_key: locator_value, "timestamp": timestamp},
            record=record,
        )
        if unit:
            units.append(unit)
    return units


def _parse_csv(path: Path) -> list[dict[str, Any]]:
    units: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row_number, record in enumerate(csv.DictReader(handle), start=2):
            text = " | ".join(f"{key}: {value}" for key, value in record.items() if value is not None)
            row_id = record.get("row_id") or row_number
            timestamp = record.get("timestamp")
            unit = _text_unit(
                text,
                {"row_id": row_id, "line": row_number, "timestamp": timestamp},
                record=record,
            )
            if unit:
                units.append(unit)
    return units


def parse_source(root: Path, source: dict[str, Any]) -> ParsedSource:
    relative_path = source.get("file_path")
    if not isinstance(relative_path, str):
        raise ValueError("Manifest source is missing a file_path")
    path = _safe_source_path(root, relative_path)
    source_hash = _source_hash(path, source.get("sha256"))
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        units = _parse_pdf(path)
    elif suffix in {".html", ".htm"}:
        units = _parse_html(path)
    elif suffix == ".vtt":
        units = _parse_vtt(path)
    elif suffix == ".md":
        units = _parse_markdown(path)
    elif suffix == ".docx":
        units = _parse_docx(path)
    elif suffix == ".txt":
        units = _parse_text(path)
    elif suffix == ".json":
        units = _parse_json(path)
    elif suffix == ".csv":
        units = _parse_csv(path)
    elif suffix in {".png", ".jpg", ".jpeg", ".webp"}:
        from PIL import Image

        with Image.open(path) as image:
            image.verify()
        description = source.get("description", "")
        units = []
        unit = _text_unit(
            f"{source.get('title', path.name)}. Image metadata description: {description}",
            {"image": path.name, "analysis": "metadata_only", "ocr_analyzed": False},
        )
        if unit:
            units.append(unit)
    else:
        raise ValueError(f"Unsupported source format: {suffix or 'unknown'}")

    source_record = {
        **source,
        "file_path": relative_path.replace("\\", "/"),
        "source_hash": source_hash,
        "size_bytes": path.stat().st_size,
        "analysis_status": (
            "metadata_only"
            if suffix in {".png", ".jpg", ".jpeg", ".webp"}
            else ("parsed" if units else "no_extractable_text")
        ),
    }
    return ParsedSource(source=source_record, source_hash=source_hash, units=units)
