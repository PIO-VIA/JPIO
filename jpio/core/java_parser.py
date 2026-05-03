import json
import subprocess
from pathlib import Path
from typing import Tuple
from .models import ParseResult

class JPIOParserError(Exception):
    """Exception raised when Java parsing fails."""
    pass

def check_java_available() -> Tuple[bool, str]:
    """
    Checks if java is installed and accessible in the PATH.
    Returns (True, version) if available, (False, "") otherwise.
    """
    try:
        result = subprocess.run(
            ["java", "-version"],
            capture_output=True,
            text=True,
            stderr=subprocess.STDOUT
        )
        if result.returncode == 0:
            # Output is usually on stderr for java -version
            # Example: openjdk version "21.0.2" 2024-01-16
            line = result.stdout.splitlines()[0]
            version = line.split('"')[1] if '"' in line else "unknown"
            return True, version
        return False, ""
    except (subprocess.SubprocessError, FileNotFoundError, IndexError):
        return False, ""

def get_jar_path() -> Path:
    """
    Returns the absolute path to jpio-parser.jar.
    The JAR is in jpio/bin/jpio-parser.jar relative to the project root.
    """
    # Assuming this file is in jpio/core/java_parser.py
    # jar_path = Path(__file__).parent.parent / "bin" / "jpio-parser.jar"
    
    # Better to find it relative to the package
    base_dir = Path(__file__).parent.parent
    jar_path = base_dir / "bin" / "jpio-parser.jar"
    
    if not jar_path.exists():
        raise FileNotFoundError(f"JPIO Parser JAR not found at {jar_path}")
    
    return jar_path

def parse_project(source_path: Path) -> ParseResult:
    """
    Calls the JAR and returns the deserialized ParseResult.
    """
    is_available, java_version = check_java_available()
    if not is_available:
        raise JPIOParserError(
            "Java is not installed or not in PATH. Please install Java 17+ from https://adoptium.net"
        )

    try:
        jar_path = get_jar_path()
    except FileNotFoundError as e:
        raise JPIOParserError(str(e))

    try:
        result = subprocess.run([
            "java", "-jar", str(jar_path),
            "--source", str(source_path)
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            raise JPIOParserError(f"Parser error (code {result.returncode}):\n{result.stderr}")

        try:
            data = json.loads(result.stdout)
            return ParseResult.from_dict(data)
        except json.JSONDecodeError:
            raise JPIOParserError(f"Invalid JSON returned by parser:\n{result.stdout}")

    except subprocess.TimeoutExpired:
        raise JPIOParserError("Parser timed out after 60 seconds.")
    except Exception as e:
        raise JPIOParserError(f"Unexpected error during parsing: {str(e)}")
