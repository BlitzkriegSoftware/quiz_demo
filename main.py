import json
import os
from pathlib import Path
from typing import Annotated, List
from fastapi.responses import HTMLResponse
import uvicorn
from fastapi import FastAPI, Form, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from functools import cache

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GuessResult:
    def __init__(self, html: str, isDone: int):
        self.html = html
        self.isDone = isDone


class Answer(BaseModel):
    choice: str
    correct: bool


class Question(BaseModel):
    question: str
    answers: List[Answer]

    @field_validator("answers")
    @classmethod
    def must_have_exactly_one_correct_answer(
        cls, answers: List[Answer]
    ) -> List[Answer]:
        correct_count = sum(a.correct for a in answers)
        if correct_count != 1:
            raise ValueError(
                f"Expected exactly 1 correct answer, found {correct_count}"
            )
        return answers

    @property
    def correct_answer(self) -> Answer:
        return next(a for a in self.answers if a.correct)


def safe_int(value, default=0):
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def load_quiz(path: str | Path) -> List[Question]:
    """Load a quiz JSON file into a list of Question instances."""
    data = json.loads(Path(path).read_text())
    return [Question.model_validate(item) for item in data]


@cache
def quizGet():
    quizfile = os.getenv("QUIZFILE", "quiz.json")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    quizfilepath = os.path.join(script_dir, "data", quizfile)
    quiz = load_quiz(quizfilepath)
    return quiz


def html_quiz() -> str:
    quiz = quizGet()
    html = ""
    for i, q in enumerate(quiz, start=1):
        html += f"{i}. {q.question.strip()}<br/><ul>"
        for a in q.answers:
            marker = "✓" if a.correct else " "
            html += f"<li>[{marker}] {a.choice}</li>"
        html += "</ul>"
        html += f"<p>correct: {q.correct_answer.choice}</p>"
    return html


def print_quiz():
    quiz = quizGet()
    for i, q in enumerate(quiz, start=1):
        print(f"{i}. {q.question.strip()}")
        for a in q.answers:
            marker = "✓" if a.correct else " "
            print(f"   [{marker}] {a.choice}")
        print(f"   -> correct: {q.correct_answer.choice}\n")


def make_answer_button(index: int):
    html = "<button"
    html += f" id='guess+{index}'"
    html += " class='btn btn-secondary btn-sm actionbutton'"
    html += " hx-post'/guess'"
    html += " hx-include='#nextq'"
    html += " hx-include='#score'"
    html += " hx-target='#result'"
    html += ">"
    html += f"{index}"
    html += "</button> "
    return html


def format_question(index: int) -> str:
    quiz = quizGet()
    it = quiz[index]
    html = "<div class='quizbody'>"
    html += "  <div class='quizquestion'>"
    html += it.question
    html += "  </div>"
    html += "  <div class='quizanswers'>"
    html += "    Select from one of these answers:"
    html += "    <ol>"
    for id, value in enumerate(it.answers):
        html += "      "
        html += make_answer_button(id)
        html += f"      <li id='ans-{id}'>"
        html += value.choice
        html += "</li>"
    html += "    </ol>"
    html = "  </div>"
    html += "</div>"
    return html


def end_of_quiz(score: str) -> str:
    quiz = quizGet()
    qlen: int = len(quiz) - 1
    html = f"<div class='quizover'>Quiz Over! Score {score} out of {qlen}</div>"
    return html


def next_question(nextq: str, score: str) -> GuessResult:
    quiz = quizGet()
    nq = safe_int(nextq)
    qlen: int = len(quiz) - 1
    if nq > qlen:
        return GuessResult(end_of_quiz(score), 1)
    else:
        nq = nq + 1
        return GuessResult(format_question(nq), 0)


def add_header(response: Response, score: str, nextq: str, bdone):
    if len(score.strip()) <= 0:
        score = "0"
    if len(nextq.strip()) <= 0:
        nextq = "-1"
    if len(bdone.strip()) <= 0:
        bdone = "0"

    response.headers["HX-Trigger"] = (
        f'{{"updateState": {{"score":{score}, "nextq": {nextq}, "bdone": {bdone} }}}}'
    )
    return


@app.post("/guess", response_class=HTMLResponse)
def guess(
    response: Response,
    nextq: Annotated[str | None, Form()] = "-1",
    score: Annotated[str | None, Form()] = "0",
    bdone: Annotated[str | None, Form()] = "0",
): ...


@app.post("/new", response_class=HTMLResponse)
def new_game(
    response: Response,
    nextq: Annotated[str | None, Form()] = "-1",
    score: Annotated[str | None, Form()] = "0",
    bdone: Annotated[str | None, Form()] = "0",
):
    nextq = "-1"
    score = "0"
    result = next_question(nextq, score)
    bdone = "0" if result.isDone else "1"
    add_header(response, score, nextq, bdone)
    return result.html


@app.get("/print", response_class=HTMLResponse)
def all_quiz(
    response: Response,
    nextq: Annotated[str | None, Form()] = "-1",
    score: Annotated[str | None, Form()] = "0",
    bdone: Annotated[str | None, Form()] = "0",
):
    return html_quiz()


if __name__ == "__main__":
    _ = quizGet()
    port = int(os.getenv("QUIZPORT", 8084))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
