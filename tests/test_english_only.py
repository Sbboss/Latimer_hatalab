import re
import subprocess
import unittest
from pathlib import Path


CJK_CHARACTER = re.compile(
    r"[\u2e80-\u303f\u3100-\u312f\u31a0-\u31ef\u3200-\u33ff"
    r"\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uff00-\uffef"
    r"\U00020000-\U0003347f]"
)


class RepositoryLanguageTests(unittest.TestCase):
    def test_tracked_paths_and_utf8_text_contain_no_cjk_characters(self):
        result = subprocess.run(
            ["git", "ls-files", "-z"],
            check=True,
            capture_output=True,
        )
        tracked_paths = [
            Path(raw_path.decode("utf-8"))
            for raw_path in result.stdout.split(b"\0")
            if raw_path
        ]

        violations: list[str] = []
        for path in tracked_paths:
            if CJK_CHARACTER.search(path.as_posix()):
                violations.append(f"tracked path: {path}")
            if not path.is_file():
                continue

            raw = path.read_bytes()
            if b"\0" in raw:
                continue
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                continue

            for line_number, line in enumerate(text.splitlines(), start=1):
                if CJK_CHARACTER.search(line):
                    violations.append(f"{path}:{line_number}")
                    if len(violations) >= 20:
                        break
            if len(violations) >= 20:
                break

        self.assertFalse(
            violations,
            "CJK characters are not allowed in tracked repository content:\n"
            + "\n".join(violations),
        )


if __name__ == "__main__":
    unittest.main()
