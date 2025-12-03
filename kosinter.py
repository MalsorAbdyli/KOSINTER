#!/usr/bin/env python3
import re
import requests
from dataclasses import dataclass
from typing import Dict, Optional, List

GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
RESET = "\033[0m"

SERVICES = {
    "instagram": "https://www.instagram.com/{username}/",
    "facebook": "https://www.facebook.com/{username}",
    "twitter": "https://twitter.com/{username}",
    "github": "https://github.com/{username}",
    "github_gist": "https://gist.github.com/{username}",
    "gitlab": "https://gitlab.com/{username}",
    "reddit": "https://www.reddit.com/user/{username}",
    "tiktok": "https://www.tiktok.com/@{username}",
    "youtube": "https://www.youtube.com/@{username}",
    "snapchat": "https://www.snapchat.com/add/{username}",
}


@dataclass
class UsernameCheckResult:
    service: str
    username: str
    url: str
    exists: bool
    http_status: Optional[int]
    error: Optional[str]


def check_profile(service: str, username: str, url: str, timeout: float = 8.0):
    uname = username.lower()

    # INSTAGRAM – JSON API (authoritative)
    if service == "instagram":
        api_url = (
            "https://i.instagram.com/api/v1/users/web_profile_info/"
            f"?username={username}"
        )
        ig_headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0 Safari/537.36"
            ),
            "X-IG-App-ID": "936619743392459",
        }
        try:
            resp = requests.get(api_url, headers=ig_headers, timeout=timeout)
            status = resp.status_code

            if status == 200:
                try:
                    data = resp.json()
                except ValueError:
                    return False, status, "invalid_json"
                user_obj = data.get("data", {}).get("user")
                return (True if user_obj else False), status, None

            if status == 404:
                return False, status, None

            return False, status, "uncertain"
        except requests.RequestException as e:
            return False, None, str(e)

    # TWITTER / X – HTML inspection (conservative)
    if service == "twitter":
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }

        # Error span / text that appears ONLY on non-existent profiles
        not_exist_texts = [
            "hmm...this page doesn’t exist. try searching for something else.",
            "hmm...this page doesn't exist. try searching for something else.",
        ]
        not_exist_span = (
            '<span class="css-1jxf684 r-bcqeeo r-1ttztb7 r-qvutc0 r-poiln3">'
            "Hmm...this page doesn’t exist. Try searching for something else."
            "</span>"
        )

        try:
            resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
            status = resp.status_code
            html = resp.text
            html_lower = html.lower()
            final_url = resp.url.lower()

            # 1) Explicit "page doesn't exist" markers → definitely NOT found
            if not_exist_span in html:
                return False, status, None
            for t in not_exist_texts:
                if t in html_lower:
                    return False, status, None

            # 2) HTTP 404 → not found
            if status == 404:
                return False, status, None

            # 3) Suspended accounts (URL or text) → username exists
            if "account suspended" in html_lower or "/account/suspended" in final_url:
                return True, status, None

            # 4) Positive markers: handle appears in title or bootstrap JSON
            handle = uname
            positive_markers = [
                f"(@{handle}) / x",              # <title>… (@cristiano) / X</title>
                f"(@{handle}) / twitter",
                f'"screen_name":"{handle}"',
                f'"screen_name": "{handle}"',
                f'@{handle} ·',                  # header line
            ]
            for m in positive_markers:
                if m in html_lower:
                    return True, status, None

            # 5) If none of the above triggered:
            #    be conservative → treat as NOT FOUND rather than saying it exists.
            return False, status, "uncertain"

        except requests.RequestException as e:
            return False, None, str(e)

    # OTHER SERVICES – HTML / status heuristics
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        )
    }

    try:
        resp = requests.get(url, headers=headers, allow_redirects=True, timeout=timeout)
        status = resp.status_code
        text_lower = resp.text.lower()

        if service == "facebook":
            if status == 200:
                return True, status, None
            if status == 404:
                return False, status, None
            return False, status, "uncertain"

        if service == "reddit":
            if (
                "sorry, nobody on reddit goes by that name" in text_lower
                or "page not found" in text_lower
            ):
                return False, status, None
            if status == 200:
                return True, status, None
            if status == 404:
                return False, status, None
            return False, status, "uncertain"

        if service == "tiktok":
            if (
                "couldn't find this account" in text_lower
                or "couldn’t find this account" in text_lower
                or "account not found" in text_lower
                or "this account could not be found" in text_lower
            ):
                return False, status, None
            if status == 200:
                return True, status, None
            if status == 404:
                return False, status, None
            return False, status, "uncertain"

        if status == 200:
            return True, status, None
        if status == 404:
            return False, status, None
        return False, status, "uncertain"

    except requests.RequestException as e:
        return False, None, str(e)


