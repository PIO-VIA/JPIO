"""

Takes the dict { filepath: java_code } produced by generator.py
and writes the files to disk.

Special convention:
    Keys prefixed with "__append__:" do not create a new file
    but append the content to the end of an existing file
    (e.g., application.properties).
"""

from pathlib import Path

from jpio.utils.file_helper import write_file, append_to_file
from jpio.utils.console import print_file_created, print_warning

APPEND_PREFIX = "__append__:"


def write_all(
    generated: dict[str, str],
    base_path: Path = Path("."),
) -> int:
    """
    Writes all generated files to disk.

    Parameters:
        generated: dict { relative_path: content }
        base_path: root of the Spring Boot project (defaults to current folder)

    Returns:
        The number of files actually written.
    """
    written_count = 0

    for rel_path, content in generated.items():

        # ── Append mode (application.properties) ────────────────────────────
        if rel_path.startswith(APPEND_PREFIX):
            actual_path = base_path / rel_path[len(APPEND_PREFIX):]

            if actual_path.exists():
                append_to_file(actual_path, "\n" + content)
                print_file_created(str(actual_path.relative_to(base_path)))
                written_count += 1
            else:
                print_warning(
                    f"File not found for append: {actual_path} — skipping."
                )
            continue

        # ── Normal creation mode ────────────────────────────────────────────
        filepath = base_path / rel_path
        was_written = write_file(filepath, content, overwrite=False)

        if was_written:
            print_file_created(rel_path)
            written_count += 1
        else:
            print_warning(f"File already exists — skipping: {rel_path}")

    return written_count