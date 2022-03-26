import argparse
import hashlib
import os.path
import shutil
import signal
from pathlib import Path
from typing import Dict

import xmltodict
from rich.console import Console
from rich.progress import Progress, TextColumn
from rich.table import Table
from rich.text import Text

from nmssoundunpack.lib import PSArc, get_psarc_paths, count_files_in_psarc, unpack_psarc, get_wem_file_path, \
    process_wem_file

psarcs: list[PSArc] = [
    PSArc("NMSARC.5B11B94C.pak", "AUDIO/WINDOWS"),
    PSArc("NMSARC.FE28D146.pak", "AUDIO")
]

run = True

def main():
    args = parser.parse_args()
    source = Path.cwd() / Path(args.source)
    destination = Path.cwd() / Path(args.destination)
    tmp = Path.cwd() / Path(args.tmp) if args.tmp is not None else destination / Path(
        __file__).parent.name
    keep = args.keep

    for psarc in psarcs:
        psarc_path = source / psarc.name
        if not psarc_path.exists():
            print(f"File {psarc_path} is not found in {source}")
            print("Tip: run with --help to view help")
            exit(1)

    console = Console()

    if not all(get_psarc_paths(psarc, source, tmp)[1].is_dir() for psarc in psarcs):
        with Progress(  # It leaves empty line if no tasks were created
                *Progress.get_default_columns(),
                TextColumn("{task.completed}/{task.total}"),
                console=console) as progress:
            for psarc in psarcs:
                psarc_path, unpack_dir = get_psarc_paths(psarc, source, tmp)
                if unpack_dir.is_dir():
                    console.print(f"Skipping \"{psarc.name}\"")
                    continue
                task = progress.add_task(f"Extracting \"{psarc.name}\"", start=False)
                files_count = count_files_in_psarc(psarc_path)
                progress.update(task, total=files_count)
                progress.start_task(task)
                console.print(
                    Text("Extracting ").append(stylize_path(psarc_path)).append(" to ").append(stylize_path(unpack_dir))
                )
                unpack_psarc(psarc_path, unpack_dir, lambda x: progress.update(task, advance=1))
    else:
        for psarc in psarcs:
            console.print(f"Skipping \"{psarc.name}\"")

    files: Dict[Path, Path] = {}
    with Progress(console=console) as progress:
        console.print("Constructing source-destination pairs")
        task = progress.add_task("Constructing source-destination pairs", total=len(psarcs), start=False)
        for psarc in psarcs:
            before = len(files)
            task_collecting_files = progress.add_task(f"Collecting files from {psarc.name}", start=False)
            with (tmp / os.path.splitext(psarc.name)[0] / psarc.base_path / "SOUNDBANKSINFO.XML").open("rb") as f:
                files_xml = xmltodict.parse(f)["SoundBanksInfo"]["StreamedFiles"]["File"]
                progress.update(task_collecting_files, total=len(files_xml))
                console.print(f"Collecting files from {psarc.name}")
                progress.start_task(task_collecting_files)
                progress.start_task(task)
                for file in files_xml:
                    wem_path, converted_path = get_wem_file_path(psarc, file, tmp, destination)
                    if wem_path.exists():
                        if converted_path not in files:
                            files[converted_path] = wem_path
                        # region On collision
                        elif files[converted_path] != wem_path:
                            dict_file_md5 = md5_of_file(files[converted_path], progress)
                            this_file_md5 = md5_of_file(wem_path, progress)
                            if dict_file_md5.digest() != this_file_md5.digest():  # Just in case
                                console.print(
                                    Text("File ").append(stylize_path(converted_path)).append(" has collision:"))
                                console.print(stylize_path(files[converted_path]))
                                console.print(stylize_path(wem_path))
                                counter = 1
                                split_path = list(os.path.splitext(os.fspath(converted_path)))
                                split_path.insert(-1, f"_{counter}")
                                add = True
                                while (converted_path := Path("".join(split_path))) in files:
                                    dict_file_md5 = md5_of_file(files[converted_path], progress)
                                    if dict_file_md5.digest() != this_file_md5.digest():
                                        counter = counter + 1
                                        split_path[-2] = f"_{counter}"
                                        continue
                                    else:
                                        add = False
                                        break
                                if add:
                                    files[Path("".join(split_path))] = wem_path
                        # endregion
                    progress.update(task_collecting_files, advance=1)
            progress.update(task, advance=1)
            console.print(f"{len(files) - before} files collected from {psarc.name}")

    # Add handlers so that Ctrl+C doesn't break files
    signal.signal(signal.SIGINT, interrupt)
    signal.signal(signal.SIGTERM, interrupt)
    signal.signal(signal.SIGHUP, interrupt)
    console.print(f"{len(files)} files to proceed")
    converted = 0
    errors = []
    skipped = 0

    with Progress(
            *Progress.get_default_columns(),
            TextColumn("{task.completed}/{task.total}"),
            console=console) as progress:
        task = progress.add_task("Converting files", total=len(files))
        for destination in files:
            source = files[destination]
            if not destination.exists():
                try:
                    process_wem_file(source, destination)
                    converted += 1
                except Exception:
                    errors.append((source, destination))
                    console.print(f"An error occurred while converting {source} to {destination}")
                    console.print_exception()
            else:
                skipped += 1
            progress.update(task, advance=1, description=f"Converting files ({skipped} skipped, {len(errors)} errors)")
            if not run:
                break
    if run and not keep:
        console.print("Clearing temporary directory")
        shutil.rmtree(tmp)
    console.print(f"{'Done' if run else 'Interrupted'}. "
                  f"{converted} files converted, {skipped} files skipped and {len(errors)} errors")
    if errors:
        table = Table(title="Errors")
        table.add_column("Source", overflow="fold")
        table.add_column("Destination", overflow="fold")
        for error in errors:
            table.add_row(str(error[0]), str(error[1]))
        console.print(table)

# noinspection PyUnusedLocal
def interrupt(signal_num, stack_frame):
    global run
    run = False

def md5_of_file(file: Path, progress: Progress):
    md5 = hashlib.md5()
    task = progress.add_task(f"Calculating md5 ({file.name})", total=file.stat().st_size)
    with file.open("rb") as f:
        while data := f.read(4096):
            md5.update(data)
            progress.update(task, advance=len(data))
    progress.remove_task(task)
    return md5

# For argparse
def dir_path(path_):
    if os.path.isdir(path_):
        return path_
    else:
        raise NotADirectoryError(path_)

def new_dir_path(path_):
    if os.path.isfile(path_):
        raise NotADirectoryError(path_)
    return path_

def stylize_path(path: Path) -> Text:
    parent = Text(str(path.parent) + "/")
    parent.stylize("repr.path")
    filename = Text(str(path.name))
    filename.stylize("repr.filename")
    return parent.append(filename)

parser = argparse.ArgumentParser(description="Unpack, convert and catalog No Man's Sky sound assets")
parser.add_argument("--source", type=dir_path, default=os.getcwd(), metavar="path",
                    help="Source directory (usually game installation directory plus GAMEDATA/PCBANKS)")
parser.add_argument("--destination", type=new_dir_path, default=os.getcwd(), metavar="path",
                    help="Destination directory")
parser.add_argument("--tmp", type=new_dir_path, metavar="path",
                    help="Temporary directory to unpack archives")
parser.add_argument("-k", "--keep", action="store_const", const=True, default=False, dest="keep",
                    help="Keep temporary files")

if __name__ == "__main__":
    main()
