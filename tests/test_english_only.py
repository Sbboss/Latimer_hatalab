import re
import subprocess
import unittest
from pathlib import Path


HAN_IDEOGRAPH = re.compile(
    r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\U00020000-\U0003347f]"
)


class RepositoryLanguageTests(unittest.TestCase):
    def test_tracked_paths_and_utf8_text_contain_no_han_ideographs(self):
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
            if HAN_IDEOGRAPH.search(path.as_posix()):
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
                if HAN_IDEOGRAPH.search(line):
                    violations.append(f"{path}:{line_number}")
                    if len(violations) >= 20:
                        break
            if len(violations) >= 20:
                break

        self.assertFalse(
            violations,
            "Han ideographs are not allowed in tracked repository content:\n"
            + "\n".join(violations),
        )


if __name__ == "__main__":
    unittest.main()
