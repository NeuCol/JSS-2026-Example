import re, sys

def extract(path):
    with open(path) as f:
        text = f.read()
    m = re.search(r"reshape\(\(/(.*?)/\)[\s&]*,[\s&]*\(/\s*9,9,9,9\s*/\)\)", text, re.S)
    body = m.group(1)
    body = body.replace("&", "")
    # split on commas, strip whitespace/newlines, drop empty tokens
    nums = [tok.strip() for tok in body.split(",")]
    nums = [n for n in nums if n != ""]
    assert len(nums) == 9*9*9*9, f"{path}: got {len(nums)} numbers"
    return nums

def render(nums):
    lines = []
    for i in range(0, len(nums), 9):
        row = nums[i:i+9]
        lines.append("    " + ", ".join(row) + ("," if i+9 < len(nums) else ""))
    return "\n".join(lines)

if __name__ == "__main__":
    path = sys.argv[1]
    out = sys.argv[2]
    nums = extract(path)
    with open(out, "w") as f:
        f.write(render(nums))
        f.write("\n")