def check_username_single(username: str) -> Dict[str, UsernameCheckResult]:
    results: Dict[str, UsernameCheckResult] = {}

    for service, template in SERVICES.items():
        url = template.format(username=username)
        exists, status, error = check_profile(service, username, url)

        results[service] = UsernameCheckResult(
            service=service,
            username=username,
            url=url,
            exists=exists,
            http_status=status,
            error=error,
        )

    return results


def generate_variants(base_username: str) -> List[str]:
    if re.search(r"[._-]", base_username):
        parts = re.split(r"[._-]", base_username)
    else:
        if len(base_username) >= 4:
            mid = len(base_username) // 2
            parts = [base_username[:mid], base_username[mid:]]
        else:
            parts = [base_username]

    root = "".join(parts)
    dot = ".".join(parts)
    dash = "-".join(parts)
    underscore = "_".join(parts)

    candidates = [base_username, root, dot, dash, underscore]

    variants: List[str] = []
    seen = set()
    for c in candidates:
        if c and c not in seen:
            seen.add(c)
            variants.append(c)

    return variants


def print_results(base_username: str, all_results: Dict[str, Dict[str, UsernameCheckResult]]):
    print("\n======================================")
    print(f"     OSINT RESULTS FOR BASE: {base_username}")
    print("======================================\n")

    for variant, results in all_results.items():
        print(f"--- Username variant: {variant} ---")
        any_found = False

        for service, r in results.items():
            pretty_name = service.replace("_", " ").title()

            if r.exists:
                any_found = True
                print(f"{GREEN}[+] {pretty_name:15} FOUND  -> {r.url}{RESET}")
            else:
                print(f"{RED}[-] {pretty_name:15} not found{RESET}")

        if not any_found:
            print(f"{RED}No profiles found for this variant.{RESET}")

        print()

    print("Scan complete.\n")


def run_scan() -> bool:
    base_username = input("OSINT > Enter base username: ").strip()

    if not base_username:
        print("No username entered. Exiting.")
        return False

    print("\nProcessing scan, please wait...\n")

    variants = generate_variants(base_username)
    all_results = {}

    for v in variants:
        all_results[v] = check_username_single(v)

    print_results(base_username, all_results)

    while True:
        again = input("Do you want to scan another username? (y/n): ").strip().lower()
        if again in ("y", "yes"):
            return True
        if again in ("n", "no", ""):
            return False
        print("Please answer with 'y' or 'n'.")


def main():
    print(
        YELLOW
        + r"""
██╗  ██╗ ██████╗  ██████╗ ██╗███╗   ██╗████████╗███████╗██████╗ 
██║ ██╔╝██╔═══██╗██╔════╝ ██║████╗  ██║╚══██╔══╝██╔════╝██╔══██╗
█████╔╝ ██║   ██║██████╗  ██║██╔██╗ ██║   ██║   █████╗  ██████╔╝
██╔═██╗ ██║   ██║╚════██╗ ██║██║╚██╗██║   ██║   ██╔══╝  ██╔══██╗
██║  ██╗╚██████╔╝██████╔╝ ██║██║ ╚████║   ██║   ███████╗██║  ██║
╚═╝  ╚═╝ ╚═════╝ ╚═════╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚═╝  ╚═╝
"""
        + RESET
    )

    print(
        "         KOSINTER - OSINT Username Enumeration Tool.\n"
        "\n"
        "         Join us on Discord at our KOSINT COMMUNITY:\n"
        "               https://discord.gg/6mHpwwnP\n\n"
    )

    while True:
        if not run_scan():
            print("Goodbye.")
            break


if __name__ == "__main__":
    main()
