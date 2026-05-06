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
