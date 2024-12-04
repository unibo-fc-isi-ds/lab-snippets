# Some istruction
1. to do the "get" action, first take the signature with "authenticate" action
2. "authenticate" need user(-u) and password(-p)
3. "get" need user(-u) and admin's signature(-s)


# Lab snippets, examples, and exercises

This repository contains the lab snippets, examples, and exercises 
for the course "Distributed Systems" (module 2) at the University of Bologna. 
The course is part of the Master in Computer Science and Engineering.

Code snippets are organized into directories, on a per-lab basis.
The order by which labs are presented may vary from year to year.
This is what labs are about:
1. Lab 1: Introduction to PyGame and Game Loops
2. Lab 2: UDP sockets
3. Lab 3: TCP sockets
4. Lab 4: Presentation and RPC

## File structure

Each snippet consist of a Python module, which is a file with a `.py` extension.
Snippets paths and names are organized as follows:

```
<root directory>
└── snippets/
    ├── __init__.py
    └── lab<N>/
        └── example<M>_<DESCRIPTION>.py
```

where
- `N` is the lab number
- `M` is the example number
- `DESCRIPTION` is a short description of the example

## Prepare the lack environment

To run the snippets, you need to have __Python__ installed on your machine.

You also need Poetry, a Python dependency manager.
If that's not installed, you can install it by running the following command:

```bash
pip install -r requirements.txt
```

Once Poetry is installed,
you can install the necessary dependencies by running the following command:

```bash
poetry install
```

This will create a virtual environment and install the necessary dependencies.
The virtual environment is created in the `.venv` directory.
Be sure to activate the virtual environment before running the snippets.

```bash
poetry shell
```

> **Note**: after you create the virtual environment, VSCode may ask you to select the Python interpreter.
> You can select the one in the `.venv` directory.
> From the second time one, every time you open this project, 
> you can expect that the virtual environment is activated automatically.

## How to run a snippet

> Do NOT run snippets as standalone scripts.
> I.e., do NOT run them by executing `python path/to/snippet.py`.

> **Note** that the following instructions contain the `poetry run` prefix.
> This is to ensure that the snippet is run within the correct virtual environment.
> If you have activated the virtual environment, you can omit the `poetry run` prefix.

To run a snippet, you can use the following command:

```bash
poetry run python -m snippets --lab <N> --example <M> [ARGS]
# or equivalently:
poetry run python -m snippets -l <N> -e <M> [ARGS]
```

where
- `<N>` is the lab number
- `<M>` is the example number
- `[ARGS]` are the arguments that the snippet accepts

