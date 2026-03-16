"""Extract card data from agent tool result JSON and print Python code."""
import re

path = r'C:\Users\Akhil\.claude\projects\C--Users-Akhil-Documents-cc4e-course-market-week\c1c83caf-9c2c-4bd4-bc4e-d267d306af8b\tool-results\toolu_01QW8jGbQH3VRsFtDec6MQTb.json'

with open(path, encoding='utf-8') as f:
    raw = f.read()

# The text field contains the python code block
# Find ``` python ... ```
start = raw.find('```python')
end = raw.rfind('```')
if start == -1:
    print("No python block found")
else:
    block = raw[start + len('```python'):end]
    # Unescape JSON string escapes
    block = block.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
    with open('extracted_cards.py', 'w', encoding='utf-8') as out:
        out.write(block)
    print("Written to extracted_cards.py")
