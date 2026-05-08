import os, re
from pathlib import Path

# Fix all tools to use Path('.') instead of Path(__file__)
for root, dirs, files in os.walk('tools'):
    for file in files:
        if file.endswith('.py'):
            path = os.path.join(root, file)
            try:
                f = open(path, 'r', encoding='utf-8')
                content = f.read()
                f.close()
                
                if 'Path(__file__).parent.parent.parent' in content:
                    content = content.replace('PROJECT_ROOT = Path(__file__).parent.parent.parent', 'PROJECT_ROOT = Path(".").resolve()')
                    
                    f = open(path, 'w', encoding='utf-8')
                    f.write(content)
                    f.close()
                    print(f'Fixed: {path}')
            except Exception as e:
                print(f'Error {path}: {e}')
print('Done')