# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/API/sync.ipynb.

# %% auto 0
__all__ = ['absolute_import', 'nbdev_update']

# %% ../nbs/API/sync.ipynb 3
from .imports import *
from .config import *
from .maker import *
from .process import *
from .export import *

from execnb.nbio import *
from fastcore.script import *
from fastcore.xtras import *

import ast,tempfile
from importlib import import_module

# %% ../nbs/API/sync.ipynb 5
def absolute_import(name, fname, level):
    "Unwarps a relative import in `name` according to `fname`"
    if not level: return name
    mods = fname.split(os.path.sep)
    if not name: return '.'.join(mods)
    return '.'.join(mods[:len(mods)-level+1]) + f".{name}"

# %% ../nbs/API/sync.ipynb 7
_re_import = re.compile("from\s+\S+\s+import\s+\S")

# %% ../nbs/API/sync.ipynb 9
def _to_absolute(code, lib_name):
    if not _re_import.search(code): return code
    res = update_import(code, ast.parse(code).body, lib_name, absolute_import)
    return ''.join(res) if res else code

def _update_lib(nbname, nb_locs, lib_name=None):
    if lib_name is None: lib_name = get_config().lib_name
    absnm = get_config().path('lib_path')/nbname
    nbp = NBProcessor(absnm, ExportModuleProc(), rm_directives=False)
    nbp.process()
    nb = nbp.nb

    for name,idx,code in nb_locs:
        assert name==nbname
        cell = nb.cells[int(idx)]
        directives = ''.join(cell.source.splitlines(True)[:len(cell.directives_)])
        cell.source = directives + _to_absolute(code, lib_name)
    write_nb(nb, absnm)

# %% ../nbs/API/sync.ipynb 10
@functools.lru_cache(maxsize=None)
def _mod_files():
    mdir = get_config().path('lib_path').parent
    midx = import_module(f'{get_config().lib_name}._modidx')
    return L(files for mod in midx.d['syms'].values() for _,files in mod.values()).unique()

# %% ../nbs/API/sync.ipynb 12
def _get_call(s):
    top,*rest = s.splitlines()
    return (*top.split(),'\n'.join(rest))

def _script2notebook(fname:str):
    code_cells = Path(fname).read_text().split("\n# %% ")[1:]
    locs = L(_get_call(s) for s in code_cells if not s.startswith('auto '))
    for nbname,nb_locs in groupby(locs, 0).items(): _update_lib(nbname, nb_locs)

@call_parse
def nbdev_update(fname:str=None): # A Python file name to update
    "Propagate change in modules matching `fname` to notebooks that created them"
    if fname and fname.endswith('.ipynb'): raise ValueError("`nbdev_update` operates on .py files.  If you wish to convert notebooks instead, see `nbdev_export`.")
    if os.environ.get('IN_TEST',0): return
    fname = Path(fname or get_config().path('lib_path'))
    lib_dir = get_config().path("lib_path").parent
    files = globtastic(fname, file_glob='*.py').filter(lambda x: str(Path(x).absolute().relative_to(lib_dir) in _mod_files()))
    files.map(_script2notebook)

