import os
import os.path
import shutil
import subprocess
import sys
from pathlib import Path
from shutil import which
from subprocess import CalledProcessError
from typing import Callable

PCB = "packed_codebooks_aoTuV_603.bin"
path = Path(__file__).parent
pwd = Path.cwd()

def get_tool(tool_path: str) -> Path:
    return os.fspath(path / "tools" / tool_path)

class PSArc:
    name: str
    base_path: Path

    def __init__(self, name: str, base_path: str):
        self.name = name
        self.base_path = Path(base_path)
        self.folder = os.path.splitext(self.name)[0]

def fix_exe_command(command: list[str]):
    if sys.platform != "win32":
        command = [which("wine")] + command
    return command

def run_exe(command: list[str], show_output=False, no_exit=False, **kwargs):
    command = fix_exe_command(command)
    try:
        return subprocess.run(command, text=True, stdout=sys.stdout if show_output else subprocess.DEVNULL,
                              stderr=sys.stderr if show_output else subprocess.DEVNULL, check=True, **kwargs)
    except CalledProcessError as e:
        if no_exit:
            raise
        print(e)
        exit(e.returncode)

def get_psarc_paths(psarc: PSArc, source_path: Path, destination_path: Path):
    psarc_path = source_path / psarc.name
    unpack_dir = destination_path / psarc.folder
    return psarc_path, unpack_dir

def count_files_in_psarc(psarc_path: Path):
    files = -1  # ignore first line
    try:
        command = [get_tool("psarc.exe"), "list", os.fspath(psarc_path)]
        p = subprocess.Popen(command, stdout=subprocess.PIPE, bufsize=1,
                             text=True)
        while p.stdout.readline():
            files += 1
        p.stdout.close()
        if (return_code := p.wait()) != 0:
            print(f"Command {command} returned non-zero status code {return_code}")
            exit(return_code)
    except Exception:
        raise
    return files

def unpack_psarc(psarc_path: Path, unpack_dir: Path, on_line: Callable[[str], None]):
    try:
        unpack_dir.mkdir(parents=True, exist_ok=True)
        command = [get_tool("psarc.exe"), "extract", os.fspath(psarc_path)]
        p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=os.fspath(unpack_dir), bufsize=1, text=True)
        while line := p.stdout.readline():
            on_line(line)
        p.stdout.close()
        if (return_code := p.wait()) != 0:
            print(f"Command {command} returned non-zero status code {return_code}")
            print(p.stderr.read(), file=sys.stderr)
            exit(return_code)
    except BaseException:
        shutil.rmtree(unpack_dir)  # Likely corrupted
        raise

def get_wem_file_path(psarc: PSArc, soundbank, source_path: Path, destination_path: Path) -> tuple[Path, Path]:
    file = source_path / psarc.folder / psarc.base_path
    if soundbank["@Language"] != "SFX":
        file = file / soundbank["@Language"].upper()
    file = file / (soundbank["@Id"] + ".WEM")
    dest = destination_path / (os.path.splitext(soundbank["Path"])[0].replace("\\", "/") + ".ogg")
    return file, dest

def process_wem_file(source: Path, destination: Path):
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        run_exe(
            [get_tool("ww2ogg/ww2ogg.exe"), os.fspath(source), "-o", os.fspath(destination), "--pcb",
             get_tool(f"ww2ogg/{PCB}")],
            no_exit=True)
        run_exe([get_tool("revorb.exe"), os.fspath(destination)], no_exit=True)
    except BaseException:
        destination.unlink(missing_ok=True)
        raise
