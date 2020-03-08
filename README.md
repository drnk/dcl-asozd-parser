# dcl-asozd-parser

[Open Office XML (docx)](https://ru.wikipedia.org/wiki/Office_Open_XML) files parser


Requirements
------------

You need Python 3.7 or later to run dcl-asozd-parser.

Used packages:
* beautifulsoup4
* lxml

## Installation

1. Clone a repository:

   ```bash
   git clone git@github.com:drnk/dcl-asozd-parser.git
   ```

2. Create virtual environment and start it:

   ```bash
   cd dcl-asozd-parser
   python -m venv .venv

   # unix
   source .venv/bin/activate
   # windows
   .venv\Scripts\activate.bat
   ```

3. Upgrade `pip` and download and install necessary libraries:

   ```bash
   python -m pip install -U pip
   pip install -r requirements.txt
   ```

## Testing

```bash
pytest
```

## Running

To parse all files end ups with `итоговая карточка`, run:

```bash
python parse.py "in" --source-mask=".*,\s*итоговая карточка.docx"
```
