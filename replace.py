import re

with open("bands_swweps.mq5", "r") as f:
    code = f.read()

# Replace timeframes
code = re.sub(r'\bPERIOD_M1\b', '_Period', code)
code = re.sub(r'\bPERIOD_M5\b', 'InpHTF1', code)
code = re.sub(r'\bPERIOD_H1\b', 'InpHTF2', code)

with open("bands_swweps.mq5", "w") as f:
    f.write(code)
