from __future__ import annotations

import random

Position = tuple[int, int]
DIRECTIONS = {"w": (0, -1), "s": (0, 1), "a": (-1, 0), "d": (1, 0)}


class GameObject:
    symbol = "?"

    def __init__(self, position: Position) -> None:
        self.position = position

    def __str__(self) -> str:
        return self.symbol


class Apple(GameObject):
    symbol = "*"


class Snake(GameObject):
    symbol = "O"

    def __init__(self, position: Position) -> None:
        super().__init__(position)
        self._body = [position]
        self._direction = DIRECTIONS["d"]

    @property
    def body(self) -> tuple[Position, ...]:
        return tuple(self._body)

    def turn(self, key: str) -> None:
        if key not in DIRECTIONS:
            raise ValueError("Направление: w, a, s или d.")
        direction = DIRECTIONS[key]
        opposite = (-self._direction[0], -self._direction[1])
        if len(self._body) > 1 and direction == opposite:
            return
        self._direction = direction

    def next_position(self, width: int, height: int) -> Position:
        x, y = self.position
        dx, dy = self._direction
        return ((x + dx) % width, (y + dy) % height)

    def move(self, position: Position, grow: bool = False) -> None:
        self.position = position
        self._body.insert(0, position)
        if not grow:
            self._body.pop()


class SnakeGame:
    def __init__(self, width: int = 8, height: int = 8,
                 seed: int | None = None) -> None:
        if (type(width) is not int or type(height) is not int
                or width < 2 or height < 2):
            raise ValueError("Размеры поля должны быть целыми, минимум 2 × 2.")
        self.width = width
        self.height = height
        self.snake = Snake((width // 2, height // 2))
        self._random = random.Random(seed)
        self.apple = self._new_apple()
        self.game_over = False
        self.won = False

    @property
    def score(self) -> int:
        return len(self.snake.body) - 1

    def _new_apple(self) -> Apple | None:
        free = [(x, y) for y in range(self.height) for x in range(self.width)
                if (x, y) not in self.snake.body]
        return Apple(self._random.choice(free)) if free else None

    def step(self, key: str = "") -> None:
        if self.game_over:
            return
        if key:
            self.snake.turn(key)
        position = self.snake.next_position(self.width, self.height)
        grow = self.apple is not None and position == self.apple.position
        occupied = self.snake.body if grow else self.snake.body[:-1]
        if position in occupied:
            self.game_over = True
            return
        self.snake.move(position, grow)
        if grow:
            self.apple = self._new_apple()
            if self.apple is None:
                self.won = True
                self.game_over = True

    def render(self) -> str:
        rows = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                position = (x, y)
                if position == self.snake.position:
                    row.append(str(self.snake))
                elif position in self.snake.body:
                    row.append("o")
                elif (self.apple is not None
                      and position == self.apple.position):
                    row.append(str(self.apple))
                else:
                    row.append(".")
            rows.append(" ".join(row))
        return "\n".join(rows)


def main() -> None:
    game = SnakeGame()
    print("Змейка: w/a/s/d + Enter, Enter — вперёд, q — выход.")
    try:
        while not game.game_over:
            print(game.render())
            print(f"Счёт: {game.score}")
            key = input("Ход: ").strip().lower()
            if key == "q":
                return
            try:
                game.step(key)
            except ValueError as error:
                print(error)
        print(game.render())
        print("Победа!" if game.won else "Столкновение со змейкой.")
        print(f"Счёт: {game.score}")
    except (EOFError, KeyboardInterrupt):
        print("\nИгра завершена.")


if __name__ == "__main__":
    main()
