import base64
import re
from pathlib import Path


def base64_to_pic(base64_str):
    base64_str = re.sub("^.*?base64://", "", base64_str)
    base64_bs = base64.b64decode(base64_str)

    # 固定名称
    name = '1.png'

    path = Path("temp", "image", name)
    if not path.parent.exists():
        path.parent.mkdir(parents=True)
    with path.open('wb') as f:
        f.write(base64_bs)
    return str(path)
