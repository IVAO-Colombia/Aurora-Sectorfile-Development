#!/usr/bin/env python3
"""
Core installer module for Aurora SectorFiles link setup (Windows).
Expose run(aurora, repo, force=False, dry_run=False, debug=False, progress=None, log=None)

progress callback signature: progress(percent:int) -> None (percent optional; receives -1 for indeterminate)
log callback signature: log(str) -> None
"""
import os
import shutil
import subprocess
from typing import Callable, Optional

# small configuration
FILES_EXTS_TO_LINK_ONCE = {'.isc', '.clr'}
COnew_REL = os.path.join('Include', 'COnew')

def _log(callback: Optional[Callable[[str], None]], msg: str):
    if callback:
        callback(msg)
    else:
        print(msg, end='')

def _try_hardlink(src, dst):
    try:
        os.link(src, dst)
        return True
    except Exception:
        return False

def _try_symlink(src, dst):
    try:
        os.symlink(src, dst)
        return True
    except Exception:
        return False

def _try_mklink_hard(src, dst):
    cmd = f'mklink /H "{dst}" "{src}"'
    r = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return r.returncode == 0

def _make_dir_junction(link_path, target_path):
    cmd = f'mklink /J "{link_path}" "{target_path}"'
    r = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return (r.returncode == 0, r.stdout + r.stderr)

def _create_file_link(src, dst, log_cb=None):
    # remove if exists
    if os.path.exists(dst):
        try:
            os.remove(dst)
        except Exception:
            _log(log_cb, f"Warning: couldn't remove existing {dst}\n")
    if _try_hardlink(src, dst):
        _log(log_cb, f"Hard link: {dst} -> {src}\n")
        return True
    if _try_symlink(src, dst):
        _log(log_cb, f"Symlink: {dst} -> {src}\n")
        return True
    if _try_mklink_hard(src, dst):
        _log(log_cb, f"mklink /H: {dst} -> {src}\n")
        return True
    return False

def find_sectorfile_dir(root: str, accept_empty_named=True, log_cb: Optional[Callable[[str], None]] = None) -> str:
    root = os.path.abspath(root)
    # if root looks like sectorfile, use it
    if os.path.isdir(root) and (os.path.isdir(os.path.join(root, 'Include')) or any(f.lower().endswith('.isc') for _,_,files in os.walk(root) for f in files)):
        return root
    # accept common names under root
    names = ['SectorFiles', 'Sectorfile', 'SectorFile', 'SectorFile-MAIN']
    for n in names:
        cand = os.path.join(root, n)
        if os.path.isdir(cand):
            # accept if contain include or isc files, otherwise allow if named
            if os.path.isdir(os.path.join(cand, 'Include')) or any(f.lower().endswith('.isc') for _,_,files in os.walk(cand) for f in files):
                return cand
            if accept_empty_named:
                _log(log_cb, f"Accepting folder by name: {cand}\n")
                return cand
    # final fallback: search for folder containing Include or .isc
    for dirpath, dirnames, filenames in os.walk(root):
        if 'Include' in dirnames:
            return dirpath
        for f in filenames:
            if f.lower().endswith('.isc'):
                return dirpath
    raise FileNotFoundError(f"Sectorfile folder not found under {root}")

def create_conew_junctions(src_include_conew: str, target_include_dir: str, force=False, log_cb: Optional[Callable[[str], None]]=None):
    os.makedirs(target_include_dir, exist_ok=True)
    created = []
    for name in ('COnew', 'COnew_2'):
        link_path = os.path.join(target_include_dir, name)
        if os.path.exists(link_path):
            if force:
                try:
                    if os.path.isdir(link_path) and not os.path.islink(link_path):
                        shutil.rmtree(link_path)
                    else:
                        os.remove(link_path)
                except Exception as e:
                    _log(log_cb, f"Warning: couldn't remove existing {link_path}: {e}\n")
            else:
                raise FileExistsError(f"{link_path} exists")
        ok, out = _make_dir_junction(link_path, src_include_conew)
        if ok:
            _log(log_cb, f"Directory junction created: {link_path} -> {src_include_conew}\n")
            created.append(link_path)
        else:
            _log(log_cb, f"ERROR creating junction {link_path} -> {src_include_conew}: {out}\n")
    return created

