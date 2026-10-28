import subprocess
import sys

import pytest

from exercises.snake import Apple, GameObject, Snake, SnakeGame


def test_objects_and_render():
    game = SnakeGame(4, 4, seed=1)
    assert isinstance(game.snake, GameObject)
    assert isinstance(game.apple, GameObject)
    assert str(game.snake) == "O" and str(game.apple) == "*"
    assert game.render().count("O") == 1
    assert game.render().count("*") == 1
    assert game.apple.position not in game.snake.body


def test_growth_and_no_reverse():
    game = SnakeGame(4, 4, seed=1)
    game.apple = Apple((3, 2))
    game.step("d")
    assert game.score == 1 and game.snake.body == ((3, 2), (2, 2))
    assert game.apple.position not in game.snake.body
    game.step("a")
    assert game.snake.position == (0, 2)
    assert game.score == 1


def test_collision_and_stop():
    game = SnakeGame(4, 4, seed=1)
    game.snake = Snake((0, 0))
    for position in [(1, 0), (1, 1), (0, 1), (0, 0)]:
        game.snake.move(position, grow=True)
    game.apple = Apple((3, 3))
    before = game.snake.body
    game.step("d")
    assert game.game_over and not game.won
    assert game.snake.body == before
    game.step("w")
    assert game.snake.body == before


def test_moving_into_vacated_tail_is_allowed():
    game = SnakeGame(4, 4, seed=1)
    game.snake = Snake((1, 0))
    for position in [(1, 1), (0, 1), (0, 0)]:
        game.snake.move(position, grow=True)
    game.apple = Apple((3, 3))
    game.step("d")
    assert not game.game_over
    assert game.snake.position == (1, 0)


def test_full_board_win():
    game = SnakeGame(2, 2, seed=1)
    game.snake = Snake((0, 0))
    game.snake.move((0, 1), grow=True)
    game.snake.move((1, 1), grow=True)
    game.apple = Apple((1, 0))
    game.step("w")
    assert game.won and game.game_over and game.apple is None
    assert game.score == 3


@pytest.mark.parametrize("width,height", [(0, 8), (8, 1), (True, 8), (2.5, 8)])
def test_invalid_board(width, height):
    with pytest.raises(ValueError):
        SnakeGame(width, height)


def test_invalid_direction_does_not_move():
    game = SnakeGame(seed=1)
    before = game.snake.body
    with pytest.raises(ValueError):
        game.step("bad")
    assert game.snake.body == before


def test_terminal_exit():
    result = subprocess.run([sys.executable, "-m", "exercises.snake"],
                            input="q\n", text=True, capture_output=True,
                            check=True)
    assert "Счёт: 0" in result.stdout
