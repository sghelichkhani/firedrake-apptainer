from pathlib import Path
from string import Template
import tomli

bind_path = Path("/mnt")
deps_path = Path("deps")
files_path = Path("files")

def fetch_path(name, config):
    git_path = deps_path / name
    if git_path.exists():
        return bind_path / git_path

    archive_path = files_path / config["archive"]
    if archive_path.exists():
        return bind_path / archive_path

    raise Exception(f"dependency for {name} not found")


def generate_flag(name, path):
    return f"--download-{name}={path}"

if __name__ == "__main__":
    with open("config.toml", "rb") as f:
        config = tomli.load(f)

    args = " ".join(
        generate_flag(name, fetch_path(name, block))
        for name, block in config["petsc"].items()
    )

    with open("petsc.def.tmpl", "r") as f:
        template = Template(f.read())

    with open("petsc.def", "w") as f:
        f.write(template.safe_substitute(flags=args))
