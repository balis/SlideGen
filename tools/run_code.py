#!/usr/bin/env python3
"""
Extract and execute code blocks marked with EXEC_TEST from a Marp draft.
Writes results to workspace/code_results_vN.json.

Usage: python tools/run_code.py workspace/draft_v1.md workspace/code_results_v1.json
"""

import sys
import json
import re
import subprocess
import tempfile
import os
from pathlib import Path

TIMEOUT = 15  # seconds

RUNNERS = {
    "python": lambda f: ["python3", f],
    "java": lambda f: None,  # special-cased below
    "javascript": lambda f: ["node", f],
    "js": lambda f: ["node", f],
    "bash": lambda f: ["bash", f],
    "shell": lambda f: ["bash", f],
}

EXTENSIONS = {
    "python": ".py",
    "java": ".java",
    "javascript": ".js",
    "js": ".js",
    "bash": ".sh",
    "shell": ".sh",
}

def extract_blocks(md_text):
    """Return list of (language, code, slide_context) for EXEC_TEST blocks."""
    blocks = []
    # Find code blocks preceded by EXEC_TEST marker (with up to 5 lines between)
    pattern = re.compile(
        r'<!--\s*EXEC_TEST\s*-->(?:\s*\n){0,5}\s*```(\w+)\n(.*?)```',
        re.DOTALL
    )
    for match in pattern.finditer(md_text):
        lang = match.group(1).lower()
        code = match.group(2)
        # Get surrounding slide title for context
        preceding = md_text[:match.start()].rfind('## ')
        title = md_text[preceding:match.start()].split('\n')[0].strip() if preceding >= 0 else "unknown"
        blocks.append({"lang": lang, "code": code, "slide": title})
    return blocks

def run_java(code, tmpdir):
    # Extract class name from code
    match = re.search(r'public\s+class\s+(\w+)', code)
    if not match:
        return 1, "", "No public class found in Java code"
    classname = match.group(1)
    src = os.path.join(tmpdir, f"{classname}.java")
    with open(src, 'w') as f:
        f.write(code)
    compile_result = subprocess.run(
        ["javac", src], capture_output=True, text=True, timeout=TIMEOUT
    )
    if compile_result.returncode != 0:
        return compile_result.returncode, "", compile_result.stderr
    run_result = subprocess.run(
        ["java", "-cp", tmpdir, classname],
        capture_output=True, text=True, timeout=TIMEOUT
    )
    return run_result.returncode, run_result.stdout, run_result.stderr

def run_block(block):
    lang = block["lang"]
    code = block["code"]
    result = {"lang": lang, "slide": block["slide"], "status": None,
              "stdout": "", "stderr": "", "returncode": None}
    if lang not in RUNNERS:
        result["status"] = "SKIPPED"
        result["stderr"] = f"No runner for language: {lang}"
        return result
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            if lang == "java":
                rc, out, err = run_java(code, tmpdir)
            else:
                ext = EXTENSIONS.get(lang, ".txt")
                src = os.path.join(tmpdir, f"snippet{ext}")
                with open(src, 'w') as f:
                    f.write(code)
                cmd = RUNNERS[lang](src)
                proc = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=TIMEOUT
                )
                rc, out, err = proc.returncode, proc.stdout, proc.stderr
            result["returncode"] = rc
            result["stdout"] = out[:2000]  # truncate
            result["stderr"] = err[:2000]
            result["status"] = "PASS" if rc == 0 else "FAIL"
    except subprocess.TimeoutExpired:
        result["status"] = "TIMEOUT"
        result["stderr"] = f"Exceeded {TIMEOUT}s timeout"
    except Exception as e:
        result["status"] = "ERROR"
        result["stderr"] = str(e)
    return result

def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <draft.md> <output.json>", file=sys.stderr)
        return 2
    draft_path = sys.argv[1]
    output_path = sys.argv[2]
    md_text = Path(draft_path).read_text()
    blocks = extract_blocks(md_text)
    if not blocks:
        print("No EXEC_TEST blocks found.")
        results = {"blocks_found": 0, "passed": 0, "failed": 0, "results": []}
    else:
        print(f"Found {len(blocks)} EXEC_TEST block(s). Running...")
        results_list = [run_block(b) for b in blocks]
        failures = [r for r in results_list if r["status"] in ("FAIL", "TIMEOUT", "ERROR")]
        results = {
            "blocks_found": len(blocks),
            "passed": len(blocks) - len(failures),
            "failed": len(failures),
            "results": results_list
        }
        for r in failures:
            print(f"  FAIL [{r['slide']}]: {r['stderr'][:200]}")
    Path(output_path).write_text(json.dumps(results, indent=2))
    print(f"Results written to {output_path}")
    return 1 if results.get("failed", 0) > 0 else 0

if __name__ == "__main__":
    sys.exit(main())
