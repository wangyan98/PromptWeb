#!/usr/bin/env python3
"""Build data.js for the static project gallery."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import unquote, urlparse


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".avif"}
VIDEO_EXTS = {".mp4", ".webm", ".mov", ".m4v"}

PROJECTS = [
    ("\u4e07\u7269\u751f.json", "\u4e07\u7269\u751f", "project-1"),
    ("\u4e07\u7269\u751f2.json", "\u4e07\u7269\u751f2", "project-2"),
    # 元启录
    ("\u5143\u542f\u5f55.json", "\u5143\u542f\u5f55", "project-3"),
    ("\u5143\u542f\u5f552.json", "\u5143\u542f\u5f552", "project-4"),
    # 浮光
    ("\u6d6e\u51498.json", "\u6d6e\u51498", "project-5"),
    ("\u6d6e\u5149\u706b\u661f1.json", "\u6d6e\u5149\u706b\u661f1", "project-6"),
]


def media_kind(url: str) -> str | None:
    path = unquote(urlparse(url).path).lower()
    ext = Path(path).suffix
    if ext in IMAGE_EXTS:
        return "image"
    if ext in VIDEO_EXTS:
        return "video"
    return None


def make_node(node: dict, url_to_local: dict[str, str]) -> dict:
    node_data = node.get("data") or {}
    position = node.get("position") or {}
    images: list[str] = []
    videos: list[str] = []
    seen: set[str] = set()

    def walk(value: object) -> None:
        if isinstance(value, dict):
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
        elif isinstance(value, str):
            url = value.strip()
            if not url.startswith(("http://", "https://")):
                return
            if url in seen:
                return
            seen.add(url)
            local = url_to_local.get(url)
            if not local:
                return
            kind = media_kind(url)
            if kind == "image":
                images.append(local)
            elif kind == "video":
                videos.append(local)

    walk(node_data)

    return {
        "id": node.get("id"),
        "type": node.get("type"),
        "dataType": node_data.get("type"),
        "label": node_data.get("label") or node.get("id"),
        "status": node_data.get("status") or "",
        "model": node_data.get("modelName") or node_data.get("model") or "",
        "prompt": node_data.get("prompt") or "",
        "negativePrompt": node_data.get("negativePrompt") or "",
        "source": node_data.get("mediaSource") or "",
        "taskId": node_data.get("taskId") or "",
        "generationType": node_data.get("generationType") or "",
        "resolution": (
            node_data.get("resolution")
            or node_data.get("universalResolution")
            or ""
        ),
        "aspectRatio": (
            node_data.get("aspectRatio")
            or node_data.get("universalAspectRatio")
            or ""
        ),
        "duration": (
            node_data.get("duration")
            or node_data.get("universalDuration")
            or ""
        ),
        "createdAt": node_data.get("createdAt") or 0,
        "parentNode": node.get("parentNode"),
        "position": [position.get("x", 0), position.get("y", 0)],
        "images": images,
        "videos": videos,
    }


def build_project(json_name: str, dir_name: str, project_id: str) -> dict:
    doc = json.loads(Path(json_name).read_text(encoding="utf-8-sig"))
    mapping_path = Path(dir_name) / "media_mapping.json"
    mapping = json.loads(mapping_path.read_text(encoding="utf-8-sig"))
    url_to_local = {
        source: local.replace("\\", "/")
        for local, source in mapping.items()
    }

    data = doc["data"]
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])

    project_nodes: list[dict] = []
    project_groups: list[dict] = []
    image_count = 0
    video_count = 0
    prompt_count = 0

    for node in nodes:
        if node.get("type") == "group":
            node_data = node.get("data") or {}
            measured = node.get("measured") or {}
            position = node.get("position") or {}
            project_groups.append(
                {
                    "id": node.get("id"),
                    "label": node_data.get("label") or "\u7ec4",
                    "x": position.get("x", 0),
                    "y": position.get("y", 0),
                    "width": measured.get("width", 800),
                    "height": measured.get("height", 400),
                    "childNodeIds": node_data.get("childNodeIds") or [],
                }
            )
            continue

        item = make_node(node, url_to_local)
        image_count += len(item["images"])
        video_count += len(item["videos"])
        if item["prompt"]:
            prompt_count += 1
        project_nodes.append(item)

    project_edges = [
        {
            "source": edge.get("source"),
            "target": edge.get("target"),
            "sourceHandle": edge.get("sourceHandle") or "",
            "targetHandle": edge.get("targetHandle") or "",
        }
        for edge in edges
    ]

    overview_images = []
    for node in project_nodes:
        if node["images"]:
            overview_images.extend(node["images"][:1])
        if len(overview_images) >= 12:
            break

    return {
        "id": project_id,
        "title": data.get("title") or dir_name,
        "nodes": project_nodes,
        "groups": project_groups,
        "edges": project_edges,
        "stats": {
            "nodes": len(project_nodes),
            "groups": len(project_groups),
            "edges": len(project_edges),
            "images": image_count,
            "videos": video_count,
            "prompts": prompt_count,
        },
        "overviewImages": overview_images,
    }


def main() -> None:
    projects = [build_project(*project) for project in PROJECTS]
    content = "window.PROJECT_DATA = " + json.dumps(
        projects, ensure_ascii=False, separators=(",", ":")
    ) + ";\n"
    Path("data.js").write_text(content, encoding="utf-8")

    for project in projects:
        stats = project["stats"]
        print(
            f"{project['id']}: {stats['nodes']} nodes, {stats['edges']} edges, "
            f"{stats['images']} local images, {stats['videos']} local videos"
        )


if __name__ == "__main__":
    main()
