from __future__ import annotations

import base64
import json
import re
from typing import Optional

import httpx

from app.core.config import settings
from app.core.filters import BLACK_DIRS, BLACK_EXTENSIONS, WHITE_EXTENSIONS


class GithubServiceError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


class GithubService:
    def __init__(self):
        self.base_url = "https://api.github.com"

        headers = {
            "Accept": "application/vnd.github+json",
        }
        if settings.GITHUB_TOKEN:
            headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"

        self.client = httpx.AsyncClient(
            headers=headers,
            timeout=30.0,
        )

    def extract_repo_info(self, repo_url: str) -> tuple[str, str]:
        cleaned_url = repo_url.strip()
        match = re.search(
            r"github\.com/(?P<owner>[^/\s]+)/(?P<repo>[^/\s]+?)(?:\.git)?/?$",
            cleaned_url,
        )

        if not match:
            raise GithubServiceError(
                "GitHub repository URL 형식이 올바르지 않습니다. 예: https://github.com/owner/repo",
                status_code=400,
            )

        owner = match.group("owner")
        repo_name = match.group("repo")

        if not owner or not repo_name:
            raise GithubServiceError("GitHub 저장소 정보를 찾을 수 없습니다.", status_code=400)

        return owner, repo_name

    async def get_repository_metadata(self, owner: str, repo_name: str) -> dict:
        url = f"{self.base_url}/repos/{owner}/{repo_name}"

        try:
            response = await self.client.get(url)
            if response.status_code == 401:
                raise GithubServiceError("GitHub 토큰 인증에 실패했습니다.", status_code=401)
            if response.status_code == 403:
                raise GithubServiceError(
                    "GitHub API 접근이 거부되었습니다. 토큰 또는 요청 제한을 확인하세요.",
                    status_code=403,
                )
            if response.status_code == 404:
                raise GithubServiceError(
                    f"GitHub 저장소 '{owner}/{repo_name}' 를 찾을 수 없습니다.",
                    status_code=404,
                )

            response.raise_for_status()
            data = response.json()

            return {
                "repo_name": data.get("name", repo_name),
                "repo_url": data.get("html_url"),
                "description": data.get("description") or "",
                "default_branch": data.get("default_branch") or "",
                "language": data.get("language"),
            }

        except httpx.HTTPError as exc:
            raise GithubServiceError(f"GitHub 저장소 정보 조회에 실패했습니다: {exc}", status_code=502) from exc

    async def get_readme_content(self, owner: str, repo_name: str) -> str:
        url = f"{self.base_url}/repos/{owner}/{repo_name}/readme"

        try:
            response = await self.client.get(url)

            if response.status_code == 404:
                return ""
            if response.status_code == 401:
                raise GithubServiceError("GitHub 토큰 인증에 실패했습니다.", status_code=401)
            if response.status_code == 403:
                raise GithubServiceError(
                    "GitHub API 접근이 거부되었습니다. 토큰 또는 요청 제한을 확인하세요.",
                    status_code=403,
                )

            response.raise_for_status()
            data = response.json()
            content_b64 = data.get("content", "")
            if not content_b64:
                return ""

            decoded_bytes = base64.b64decode(content_b64.replace("\n", ""))
            return decoded_bytes.decode("utf-8", errors="ignore")

        except httpx.HTTPError as exc:
            raise GithubServiceError(f"README 조회에 실패했습니다 ({repo_name}): {exc}", status_code=502) from exc

    async def scan_repository(
        self,
        owner: str,
        repo_name: str,
        path: str = "",
        depth: int = 0,
        max_depth: int = 10,
    ) -> list[dict]:
        if depth > max_depth:
            return []

        url = f"{self.base_url}/repos/{owner}/{repo_name}/contents/{path}"
        try:
            response = await self.client.get(url)
            if response.status_code == 404:
                return []
            if response.status_code == 401:
                raise GithubServiceError("GitHub 토큰 인증에 실패했습니다.", status_code=401)
            if response.status_code == 403:
                raise GithubServiceError(
                    "GitHub API 접근이 거부되었습니다. 토큰 또는 요청 제한을 확인하세요.",
                    status_code=403,
                )

            response.raise_for_status()
            contents = response.json()
            if not isinstance(contents, list):
                return []

            results = []

            for item in contents:
                item_type = item.get("type")
                item_name = item.get("name", "")

                if item_type == "dir":
                    if item_name in BLACK_DIRS:
                        continue

                    sub_files = await self.scan_repository(
                        owner=owner,
                        repo_name=repo_name,
                        path=item.get("path", ""),
                        depth=depth + 1,
                        max_depth=max_depth,
                    )
                    results.extend(sub_files)

                elif item_type == "file":
                    ext = ""
                    if "." in item_name:
                        ext = "." + item_name.split(".")[-1].lower()

                    if ext in BLACK_EXTENSIONS:
                        continue
                    if ext and ext not in WHITE_EXTENSIONS:
                        continue

                    results.append(
                        {
                            "name": item_name,
                            "path": item.get("path"),
                            "extension": ext,
                            "download_url": item.get("download_url"),
                            "size": item.get("size"),
                        }
                    )

            return results

        except httpx.HTTPError as exc:
            raise GithubServiceError(
                f"저장소 스캔에 실패했습니다 ({repo_name}/{path}): {exc}",
                status_code=502,
            ) from exc

    async def get_package_json(self, owner: str, repo_name: str) -> Optional[dict]:
        url = f"{self.base_url}/repos/{owner}/{repo_name}/contents/package.json"

        try:
            response = await self.client.get(url)

            if response.status_code == 404:
                return None
            if response.status_code in (401, 403):
                response.raise_for_status()

            response.raise_for_status()
            data = response.json()
            content_b64 = data.get("content", "")
            if not content_b64:
                return None

            decoded_bytes = base64.b64decode(content_b64.replace("\n", ""))
            return json.loads(decoded_bytes.decode("utf-8", errors="ignore"))

        except (json.JSONDecodeError, ValueError, httpx.HTTPError):
            return None

    def detect_stack(self, package_json: Optional[dict]) -> list[str]:
        if not package_json:
            return []

        dependencies = {
            **package_json.get("dependencies", {}),
            **package_json.get("devDependencies", {}),
        }

        tech_map = {
            "react": "React",
            "next": "Next.js",
            "vue": "Vue",
            "express": "Express",
            "nestjs": "NestJS",
            "@nestjs/core": "NestJS",
            "mongoose": "MongoDB",
            "typeorm": "TypeORM",
            "tailwindcss": "TailwindCSS",
            "redux": "Redux",
            "axios": "Axios",
            "socket.io": "Socket.IO",
            "fastapi": "FastAPI",
            "django": "Django",
            "flask": "Flask",
        }

        detected = set()
        for dep in dependencies.keys():
            dep_lower = dep.lower()
            for key, value in tech_map.items():
                if key in dep_lower:
                    detected.add(value)

        return sorted(detected)

    async def analyze_repository(self, repo_url: str) -> dict:
        try:
            owner, repo_name = self.extract_repo_info(repo_url)

            metadata = await self.get_repository_metadata(owner, repo_name)
            readme = await self.get_readme_content(owner, repo_name)
            package_json = await self.get_package_json(owner, repo_name)
            stacks = self.detect_stack(package_json)
            files = await self.scan_repository(owner, repo_name)

            return {
                **metadata,
                "readme": readme,
                "stacks": stacks,
                "files": files,
            }

        finally:
            await self.close()

    async def close(self):
        await self.client.aclose()
