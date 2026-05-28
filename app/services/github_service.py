from __future__ import annotations

from typing import Union, Any

import httpx
import os
import base64
import json

from core.filters import (
    BLACK_DIRS,
    BLACK_EXTENSIONS,
    WHITE_EXTENSIONS
)


class GithubService:

    def __init__(self):

        self.base_url = "https://api.github.com"

        self.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
        }

        self.client = httpx.AsyncClient(
            headers=self.headers,
            timeout=30.0
        )

    def extract_username(self, github_url: str) -> str:
        return github_url.strip("/").split("/")[-1]

    async def get_repositories(self, github_url: str) -> list:

        username = self.extract_username(github_url)

        url = f"{self.base_url}/users/{username}/repos"

        params = {
            "sort": "pushed",
            "per_page": 5
        }

        try:
            response = await self.client.get(
                url,
                params=params
            )

            response.raise_for_status()

            repos = response.json()

            if not isinstance(repos, list):
                return []

            return [
                repo for repo in repos
                if not repo.get("fork", False)
            ]

        except httpx.HTTPError as e:
            print(f"[GitHub API ERROR] {e}")
            return []

    async def get_readme_content(
            self,
            username: str,
            repo_name: str
    ) -> Union[list[Any], str]:

        url = f"{self.base_url}/repos/{username}/{repo_name}/readme"

        try:
            response = await self.client.get(url)

            response.raise_for_status()

            data = response.json()

            content_b64 = data.get("content", "")

            if not content_b64:
                return []

            decoded_bytes = base64.b64decode(
                content_b64.replace("\n", "")
            )

            return decoded_bytes.decode(
                "utf-8",
                errors="ignore"
            )

        except httpx.HTTPError as e:
            print(f"[README HTTP ERROR] {repo_name}: {e}")
            return []

        except Exception as e:
            print(f"[README UNKNOWN ERROR] {repo_name}: {e}")
            return []

    async def scan_repository(
            self,
            username: str,
            repo_name: str,
            path: str = "",
            depth: int = 0,
            max_depth: int = 10
    ) -> list:

        # 재귀 깊이 제한
        if depth > max_depth:
            return []

        url = f"{self.base_url}/repos/{username}/{repo_name}/contents/{path}"

        try:
            response = await self.client.get(url)

            response.raise_for_status()

            contents = response.json()

            if not isinstance(contents, list):
                return []

            results = []

            for item in contents:

                item_type = item.get("type")
                item_name = item.get("name", "")

                # 디렉토리 처리
                if item_type == "dir":

                    if item_name in BLACK_DIRS:
                        continue

                    sub_files = await self.scan_repository(
                        username=username,
                        repo_name=repo_name,
                        path=item.get("path", ""),
                        depth=depth + 1,
                        max_depth=max_depth
                    )

                    results.extend(sub_files)

                # 파일 처리
                elif item_type == "file":

                    ext = ""

                    if "." in item_name:
                        ext = "." + item_name.split(".")[-1].lower()

                    # 블랙리스트 제외
                    if ext in BLACK_EXTENSIONS:
                        continue

                    # 화이트리스트 제외
                    if ext and ext not in WHITE_EXTENSIONS:
                        continue

                    results.append({
                        "name": item_name,
                        "path": item.get("path"),
                        "extension": ext,
                        "download_url": item.get("download_url")
                    })

            return results

        except httpx.HTTPError as e:
            print(f"[SCAN HTTP ERROR] {repo_name}/{path}: {e}")
            return []

        except Exception as e:
            print(f"[SCAN UNKNOWN ERROR] {repo_name}/{path}: {e}")
            return []

    async def get_package_json(
            self,
            username: str,
            repo_name: str
    ) -> Union[dict, None]:

        url = f"{self.base_url}/repos/{username}/{repo_name}/contents/package.json"

        try:
            response = await self.client.get(url)

            if response.status_code != 200:
                return None

            data = response.json()

            content_b64 = data.get("content", "")

            if not content_b64:
                return None

            decoded_bytes = base64.b64decode(
                content_b64.replace("\n", "")
            )

            return json.loads(
                decoded_bytes.decode(
                    "utf-8",
                    errors="ignore"
                )
            )

        except (
                json.JSONDecodeError,
                ValueError,
                httpx.HTTPError
        ) as e:

            print(f"[PACKAGE JSON ERROR] {repo_name}: {e}")
            return None

    def detect_stack(self, package_json: dict) -> list:

        if not package_json:
            return []

        dependencies = {
            **package_json.get("dependencies", {}),
            **package_json.get("devDependencies", {})
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
            "flask": "Flask"
        }

        detected = set()

        for dep in dependencies.keys():

            dep_lower = dep.lower()

            for key, value in tech_map.items():

                if key in dep_lower:
                    detected.add(value)

        return list(detected)

    async def close(self):
        await self.client.aclose()

    async def analyze_user(self, github_url: str):

        try:
            username = self.extract_username(
                github_url
            )

            repos = await self.get_repositories(
                github_url
            )

            results = []

            for repo in repos:

                repo_name = repo["name"]

                readme = await self.get_readme_content(
                    username,
                    repo_name
                )

                package_json = await self.get_package_json(
                    username,
                    repo_name
                )

                stacks = self.detect_stack(
                    package_json
                )

                files = await self.scan_repository(
                    username,
                    repo_name
                )

                results.append({
                    "repo_name": repo_name,
                    "readme": readme,
                    "stacks": stacks,
                    "files": files
                })
            print(results)
            return results

        finally:
            await self.close()
