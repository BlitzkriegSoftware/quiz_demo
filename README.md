# quiz_demo

A Demo of HTMLX against a python FastAPI server

## Sources

* [FastAPI](https://fastapi.tiangolo.com/#run-it)
* [HTMLX](https://htmx.org/)
* [Bootstrap](https://getbootstrap.com/)
* [Icons](https://icons.getbootstrap.com/)
* [Roboto Font](https://fonts.google.com/specimen/Roboto)
* [Punctuation](https://en.wikipedia.org/wiki/List_of_typographical_symbols_and_punctuation_marks)
  
## How to run

```powershell
uv run main.py
```

### Environment Variables

| Variable | Use | Default Value |
| :--- | :--- | :--- |
| QUIZPORT | Port to listen on | 8084 |
| QUIZFILE | Name of quiz file to use appended to DATA/ directory | quiz.json |

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
