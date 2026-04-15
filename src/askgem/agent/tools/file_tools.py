from pathlib import Path
from pydantic import BaseModel, Field
from .base import BaseTool
from ..schema import ToolResult

class ListDirInput(BaseModel):
    path: str = Field(description="The directory path to list contents of.")

class ListDirTool(BaseTool):
    name = "list_dir"
    description = "Lists files and subdirectories in a given directory."
    input_schema = ListDirInput

    async def execute(self, path: str) -> ToolResult:
        try:
            p = Path(path).resolve()
            if not p.exists() or not p.is_dir():
                return ToolResult(tool_call_id="", content=f"Error: Path '{path}' is not a valid directory.", is_error=True)
            
            items = []
            for item in p.iterdir():
                type_str = "[DIR]" if item.is_dir() else "[FILE]"
                items.append(f"{type_str} {item.name}")
            
            return ToolResult(tool_call_id="", content="\n".join(items))
        except Exception as e:
            return ToolResult(tool_call_id="", content=f"Error listing directory: {str(e)}", is_error=True)

class ReadFileInput(BaseModel):
    path: str = Field(description="The absolute path to the file to read.")

class ReadFileTool(BaseTool):
    name = "read_file"
    description = "Reads the full content of a text file from the local filesystem."
    input_schema = ReadFileInput

    async def execute(self, path: str) -> ToolResult:
        try:
            p = Path(path).resolve()
            if not p.exists() or not p.is_file():
                return ToolResult(tool_call_id="", content=f"Error: File '{path}' not found.", is_error=True)
            
            # Read first 1MB only as a safety measure for now
            content = p.read_text(encoding="utf-8", errors="replace")
            return ToolResult(tool_call_id="", content=content)
        except Exception as e:
            return ToolResult(tool_call_id="", content=f"Error reading file: {str(e)}", is_error=True)

class WriteFileInput(BaseModel):
    path: str = Field(description="The absolute path to the file to create/overwrite.")
    content: str = Field(description="The full content to write to the file.")

class WriteFileTool(BaseTool):
    name = "write_file"
    description = "Creates a new file or overwrites an existing one with full content."
    input_schema = WriteFileInput
    requires_confirmation = True

    async def execute(self, path: str, content: str) -> ToolResult:
        try:
            p = Path(path).resolve()
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            return ToolResult(tool_call_id="", content=f"Successfully written to {path}")
        except Exception as e:
            return ToolResult(tool_call_id="", content=f"Error writing file: {str(e)}", is_error=True)

class EditFileInput(BaseModel):
    path: str = Field(description="The absolute path to the file to edit.")
    old_text: str = Field(description="The exact text block to find and replace.")
    new_text: str = Field(description="The new text block to insert.")

class EditFileTool(BaseTool):
    name = "edit_file"
    description = "Edits an existing file by replacing a specific block of text. Use for targeted changes."
    input_schema = EditFileInput
    requires_confirmation = True

    async def execute(self, path: str, old_text: str, new_text: str) -> ToolResult:
        try:
            p = Path(path).resolve()
            if not p.exists():
                return ToolResult(tool_call_id="", content=f"Error: File '{path}' not found.", is_error=True)
            
            content = p.read_text(encoding="utf-8")
            if old_text not in content:
                return ToolResult(tool_call_id="", content=f"Error: Text block to replace not found in {path}. Make sure the old_text matches exactly.", is_error=True)
            
            new_content = content.replace(old_text, new_text, 1) # Only replace first occurrence for safety
            p.write_text(new_content, encoding="utf-8")
            return ToolResult(tool_call_id="", content=f"Successfully edited {path}")
        except Exception as e:
            return ToolResult(tool_call_id="", content=f"Error editing file: {str(e)}", is_error=True)
