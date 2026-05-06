from mentask.core.compression import ContextCompressor


def test_compress_text():
    text = "Hello    world\n\n\nNew line"
    compressed = ContextCompressor.compress_text(text)
    assert compressed == "Hello world\n\nNew line"


def test_compress_python_code():
    code = """
def hello():
    # This is a comment
    print("hello") # inline comment

    return True
"""
    compressed = ContextCompressor.compress_code(code, "python")
    # Python code compression strips full line comments and collapses lines
    assert "# This is a comment" not in compressed
    assert "return True" in compressed
    assert "def hello():" in compressed


def test_compress_javascript_code():
    code = """
function test() {
    // Single line
    /* Multi
       line */
    console.log("hi");
}
"""
    compressed = ContextCompressor.compress_code(code, "javascript")
    assert "// Single line" not in compressed
    assert "Multi" not in compressed
    assert "console.log" in compressed


def test_smart_compress_mixed_content():
    content = """
Here is some code:
```python
# comment
x = 10
```
And some text.
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