def link_top_level_files_once(src_main: str, sectorfile_dir: str, force=False, log_cb: Optional[Callable[[str], None]]=None):
    count = 0
    for name in os.listdir(src_main):
        src_path = os.path.join(src_main, name)
        if not os.path.isfile(src_path):
            continue
        _, ext = os.path.splitext(name)
        if ext.lower() in FILES_EXTS_TO_LINK_ONCE:
            dst = os.path.join(sectorfile_dir, name)
            if os.path.exists(dst):
                if force:
                    try:
                        os.remove(dst)
                    except Exception as e:
                        _log(log_cb, f"Warning: couldn't remove {dst}: {e}\n")
                else:
                    _log(log_cb, f"Skipping existing {dst}\n")
                    continue
            ok = _create_file_link(src_path, dst, log_cb=log_cb)
            if not ok:
                try:
                    shutil.copy2(src_path, dst)
                    _log(log_cb, f"Copied (fallback): {dst}\n")
                except Exception as e:
                    _log(log_cb, f"ERROR copying {src_path} -> {dst}: {e}\n")
            count += 1
    return count

def run(aurora: str, repo: str, force=False, dry_run=False, debug=False,
        progress: Optional[Callable[[int], None]] = None,
        log: Optional[Callable[[str], None]] = None) -> int:
    """
    Main entry:
    aurora: path to Aurora install root or SectorFiles folder or .exe
    repo: path to repo root or SectorFile-MAIN
    Returns 0 on success, non-zero on error.
    """
    try:
        if aurora.lower().endswith('.exe'):
            aurora_root = os.path.dirname(aurora)
        else:
            aurora_root = aurora
        _log(log, f"Detecting Sectorfile folder under: {aurora_root}\n")
        sectorfile_dir = find_sectorfile_dir(aurora_root, accept_empty_named=True, log_cb=log)
        _log(log, f"Sectorfile root: {sectorfile_dir}\n")

        # determine src_main
        repo_candidate1 = repo
        repo_candidate2 = os.path.join(repo, 'SectorFile-MAIN')
        if os.path.isdir(repo_candidate1) and os.path.isdir(os.path.join(repo_candidate1, 'Include')):
            src_main = repo_candidate1
        elif os.path.isdir(repo_candidate2):
            src_main = repo_candidate2
        else:
            _log(log, f"ERROR: repository SectorFile-MAIN not found at {repo}\n")
            return 2

        src_include_conew = os.path.join(src_main, COnew_REL)
        if not os.path.isdir(src_include_conew):
            _log(log, f"ERROR: expected source Include/COnew at {src_include_conew}\n")
            return 3

        target_include_dir = os.path.join(sectorfile_dir, 'Include')
        _log(log, f"Target Include dir: {target_include_dir}\n")
        if dry_run:
            _log(log, "DRY RUN: no changes will be made.\n")
            _log(log, f"Would create junctions at {target_include_dir}\\COnew and COnew_2 -> {src_include_conew}\n")
            _log(log, f"Would link .isc/.clr from {src_main} into {sectorfile_dir}\n")
            return 0

        os.makedirs(target_include_dir, exist_ok=True)
        if progress:
            progress(-1)  # indeterminate
        create_conew_junctions(src_include_conew, target_include_dir, force=force, log_cb=log)
        linked = link_top_level_files_once(src_main, sectorfile_dir, force=force, log_cb=log)
        _log(log, f"Linked or copied {linked} top-level .isc/.clr files.\n")
        if progress:
            progress(100)
        _log(log, "Done.\n")
        return 0
    except Exception as e:
        _log(log, f"Unhandled error: {e}\n")
        return 10