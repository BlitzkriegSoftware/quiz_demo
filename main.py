import json
import os
from pathlib import Path
from typing import Annotated, List
from fastapi.responses import HTMLResponse
import uvicorn
from fastapi import FastAPI, Form, Request, Response
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
    expose_headers=["hx-trigger"],
)


class GuessResult:
    def __init__(self, html: str, qid: int, isDone: int):
        self.html = html
        self.qid = qid
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


def quiz_as_html() -> str:
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


def quiz_as_text():
    quiz = quizGet()
    for i, q in enumerate(quiz, start=1):
        print(f"{i}. {q.question.strip()}")
        for a in q.answers:
            marker = "✓" if a.correct else " "
            print(f"   [{marker}] {a.choice}")
        print(f"   -> correct: {q.correct_answer.choice}\n")


def make_answer_button(index: int, caption: str):
    json = "{ "
    json += "choice:"
    json += str(index)
    json += " }"

    html = "<button"
    html += f" id='guess-{index}'"
    html += " class='btn btn-secondary btn-sm btn-info actionbutton'"
    html += " hx-post='guess'"
    html += f'hx-vals="js:{json}"'
    html += " hx-include='#bdone'"
    html += " hx-include='#nextq'"
    html += " hx-include='#score'"
    html += " hx-target='#result'"
    html += ">"
    html += caption
    html += "</button> "
    return html


def question_as_html(index: int) -> str:
    quiz = quizGet()
    it = quiz[index]
    html = ""
    html += "<div class='quizbody'>"
    html += "  <div class='quizquestion'>"
    html += it.question
    html += "  </div>"
    html += "  <div class='quizanswers'>"
    html += "    Select from one of these answers:"
    html += "    <ul>"
    for id, value in enumerate(it.answers):
        html += f"<li id='ans-{id}'>"
        html += make_answer_button(id, value.choice)
        html += "</li>"
    html += "    </ul>"
    html += "  </div>"
    html += "</div>"
    return html


def end_of_quiz(score: str) -> str:
    quiz = quizGet()
    qlen: int = len(quiz) - 1
    html = f"<div class='quizover'>Quiz Over! Score {score} out of {qlen}</div>"
    return html


def next_question(nextq: str, score: str, msg: str) -> GuessResult:
    quiz = quizGet()
    iNextQ = safe_int(nextq)
    if iNextQ < 0:
        iNextQ = 0
    qlen: int = len(quiz) - 1
    if iNextQ > qlen:
        html = end_of_quiz(score)
        if len(msg) > 0:
            html = f"<h3>{msg}</h3>" + html
        return GuessResult(html, iNextQ, 1)
    else:
        html = question_as_html(iNextQ)
        if len(msg) > 0:
            html = f"<h3>{msg}</h3>" + html
        return GuessResult(html, iNextQ, 0)


def add_header(response: Response, nextq: str, score: str, bdone: str):
    if len(score.strip()) <= 0:
        score = "0"
    if len(nextq.strip()) <= 0:
        nextq = "0"
    if len(bdone.strip()) <= 0:
        bdone = "0"

    response.headers["HX-Trigger"] = (
        f'{{"updateState": {{"nextq": {nextq}, "score":{score}, "bdone": {bdone} }}}}'
    )
    return


@app.post("/guess", response_class=HTMLResponse)
def guess(
    response: Response,
    nextq: Annotated[str | None, Form()] = "0",
    score: Annotated[str | None, Form()] = "0",
    bdone: Annotated[str | None, Form()] = "0",
    choic: Annotated[str | None, Form()] = "0",
):
    # print(request)
    quiz = quizGet()
    iScore = safe_int(score)
    iChoice = safe_int(choic)
    iNextQ = safe_int(nextq)
    if iNextQ < 0:
        iNextQ = 0

    tq = quiz[iNextQ]
    sCorrectAnswer = tq.correct_answer.choice
    sChoice = tq.answers[iChoice].choice

    msg = "Incorrect Answer"
    if sChoice == sCorrectAnswer:
        iScore = iScore + 1
        msg = "Correct Answer"

    iNextQ = iNextQ + 1
    result = next_question(str(iNextQ), str(iScore), msg)
    bdone = "0" if result.isDone else "1"
    add_header(response, str(iNextQ), str(iScore), bdone)
    return result.html


@app.post("/new", response_class=HTMLResponse)
def new_game(
    response: Response,
    nextq: Annotated[str | None, Form()] = "0",
    score: Annotated[str | None, Form()] = "0",
    bdone: Annotated[str | None, Form()] = "0",
):
    nextq = "0"
    score = "0"
    result = next_question(nextq, score, "")
    bdone = "0" if result.isDone else "1"
    add_header(response, nextq, score, bdone)
    return result.html


@app.get("/print", response_class=HTMLResponse)
def all_quiz(
    response: Response,
    nextq: Annotated[str | None, Form()] = "0",
    score: Annotated[str | None, Form()] = "0",
    bdone: Annotated[str | None, Form()] = "0",
):
    return quiz_as_html()


if __name__ == "__main__":
    _ = quizGet()
    port = int(os.getenv("QUIZPORT", 8084))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
