from __future__ import annotations

import re
from pathlib import Path
from typing import List, Tuple

from hhat_lang.core.data.core import CompositeSymbol
from hhat_lang.dialects.heather.code.ast import FnDef, Program
from hhat_lang.dialects.heather.parsing.run import parse_file


class FunctionResolutionError(Exception):
    """Custom error for function resolution issues."""

    pass


def _validate_path_component(component: str, is_directory_in_src: bool):
    """
    Validates a single component of a module path (directory or file stem).
    """
    if not component:
        raise FunctionResolutionError("Path component cannot be empty.")

    # Must start with a letter or underscore, followed by alphanumeric, underscore, or hyphen.
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_-]*$", component):
        raise FunctionResolutionError(
            f"Path component '{component}' is invalid. "
            "Must start with a letter or underscore, and only contain "
            "alphanumeric characters, underscores (_), or hyphens (-)."
        )

    if is_directory_in_src and component.startswith("hat_"):
        raise FunctionResolutionError(
            f"Directory component '{component}' within 'src/' cannot start with 'hat_'."
        )


def locate_function_source(
    module_path_str: str, function_name: str, project_root_str: str
) -> Tuple[str, str]:
    """
    Locates the source file for a given function based on its module path and name.

    The function name itself is also validated against basic H-hat naming conventions.
    Dialects may impose stricter rules.

    Args:
        module_path_str: The module path string, e.g., "math", "maths.linalg", "main".
        function_name: The name of the function, e.g., "sum", "dot", "rv-continuous".
        project_root_str: The absolute path to the project root directory.

    Returns:
        A tuple containing the absolute string path to the .hat file and the function name.

    Raises:
        FunctionResolutionError: If the path is invalid, file not found,
                                 or other resolution issues.
    """
    if not module_path_str:
        raise FunctionResolutionError("Module path string cannot be empty.")
    if not function_name:
        raise FunctionResolutionError("Function name cannot be empty.")

    # Validate function_name (basic H-hat core validation)
    # Must start with a letter or underscore, followed by alphanumeric, underscore, or hyphen.
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_-]*$", function_name):
        raise FunctionResolutionError(
            f"Function name '{function_name}' is invalid. "
            "Must start with a letter or underscore, and only contain "
            "alphanumeric characters, underscores (_), or hyphens (-)."
        )

    project_root = Path(project_root_str)
    module_components = module_path_str.split(".")

    # Case 1: Function in main.hat (module_path_str == "main")
    if module_path_str == "main":
        if len(module_components) > 1 or module_components[0] != "main":
            raise FunctionResolutionError(
                f"Invalid module path for 'main': {module_path_str}"
            )
        # "main" as a file stem does not need validation against "hat_" prefix or other rules here.
        target_file = project_root / "main.hat"
        if not target_file.is_file():
            raise FunctionResolutionError(f"'main.hat' not found at {target_file}")
        return str(target_file), function_name

    # Case 2: Function in a .hat file within src/
    # module_components = ["directory", "subdirectory", "file_stem"]
    if not module_components:  # Should be caught by earlier check, but as safeguard.
        raise FunctionResolutionError("Module components list is empty.")

    file_stem = module_components[-1]
    directory_components = module_components[:-1]

    # Validate file_stem (as a file name part, not a directory in src)
    _validate_path_component(file_stem, is_directory_in_src=False)

    # Validate directory_components
    current_path_check = project_root / "src"
    for dir_comp in directory_components:
        _validate_path_component(dir_comp, is_directory_in_src=True)
        current_path_check /= dir_comp
        if (
            not current_path_check.is_dir() and not current_path_check.exists()
        ):  # Check if path exists if it's not the full path yet
            # This check is tricky because we build the path. The final file check is key.
            # We primarily validate names here. Existence is checked for the final file.
            pass

    relative_file_path = Path(*directory_components) / (file_stem + ".hat")
    target_file = project_root / "src" / relative_file_path

    if not target_file.is_file():
        raise FunctionResolutionError(f"Source file not found: {target_file}")

    return str(target_file), function_name


def get_function_definitions(file_path: str, function_name: str) -> List[FnDef]:
    """
    Parse the .hat file and return all function definitions (FnDef) matching the function_name.
    Raises FunctionResolutionError if none found.
    """
    ast = parse_file(file_path)
    # The root AST should be a Program node
    if not isinstance(ast, Program):
        raise FunctionResolutionError(
            f"File {file_path} does not parse to a valid Program AST."
        )

    # Find all FnDef nodes in the AST
    found_defs = []

    def visit(node):
        if isinstance(node, FnDef):
            print("DEBUG FnDef node:", node, node._value)
            fn_id = node._value[0]
            print("DEBUG fn_id:", fn_id, getattr(fn_id, "_value", None))
            if hasattr(fn_id, "_value") and fn_id._value[0] == function_name:
                found_defs.append(node)
        # Recursively visit children
        if hasattr(node, "value"):
            for v in node.value:
                if isinstance(v, (list, tuple)):
                    for item in v:
                        if hasattr(item, "__class__"):
                            visit(item)
                elif hasattr(v, "__class__"):
                    visit(v)

    visit(ast)
    if not found_defs:
        raise FunctionResolutionError(
            f"No function definition named '{function_name}' found in {file_path}"
        )
    return found_defs
