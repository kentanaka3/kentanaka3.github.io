#!/usr/bin/env python3

import argparse
import json
import sys
from collections import Counter
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit


def require(condition, message):
    if not condition:
        raise ValueError(message)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"Duplicate JSON key: {key}")
        result[key] = value
    return result


class SiteParser(HTMLParser):
    void_tags = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self):
        super().__init__()
        self.stack = []
        self.ids = set()
        self.counts = Counter()
        self.sections = {}
        self.links = []
        self.schema_blocks = []
        self.canonical = []
        self.alternates = []
        self.description = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.counts[tag] += 1
        if "id" in attrs:
            require(attrs["id"] not in self.ids, f"Duplicate HTML id: {attrs['id']}")
            self.ids.add(attrs["id"])
        if tag == "main":
            require(self.stack and self.stack[-1][0] == "body", "The main element must be a direct child of body")
        if tag in {"main", "section", "article", "h1", "h2", "h3"}:
            require(not any("hidden" in parent or parent.get("aria-hidden") == "true" for _, parent in self.stack + [(tag, attrs)]), "CV content must not be hidden")
        if tag == "section":
            require("id" in attrs, "CV sections need stable ids")
            self.sections[attrs["id"]] = {"articles": 0, "headings": 0, "text": [], "dates": set()}
        section = next((parent.get("id") for parent_tag, parent in reversed(self.stack) if parent_tag == "section"), None)
        if section:
            if tag == "article":
                self.sections[section]["articles"] += 1
            if tag == "h2":
                self.sections[section]["headings"] += 1
        if tag == "time":
            value = attrs.get("datetime", "")
            require(len(value) in {4, 7, 10}, f"Unexpected datetime precision: {value}")
            date.fromisoformat(value + {4: "-01-01", 7: "-01", 10: ""}[len(value)])
            if section:
                self.sections[section]["dates"].add(value)
        if tag == "a":
            self.links.append(attrs.get("href", ""))
            if attrs.get("target") == "_blank":
                require({"noopener", "noreferrer"} <= set(attrs.get("rel", "").split()), "External links must retain safe rel attributes")
        if tag == "link":
            if attrs.get("rel") == "canonical":
                self.canonical.append(attrs.get("href"))
            if attrs.get("rel") == "alternate" and attrs.get("type") == "application/json":
                self.alternates.append(attrs.get("href"))
        if tag == "meta" and attrs.get("name") == "description":
            self.description = attrs.get("content")
        if tag == "script" and attrs.get("type") == "application/ld+json":
            self.schema_blocks.append("")
        if tag not in self.void_tags:
            self.stack.append((tag, attrs))

    def handle_endtag(self, tag):
        if tag in self.void_tags:
            return
        require(self.stack and self.stack[-1][0] == tag, f"Mismatched closing tag: {tag}")
        self.stack.pop()

    def handle_data(self, text):
        if self.stack and self.stack[-1][0] == "script":
            if self.stack[-1][1].get("type") == "application/ld+json":
                self.schema_blocks[-1] += text
            return
        for tag, attrs in self.stack:
            if tag == "section":
                self.sections[attrs["id"]]["text"].append(text)


