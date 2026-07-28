# quiz_demo

A Demo of HTMLX against a python FastAPI server

- [quiz\_demo](#quiz_demo)
  - [Special thanks](#special-thanks)
  - [Sources](#sources)
  - [How to run](#how-to-run)
    - [Debug .vscode/launch.json](#debug-vscodelaunchjson)
    - [Environment Variables](#environment-variables)
  - [Quiz File Format](#quiz-file-format)

## Special thanks

[Claude](https://support.claude.com/en/articles/10065433-install-claude-desktop) rocks. I would get stuck and it always had the answer with clear examples.

## Sources

Here are the sources for this demo:

- [FastAPI](https://fastapi.tiangolo.com/#run-it)
- [HTMLX](https://htmx.org/)
- [Bootstrap](https://getbootstrap.com/)
- [Icons](https://icons.getbootstrap.com/)
- [Roboto Font](https://fonts.google.com/specimen/Roboto)
- [Punctuation](https://en.wikipedia.org/wiki/List_of_typographical_symbols_and_punctuation_marks)
  
## How to run

1. Optionally restore packages with:

  ```powershell
  uv sync
  ```

2. Then

  ```powershell
  uv run main.py
  ```
3. Open index.html in a browser

Then open `index.html` in a browser (or live server).

### Debug .vscode/launch.json

Here is the configuration snippet

```json
{
    "name": "debug",
    "type": "debugpy",
    "request": "launch",
    "cwd":"${workspaceFolder}",
    "program": "main.py",
    "console": "integratedTerminal"
}
```


### Environment Variables

| Variable | Use | Default Value |
| :--- | :--- | :--- |
| QUIZPORT | Port to listen on | 8084 |
| QUIZFILE | Name of quiz file to use appended to DATA/ directory | quiz.json |

> If you change the port, it needs to be done in `index.html` too!

```html
<html lang="en">
  <head>
    <!-- if you change the port change this -->
    <base href="http://localhost:8084" />
```

## Quiz File Format

Each file is an array of quiz questions (one topic per file), as follows:

```json
    "question": "Question should end in '?'",
    "answers": [
      { "choice": "", "correct": false },
      { "choice": "", "correct": false },
      { "choice": "", "correct": false },
      { "choice": "", "correct": false },
      { "choice": "", "correct": false }
    ]
  },
```

Notes:

1. Question should end in a '?'
2. Answers Array (try to keep it less than 10 entires)
3. One choice should be marked `true` the other should be `false`
4. The array can safely be 3-300 questions
