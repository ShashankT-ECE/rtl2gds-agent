import re


def strip_code_fences(text: str) -> str:
    """
    Strip markdown code fences (```python, ```verilog, ``` or bare ```) from LLM output.
    Also handles explanatory text before/after fences (e.g. "The bug is... ```verilog\n...\n```").
    Falls back to original text if stripping produces empty result.
    """
    original = text.strip()

    # Strategy 1: Find a fenced code block anywhere in the text
    block_pattern = re.compile(r'^```\w*\s*\n(.*?)\n```\s*$', re.DOTALL)
    m = block_pattern.search(original)
    if m:
        result = m.group(1).strip()
        if result:
            return result

    # Strategy 2: Text starts with fences (original simpler approach)
    if original.startswith("```"):
        result = re.sub(r'^```\w*\s*\n', '', original)
        result = re.sub(r'\n```\s*$', '', result)
        result = result.strip()
        if result:
            return result

    # Strategy 3: Look for verilog module keyword and extract module..endmodule
    # (handles cases where LLM adds commentary before and/or after the code)
    module_match = re.search(r'^\s*module\s+\w+', original, re.MULTILINE)
    endmodule_match = re.search(r'\bendmodule\b', original[module_match.start():]) if module_match else None
    if module_match:
        if endmodule_match:
            result = original[module_match.start():module_match.start() + endmodule_match.end()]
        else:
            result = original[module_match.start():].strip()
        result = result.strip()
        return result if result else original

    # Fallback: return original if nothing worked
    return original
