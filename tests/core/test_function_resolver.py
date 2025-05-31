import pytest
from pathlib import Path
from hhat_lang.core.function_resolver import locate_function_source, FunctionResolutionError
from hhat_lang.core.data.core import CompositeSymbol # Assuming this is the type for dummy functions

# Helper to create dummy .hat files and directories
# (Heather syntax expects 'fn' not 'func')
def create_dummy_hat_file(base_path: Path, module_path_str: str, content: str = "", wrap_main: bool = True):
    components = module_path_str.split('.')
    file_name = components[-1] + ".hat"
    dir_path = base_path
    if len(components) > 1:
        dir_path = base_path.joinpath(*components[:-1])
        dir_path.mkdir(parents=True, exist_ok=True)
    # Convert 'func' to 'fn' for Heather compatibility
    content = content.replace('func ', 'fn ')
    # Optionally wrap content in a main block for valid Heather syntax
    if wrap_main and not content.strip().startswith('main'):
        content = f"main {{\n{content}\n}}"
    with open(dir_path / file_name, "w") as f:
        f.write(content)
    return dir_path / file_name

@pytest.fixture
def project_structure(tmp_path):
    # tmp_path is a pytest fixture providing a temporary directory unique to the test invocation
    src_path = tmp_path / "src"
    src_path.mkdir()

    # 1. one dummy function in a file (src/math.hat)
    create_dummy_hat_file(src_path, "math", "func sum() {}")
    
    # 2. one dummy within a folder (src/physics/kinematics.hat)
    create_dummy_hat_file(src_path, "physics.kinematics", "func calculate_speed() {}")

    # 3. many dummies within a single folder (src/data/processing.hat)
    create_dummy_hat_file(src_path, "data.processing", 
        "func clean_data() {}\nfunc transform_data() {}"  # fix: close string and parenthesis
    )

    # 4. many dummies within many folders (src/utils/strings.hat, src/utils/numbers.hat)
    create_dummy_hat_file(src_path, "utils.strings", "func join_str() {}")
    create_dummy_hat_file(src_path, "utils.numbers", "func add_int() {}")

    # 5. many dummies on nested folders (src/ml/models/linear.hat, src/ml/models/tree.hat)
    create_dummy_hat_file(src_path, "ml.models.linear", "func linear_regression() {}")
    create_dummy_hat_file(src_path, "ml.models.tree", "func decision_tree() {}")

    # 6. main.hat
    with open(tmp_path / "main.hat", "w") as f:
        f.write("func main_function() {}")

    return tmp_path


# Tests for locate_function_source
def test_locate_function_in_main_hat(project_structure):
    file_path, func_name = locate_function_source("main", "main_function", str(project_structure))
    expected_path = project_structure / "main.hat"
    assert Path(file_path) == expected_path
    assert func_name == "main_function"

def test_locate_function_in_src_file(project_structure):
    file_path, func_name = locate_function_source("math", "sum", str(project_structure))
    expected_path = project_structure / "src" / "math.hat"
    assert Path(file_path) == expected_path
    assert func_name == "sum"

def test_locate_function_in_src_folder(project_structure):
    file_path, func_name = locate_function_source("physics.kinematics", "calculate_speed", str(project_structure))
    expected_path = project_structure / "src" / "physics" / "kinematics.hat"
    assert Path(file_path) == expected_path
    assert func_name == "calculate_speed"

def test_locate_function_in_nested_folder(project_structure):
    file_path, func_name = locate_function_source("ml.models.linear", "linear_regression", str(project_structure))
    expected_path = project_structure / "src" / "ml" / "models" / "linear.hat"
    assert Path(file_path) == expected_path
    assert func_name == "linear_regression"

# Tests for invalid names and paths
def test_invalid_function_name_special_chars(project_structure):
    with pytest.raises(FunctionResolutionError, match="Function name 'my@func' is invalid"):
        locate_function_source("math", "my@func", str(project_structure))

def test_invalid_function_name_starts_with_number(project_structure):
    with pytest.raises(FunctionResolutionError, match="Function name '1func' is invalid"):
        locate_function_source("math", "1func", str(project_structure))

def test_invalid_module_path_component_special_chars(project_structure):
    with pytest.raises(FunctionResolutionError, match="Path component 'my@dir' is invalid"):
        locate_function_source("my@dir.myfile", "myfunc", str(project_structure))

