

def read_file(path: str) -> str:
    """Read a file and return its content as a string."""
    with open(path, "r") as f:
        return f.read()