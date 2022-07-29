import argparse
from git import RemoteProgress, Repo
from pathlib import Path
import requests
import tomli
from tqdm import tqdm


class ProgressPrinter(RemoteProgress):
    stage_names = {
        RemoteProgress.COUNTING: "counting",
        RemoteProgress.COMPRESSING: "compressing",
        RemoteProgress.RECEIVING: "receiving",
        RemoteProgress.RESOLVING: "resolving",
    }

    def __init__(self):
        super().__init__()

        self.stage = None
        self._pbar = None

    def update(self, op_code, cur_count, max_count=None, message=""):
        stage = op_code & RemoteProgress.OP_MASK

        if stage != self.stage:
            if self._pbar:
                self._pbar.close()

            self._pbar = tqdm(desc=self.stage_names[stage], total=max_count, position=1)
            self.stage = stage

        if message:
            self._pbar.set_postfix(downloaded=message)

        self._pbar.update(cur_count - self._pbar.n)


def update_repos(repos):
    deps_path = Path("deps")
    deps_path.mkdir(exist_ok=True)

    with tqdm(repos.items()) as t:
        for repo, url in t:
            repo_path = deps_path / repo

            if repo_path.exists():
                t.set_description(f"updating {repo}")
                print()
                r = Repo(repo_path)
                r.remotes.origin.fetch(progress=ProgressPrinter())
            else:
                t.set_description(f"checking out {repo}")
                print()
                Repo.clone_from(
                    url.split("#")[0],
                    deps_path / repo,
                    progress=ProgressPrinter(),
                    bare=True,
                )


def download_archives(archives):
    files_path = Path("files")
    files_path.mkdir(exist_ok=True)

    with tqdm(archives.values()) as t:
        for archive in t:
            archive_path = archive["archive"]
            url = archive["url"]

            file_path = files_path / archive_path
            if file_path.exists():
                continue

            t.set_description(f"downloading {archive_path}")
            r = requests.get(url, stream=True)
            with file_path.open("wb") as f:
                for chunk in tqdm(r.iter_content(1024), unit="kB"):
                    f.write(chunk)


if __name__ == "__main__":
    with open("config.toml", "rb") as f:
        config = tomli.load(f)

    parser = argparse.ArgumentParser(
        description="Fetch Firedrake Apptainer dependencies",
        epilog="With no arguments, downloads git and archive dependencies for Firedrake",
    )
    parser.add_argument(
        "--repos", action="store_true", help="Clone or update all git repositories"
    )
    parser.add_argument(
        "--archives", action="store_true", help="Download source code archives"
    )
    parser.add_argument(
        "--only",
        help="Restrict downloaded dependencies to comma-separated list",
    )
    parser.add_argument(
        "--prefer-archives",
        action="store_true",
        help="Prefer tarball archives to git repositories, for PETSc dependencies",
    )
    parser.add_argument(
        "components",
        nargs="*",
        choices=[[], "firedrake", "petsc"],
        help="Components of which to download dependencies",
    )
    args = parser.parse_args()

    if args.only:
        only_list = [dep.lower() for dep in args.only.split(",")]
        config["repos"] = {
            k: v for k, v in config["repos"].items() if k.lower() in only_list
        }
        config["archives"] = {
            k: v for k, v in config["archives"].items() if k.lower() in only_list
        }
        config["petsc"] = {
            k: v for k, v in config["petsc"].items() if k.lower() in only_list
        }

    if "firedrake" in args.components or not args.components:
        do_all = not (args.repos or args.archives)
        if args.repos or do_all:
            update_repos(config["repos"])

        if args.archives or do_all:
            download_archives(config["archives"])

    if "petsc" in args.components:
        # whether we want to get things that are *only* available through git,
        # or everything available through git
        if args.prefer_archives:
            repos = {
                package: locations["git-url"]
                for package, locations in config["petsc"].items()
                if "archive" not in locations
            }
        else:
            repos = {
                package: locations["git-url"]
                for package, locations in config["petsc"].items()
                if "git-url" in locations
            }

        # download tarball archives for everything else
        archives = {
            package: locations
            for package, locations in config["petsc"].items()
            if package not in repos
        }
        update_repos(repos)
        download_archives(archives)
