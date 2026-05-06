import pytest

from mentask.core.compression import ContextCompressor


def test_smart_compress_basic():
    content = "Hello world\n# comment\nprint('hi')"
    compressed = ContextCompressor.smart_compress(content)
    assert "Hello world" in compressed
    assert "# comment" not in compressed
    assert "print('hi')" in compressed


def test_smart_compress_code_blocks():
    content = """
    Some text
    ```python
    # This is a comment
    x = 10  # inline comment
    print(x)
    ```
    """
    compressed = ContextCompressor.smart_compress(content)
    assert "# This is a comment" not in compressed
    assert "# inline comment" not in compressed
    assert "x = 10" in compressed
    assert "print(x)" in compressed


def test_smart_compress_multiple_blocks():
    content = """
    ```python
    # first
    a = 1
    ```
    middle
    ```javascript
    // second
    let b = 2;
    ```
    """
    compressed = ContextCompressor.smart_compress(content)
    assert "# first" not in compressed
    assert "// second" not in compressed
    assert "a = 1" in compressed
    assert "let b = 2;" in compressed


def test_smart_compress_mixed_content():
    content = """
    Here is some code:
    ```python
    # comment
    x = 10
    ```
    And some text outside.
    """
    compressed = ContextCompressor.smart_compress(content)
    assert "# comment" not in compressed
    assert "x = 10" in compressed
    assert "Here is some code" in compressed


def test_compress_code_aliases():
    python_code = "# full line comment\nprint('py')"
    assert ContextCompressor.compress_code(python_code, "py") == "print('py')"

    js_code = "console.log('js'); // comment"
    assert ContextCompressor.compress_code(js_code, "js") == "console.log('js');"

    ts_code = "let x: number = 1; /* comment */"
    assert ContextCompressor.compress_code(ts_code, "ts") == "let x: number = 1;"


def test_compress_code_c_style():
    c_code = "int main() { return 0; } // c comment"
    assert ContextCompressor.compress_code(c_code, "c") == "int main() { return 0; }"

    cpp_code = "std::cout << 'cpp'; /* cpp comment */"
    assert ContextCompressor.compress_code(cpp_code, "cpp") == "std::cout << 'cpp';"

    java_code = "System.out.println('java'); // java comment"
    assert ContextCompressor.compress_code(java_code, "java") == "System.out.println('java');"

    ts_code_full = "const a: string = 'ts'; // ts comment"
    assert ContextCompressor.compress_code(ts_code_full, "typescript") == "const a: string = 'ts';"


def test_compress_code_unknown_language():
    code = "Some code // comment \n\n # another comment"
    compressed = ContextCompressor.compress_code(code, "unknown")
    # For unknown languages, it should just compress whitespace
    assert compressed == "Some code // comment \n # another comment"

    compressed_empty_lang = ContextCompressor.compress_code(code)
    assert compressed_empty_lang == "Some code // comment \n # another comment"


def test_smart_compress_code_replacer_edge_cases():
    # Empty code block without language
    content = "```\n```"
    assert ContextCompressor.smart_compress(content) == "```\n\n```"

    # Empty code block with language
    content = "```python\n```"
    assert ContextCompressor.smart_compress(content) == "```python\n\n```"

    # Unclosed code block
    content = "```javascript\n// comment\nlet x = 1;"
    assert ContextCompressor.smart_compress(content) == "```javascript\nlet x = 1;\n```"

    # Only language, no body, no newline
    content = "```python"
    assert ContextCompressor.smart_compress(content) == "```python\n\n```"

    # No language, no body, no newline
    content = "```"
    assert ContextCompressor.smart_compress(content) == "```\n\n```"