def validate(root_dir: Path) -> None:
    public_files = ("index.html", "web/css/index.css", "web/js/index.js", "cv.pdf", "web/img/fish.png", "data/cv.json", "llms.txt")
    for resource in public_files:
        path = root_dir / resource
        require(path.is_file() and path.stat().st_size > 0, f"Missing or empty public resource: {resource}")
    cv = json.loads((root_dir / "data/cv.json").read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    parser = SiteParser()
    parser.feed((root_dir / "index.html").read_text(encoding="utf-8"))
    parser.close()
    require(not parser.stack, "HTML has unclosed tags")
    require(parser.counts["main"] == 1 and parser.counts["h1"] == 1, "Expected one main element and one H1")
    require(parser.description, "Missing meta description")
    url = cv["personal_information"]["website"].rstrip("/") + "/"
    require(parser.canonical == [url], "Canonical URL differs from the CV website")
    require(parser.alternates == ["data/cv.json"], "Missing structured CV discovery link")
    require(len(parser.schema_blocks) == 1, "Expected one JSON-LD profile block")
    schema = json.loads(parser.schema_blocks[0], object_pairs_hook=unique_object)
    require(schema.get("@context") == "https://schema.org" and schema.get("@type") == "ProfilePage", "Expected Schema.org ProfilePage")
    require(schema.get("url") == url and schema.get("@id") == url + "#profile", "Incorrect ProfilePage identifiers")
    person = schema["mainEntity"]
    require(person.get("@type") == "Person" and person.get("@id") == url + "#person", "Expected the identified Person as mainEntity")
    personal = cv["personal_information"]
    for schema_key, cv_key in {"name": "full_name", "givenName": "first_name", "familyName": "last_name", "alternateName": "native_name", "description": "headline"}.items():
        require(person.get(schema_key) == personal[cv_key], f"Person {schema_key} differs from CV")
    require(person.get("email") == "mailto:" + personal["email"], "Person email differs from CV")
    require(person.get("url") == url, "Person URL differs from CV")
    require(set(person.get("sameAs", [])) == {personal["github"], personal["linkedin"]}, "External profiles differ from CV")
    require(person.get("jobTitle") == cv["work_experience"][0]["job_title"], "Current job title differs from CV")
    address = person["address"]
    require(address.get("@type") == "PostalAddress" and address.get("addressLocality") == personal["location"]["city"] and address.get("addressCountry") == personal["location"]["country"], "Person address differs from CV")
    require(person.get("knowsAbout") == cv["technical_skills"][0]["skills"], "Structured expertise differs from CV")
    expected_alumni = {entry["institution"] for entry in cv["education"] if not entry["is_current"] and entry.get("completion_status") != "coursework_only"}
    require({entry["name"] for entry in person["alumniOf"]} == expected_alumni, "Alumni list differs from completed CV studies")
    current_employer = cv["work_experience"][0]["employer"]
    require(len(person["worksFor"]) == 2 and all(entry["name"] in current_employer for entry in person["worksFor"]), "Current affiliations differ from CV")
    for organization in person["alumniOf"] + person["worksFor"]:
        require(organization.get("@type") in {"Organization", "CollegeOrUniversity", "EducationalOrganization"}, "Invalid organization type")
    sections = {"experience": "work_experience", "education": "education", "projects": "projects", "publications": "publications", "conferences": "conferences", "datasets": "datasets", "volunteering": "volunteering"}
    for section_id, cv_key in sections.items():
        section = parser.sections[section_id]
        require(section["articles"] == len(cv[cv_key]), f"Incomplete CV section: {section_id}")
        text = " ".join("".join(section["text"]).split())
        for entry in cv[cv_key]:
            for field in ("employer", "institution", "name", "title", "description"):
                if field in entry:
                    require(entry[field].replace("-", "–") in text.replace("-", "–"), f"CV text differs in {section_id}: {field}")
            for achievement in entry.get("responsibilities_and_achievements", []):
                require(achievement in text, f"Missing achievement in {section_id}")
            for field in ("start_date", "end_date", "expected_graduation_date"):
                if entry.get(field):
                    require(entry[field] in section["dates"], f"Missing semantic date in {section_id}")
    for section_id in ("summary", "skills", "languages", "certifications", "interests", "contact"):
        require(section_id in parser.sections, f"Missing CV section: {section_id}")
    for section_id, section in parser.sections.items():
        require(section["headings"] == 1, f"Expected one H2 in section: {section_id}")
    for link in parser.links:
        parsed = urlsplit(link)
        if not parsed.scheme and not parsed.netloc:
            require(not parsed.path or (root_dir / parsed.path).is_file(), f"Broken local link: {link}")
            if parsed.fragment and not parsed.path:
                require(parsed.fragment in parser.ids, f"Broken section anchor: {link}")
    guide = (root_dir / "llms.txt").read_text(encoding="utf-8")
    require(guide.startswith("# " + personal["full_name"]), "LLM guide has an incorrect profile heading")
    require(url + "data/cv.json" in guide and url + "cv.pdf" in guide, "LLM guide must link to the JSON and PDF CV")
    print("[PASS] HTML structure, CV consistency, JSON-LD profile, dates, links, and LLM guide")


def main() -> int:
    argparse.ArgumentParser(description="Validate the static CV, JSON-LD profile, and public resources.").parse_args()
    try:
        validate(Path(__file__).resolve().parent.parent)
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(f"[FAIL] {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
