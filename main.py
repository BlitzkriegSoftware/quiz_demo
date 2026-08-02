"""
main Module
=================
Quiz Demo: HTMX + FastAPI


Environment Variables

    * QUIZPORT: Port to listen on, please see README.md
    * QUIZFILE: Path to Quiz JSON, just 'filename.json'

"""

import json
import os
from pathlib import Path
from typing import List
from pydantic import BaseModel, field_validator
from fastapi.responses import HTMLResponse
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from functools import cache
import uvicorn

"""
Must set a CORS policy, this one is not suitable for production!
expose_headers must include the list of 'hx-' headers you plan to use!
"""
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
    """
    Class: payload containing needed state for processing

    Args:
        html: markup to return to client
        qid: question id
        isDone: Is quiz over? 0 if not, 1 is so
    """

    def __init__(self, html: str, qid: int, isDone: int):
        self.html = html
        self.qid = qid
        self.isDone = isDone


class Answer(BaseModel):
    """
    Class: Answer

    Args:
        choice: text of the potential answer
        correct: bool true if this is the answer, false if not
    """

    choice: str
    correct: bool


class Question(BaseModel):
    """
    Class: Question

    Args:
        question: text of the question
        answers: potential answers only 1 can be correct
    """

    question: str
    answers: List[Answer]

    @field_validator("answers")
    @classmethod
    def must_have_exactly_one_correct_answer(
        cls, answers: List[Answer]
    ) -> List[Answer]:
        """
        Validates that answer is well formed

        Args:
            cls: instance
            answers: list of answers
        """
        correct_count = sum(a.correct for a in answers)
        if correct_count != 1:
            raise ValueError(
                f"Expected exactly 1 correct answer, found {correct_count}"
            )
        return answers

    @property
    def correct_answer(self) -> Answer:
        """
        Select correct answer
        """
        return next(a for a in self.answers if a.correct)


def safe_int(value, default=0):
    """
    Function to safely convert a string to a number, with default if unsuccessful

    Args:
        value: to be converted
        default: value if unsuccessful

    Returns:
        converted int
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def load_quiz(path: str | Path) -> List[Question]:
    """
    Load a quiz JSON file into a list of Question instances.

    Args:
        path: path to quiz JSON file

    Returns:
        Quiz as an array of Questions
    """
    data = json.loads(Path(path).read_text())
    return [Question.model_validate(item) for item in data]


def quizFromDisk(quizfile: str | Path) -> List[Question]:
    """
    Gets a quiz from disk but only from data/ folder

    Args:
        quizfile: just filename of quiz

    Returns:
        Quiz as an array of Questions
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    quizfilepath = os.path.join(script_dir, "data", quizfile)
    quiz = load_quiz(quizfilepath)
    return quiz


@cache
def quizGet() -> List[Question]:
    """
    Get current quiz (cached)

    Returns:
        Quiz as an array of Questions
    """
    quizfile = os.getenv("QUIZFILE", "quiz.json")
    quiz = quizFromDisk(quizfile)
    return quiz


def quiz_as_html() -> str:
    """
    Render quiz as an HTML snippet to be returned to UI

    Returns:
        HTML Markup Snippet
    """
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
    """
    Prints the quiz as formatted text
    """
    quiz = quizGet()
    for i, q in enumerate(quiz, start=1):
        print(f"{i}. {q.question.strip()}")
        for a in q.answers:
            marker = "✓" if a.correct else " "
            print(f"   [{marker}] {a.choice}")
        print(f"   -> correct: {q.correct_answer.choice}\n")


def make_answer_button(index: int, caption: str) -> str:
    """
    Make a button representing the potential answer to a question

    Args:
        index: index of answer (zero to ...) to make elements unique
        caption: for the button

    Returns:
        HTML Markup Snippet of the Button
    """
    html = "<button"
    html += f" id='guess-{index}'"
    html += " class='btn btn-secondary btn-sm btn-info actionbutton'"
    html += f" hx-post='guess?choic={index}'"
    html += " hx-include='#bdone, #nextq, #score'"
    html += " hx-target='#result'"
    html += ">"
    html += caption
    html += "</button> "
    return html


def question_as_html(index: int) -> str:
    """
    Render the question as html

    Args:
        index: which quiz question (0...)

    Returns:
        HTML Snippet of Question and Choicess
    """
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
    """
    Message for the end of the quiz, w. score

    Args:
        score: current score

    Returns:
        HTML Snippet for End of Quiz
    """
    quiz = quizGet()
    qlen: int = len(quiz)
    html = f"<div class='quizover'>Quiz Over! Score {score} out of {qlen}</div>"
    return html


def next_question(nextq: str, score: str, msg: str) -> GuessResult:
    """
    Get next question or end of quiz

    Args:
        nextq: next question
        score: score
        msg: (optional) message to return

    Returns:
        Instance of GuessResult
    """
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
    """
    create a well formed html header from state variables

    Args:
        response: (fastapi)
        nextq: next question
        score: (sic)
        bdone: 0=not, 1=done
    """
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
async def guess(
    request: Request,
    response: Response,
) -> str:
    """
    post /guess: logic to see if guess is correct

    Args:
        request: (fastapi)
        response: (fastapi)

    Returns:
        HTML Snippet of the result of the guess
    """
    formData = await request.form()
    bdone = formData.get("bdone")
    nextq = formData.get("nextq")
    score = formData.get("score")
    quiz = quizGet()
    choic = request.query_params.get("choic")
    iChoice = safe_int(choic)
    iScore = safe_int(score)
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
    bdone = "0"
    if result.isDone > 0:
        bdone = "1"
    add_header(response, str(iNextQ), str(iScore), bdone)
    return result.html


@app.post("/new", response_class=HTMLResponse)
async def new_game(
    request: Request,
    response: Response,
) -> str:
    """
    post /new: start a new game

    Args:
        request (Request): FastAPI Request
        response (Response): FastAPI Reponse

    Returns:
        str: HTML Snippet
    """
    formData = await request.form()
    bdone = formData.get("bdone")
    nextq = formData.get("nextq")
    score = formData.get("score")

    nextq = "0"
    score = "0"
    result = next_question(nextq, score, "")
    bdone = "0"
    if result.isDone > 0:
        bdone = "1"
    add_header(response, nextq, score, bdone)
    return result.html


@app.get("/print", response_class=HTMLResponse)
def all_quiz(response: Response) -> str:
    """
    get /print: return quiz as html

    Args:
        response: (fastapi)
    """
    return quiz_as_html()


if __name__ == "__main__":
    _ = quizGet()
    port = int(os.getenv("QUIZPORT", 8084))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