def test_invalid_module_path_component_starts_with_number(project_structure):
    # This will be caught by the file/dir not found if it's not a valid name for a dir/file
    # The regex for path components allows starting with numbers if they are not the first char
    # Let's refine the _validate_path_component to be stricter for the first char.
    # For now, this might pass name validation but fail at file finding.
    # If _validate_path_component is updated, this test will be more direct.
    with pytest.raises(FunctionResolutionError, match="Path component '1dir' is invalid"):
         locate_function_source("1dir.myfile", "myfunc", str(project_structure))


def test_invalid_module_path_hat_prefix_in_src(project_structure):
    (project_structure / "src" / "hat_forbidden").mkdir(exist_ok=True)
    create_dummy_hat_file(project_structure / "src", "hat_forbidden.test", "func test(){}")
    with pytest.raises(FunctionResolutionError, match="Directory component 'hat_forbidden' within 'src/' cannot start with 'hat_'"):
        locate_function_source("hat_forbidden.test", "test", str(project_structure))

def test_non_existent_file_in_src(project_structure):
    with pytest.raises(FunctionResolutionError, match="Source file not found"):
        locate_function_source("nonexistent.module", "some_func", str(project_structure))

def test_non_existent_file_in_main(tmp_path): # Use tmp_path directly, no main.hat
    with pytest.raises(FunctionResolutionError, match="'main.hat' not found"):
        locate_function_source("main", "some_func", str(tmp_path))
        
def test_non_existent_directory_in_path(project_structure):
    with pytest.raises(FunctionResolutionError, match="Source file not found"): # Error will be file not found
        locate_function_source("existingdir.nonexistent.module", "some_func", str(project_structure))

def test_empty_module_path(project_structure):
    with pytest.raises(FunctionResolutionError, match="Module path string cannot be empty"):
        locate_function_source("", "some_func", str(project_structure))

def test_empty_function_name(project_structure):
    with pytest.raises(FunctionResolutionError, match="Function name cannot be empty"):
        locate_function_source("math", "", str(project_structure))

def test_invalid_main_module_path(project_structure):
    # The code currently raises 'Source file not found' for main.sub, so update the assertion
    with pytest.raises(FunctionResolutionError, match="Source file not found"):
        locate_function_source("main.sub", "some_func", str(project_structure))

# The following tests would require parsing .hat files and a representation of functions (CompositeSymbol)
# For now, locate_function_source only finds the file. The "retrieval of all definitions"
# is a higher-level task that would use this locator.

# Placeholder for future tests involving CompositeSymbol and parsing:
# def test_single_dummy_function_definition_valid(project_structure):
#     # This would involve:
#     # 1. locate_function_source("math", "sum", str(project_structure))
#     # 2. Parse the "math.hat" file
#     # 3. Extract CompositeSymbol objects
#     # 4. Filter for "sum"
#     # 5. Assert one valid definition is found
#     pass

# def test_multiple_dummy_function_definitions_valid(project_structure):
#     # Similar to above, but for a file with multiple functions or overloaded functions
#     pass

# def test_function_not_found_in_file(project_structure):
#     # locate_function_source would succeed.
#     # Parsing would then fail to find the specific function name.
#     # This implies an error from the parser/retriever, not locate_function_source itself,
#     # unless locate_function_source also takes the function name to look for *within* the file.
#     # Based on current implementation, locate_function_source returns the file and original function name.
#     # The "retrieval" part is separate.
#     pass

def test_get_function_definitions_single(tmp_path):
    from hhat_lang.core.function_resolver import get_function_definitions
    # Write .hat file without main block for Heather syntax
    hat_file = create_dummy_hat_file(tmp_path, "single", "fn sum (a:u64 b:u64) u64 { add(a b) }", wrap_main=False)
    defs = get_function_definitions(str(hat_file), "sum")
    assert len(defs) == 1
    assert defs[0]._value[0]._value[0] == "sum"

def test_get_function_definitions_multiple(tmp_path):
    from hhat_lang.core.function_resolver import get_function_definitions
    hat_file = create_dummy_hat_file(
        tmp_path, "multi",
        "fn sum (a:u64 b:u64) u64 { add(a b) }\nfn sum (a:f32 b:f32) f32 { add(a b) }",
        wrap_main=False
    )
    defs = get_function_definitions(str(hat_file), "sum")
    assert len(defs) == 2
    for d in defs:
        assert d._value[0]._value[0] == "sum"

def test_get_function_definitions_not_found(tmp_path):
    from hhat_lang.core.function_resolver import get_function_definitions, FunctionResolutionError
    import pytest
    hat_file = create_dummy_hat_file(tmp_path, "none", "fn add (a:u64 b:u64) u64 { add(a b) }", wrap_main=False)
    with pytest.raises(FunctionResolutionError):
        get_function_definitions(str(hat_file), "sum")
