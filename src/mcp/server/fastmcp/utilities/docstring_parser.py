import re

from typing import Any, Dict # Added type hints

def parse_docstring(docstring: str | None) -> Dict[str, Any]:
    """
    Parses a standard Python docstring into summary, args, returns, and raises.

    Args:
        docstring: The docstring to parse.

    Returns:
        A dictionary with keys 'summary', 'args', 'returns', 'raises'.
        'args' is a dict mapping arg names to descriptions.
        'raises' is a dict mapping exception type names to descriptions.
    """
    if not docstring:
        return {"summary": "", "args": {}, "returns": "", "raises": {}}

    lines = docstring.strip().splitlines()
    if not lines:
        return {"summary": "", "args": {}, "returns": "", "raises": {}}

    summary = lines[0].strip()
    args = {}
    returns = ""
    raises = {} # Added raises dictionary
    current_section = None
    current_key = None # Used for both args and raises keys
    current_desc_lines = []

    # Regex to find args/raises lines: "key (type): description" or "key: description"
    # Allows for optional type hints for args, captures key and description
    key_pattern = re.compile(r"^\s*([\w\.]+)\s*(?:\(.*\))?:\s*(.*)") # \w includes _, . allows for exception paths

    for line in lines[1:]:
        stripped_line = line.strip()

        if not stripped_line: # Skip empty lines between sections
            continue

        # --- Section Detection ---
        section_line = stripped_line.lower()
        is_new_section_header = False
        new_section_type = None

        if section_line in ("args:", "arguments:", "parameters:"):
            new_section_type = "args"
            is_new_section_header = True
        elif section_line in ("returns:", "yields:"):
            new_section_type = "returns"
            is_new_section_header = True
        # Added Raises section detection
        elif section_line.startswith(("raises ", "raises:", "errors:", "exceptions:")):
            new_section_type = "raises"
            is_new_section_header = True
        elif section_line.startswith(("attributes:", "see also:", "example:", "examples:", "notes:")):
            # Other common sections where we might stop processing previous ones
            new_section_type = "other"
            is_new_section_header = True

        # --- Finalize Previous Item ---
        # Finalize if starting a new section OR if indentation breaks for current item
        finalize_previous = False
        if is_new_section_header:
            finalize_previous = True
        elif current_section in ["args", "raises"] and current_key and not line.startswith(' '):
            finalize_previous = True
        elif current_section == "returns" and current_desc_lines and not line.startswith(' '):
             finalize_previous = True


        if finalize_previous:
            if current_section == "args" and current_key:
                args[current_key] = " ".join(current_desc_lines).strip()
            elif current_section == "raises" and current_key: # Finalize raises item
                raises[current_key] = " ".join(current_desc_lines).strip()
            elif current_section == "returns":
                returns = " ".join(current_desc_lines).strip()

            # Reset state for the potential new item/section
            current_key = None
            current_desc_lines = []
            current_section = new_section_type # Set the new section type

            # If it was just a header line, continue to next line
            if is_new_section_header:
                # If we hit a known 'other' section, we can stop processing altogether
                # if current_section == "other":
                #    break
                continue

        # --- Process Line Content ---
        if current_section == "args" or current_section == "raises":
            match = key_pattern.match(line) # Match against original line for indentation check
            if match:
                # Finalize previous key within the *same* section if starting a new key
                if current_key:
                     desc = " ".join(current_desc_lines).strip()
                     if current_section == "args":
                         args[current_key] = desc
                     elif current_section == "raises":
                         raises[current_key] = desc

                # Start the new key
                current_key = match.group(1)
                current_desc_lines = [match.group(2).strip()]
            elif current_key and line.startswith(' '): # Check for indentation for continuation
                current_desc_lines.append(stripped_line)
            # else: Line doesn't match key format and isn't indented -> potentially end of section or ignored line

        elif current_section == "returns":
             # If it's the start of returns desc or indented continuation line
             if not current_desc_lines or line.startswith(' '):
                 current_desc_lines.append(stripped_line)
             # else: line doesn't look like continuation -> end of section handled above

    # --- Final capture after loop ---
    if current_key: # Capture the last item being processed
        desc = " ".join(current_desc_lines).strip()
        if current_section == "args":
            args[current_key] = desc
        elif current_section == "raises":
            raises[current_key] = desc
    # Capture returns description if it was the last section being processed and wasn't finalized
    elif current_section == "returns" and not returns:
        returns = " ".join(current_desc_lines).strip()

    return {"summary": summary, "args": args, "returns": returns, "raises": raises}

# docstring="""
#         Executes Python code within a secure E2B cloud sandbox.

#         Args:
#             code: The string containing the Python code to execute.

#         Returns:
#             A string containing the formatted standard output (stdout) and standard error (stderr)from the execution. If an error occurs during setup or execution, an error message string is returned.

#         Raises:
#             NotAuthorizedError: If the API key is not set.
#             ValueError: If the API key set.
# """

# result = parse_docstring(docstring)
# print(result)