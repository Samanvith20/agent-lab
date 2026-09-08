# Agent Lab

Requires Python 3.12 or newer.

## Run locally

From PowerShell in the project folder:

```powershell
cd D:\agent-lab
poetry install
poetry run agent
```

You can also run the package or the script directly:

```powershell
poetry run python -m claude_project
poetry run python claude_project/main.py
```

Run `poetry install` first: the application uses `python-dotenv` and `rich`.
Use the Poetry commands above to select the environment with those dependencies.
The interactive shell supports `/exit`, `/quit`, and `/ask <question>`.
Search and answer generation for `/ask` are not implemented yet.

## Make the command available from any folder

Install with pipx once for your Windows user account:

```powershell
python -m pip install --user pipx
python -m pipx ensurepath
python -m pipx install --editable D:\agent-lab
```

Open a new terminal (restart VS Code if using its integrated terminal), then run
this from any directory:
                                                                                                                                                                                                                                                        
```powershell
agent
```

pipx keeps the application's dependencies in a separate virtual environment and
places its command on your user's PATH. This makes the command available across
folders for your account; it is not a system-wide install for all users.
The editable install uses this source folder, so Python code changes take effect
without reinstalling. Keep the folder in place. After changing dependencies or
command metadata, run `python -m pipx reinstall agent-lab`.

## How it works

`agent-lab` is the distribution name used by installers. `claude_project` is the
importable Python package. The `[project.scripts]` entry in `pyproject.toml` maps
the terminal command `agent` to the `run()` function in `claude_project/main.py`.
Installing the project creates the command launcher; editing the TOML alone
does not create it. Poetry exposes it through `poetry run`; pipx exposes it on
your user's PATH.

The guard in `main.py` calls `run()` when the file is executed directly.
`__main__.py` supports `python -m claude_project`.
