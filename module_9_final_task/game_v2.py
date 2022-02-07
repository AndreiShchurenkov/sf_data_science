"""Игра угадай число
Компьютер сам загадывает и сам угадывает число от 1 до 100
Выводится среднее и максимальное число попыток для оценки алгоритма
"""

from numpy import mean, random


def predict_by_more_less(number: int) -> int:
    """Угадываем число. После каждой попытки сокращаем границы интервала.
    Если пробное число меньше загаданного, подтягиваем к нему нижнюю границу,
    и наоборот. Новое пробное число выбираем выбираем в середине интевала.

    Args:
        number (int, optional): загаданное число

    Returns:
        int: число попыток
    """

    min = 1
    max = 100

    count = 0

    while True:
        count += 1
        mid = round((min + max)/2)

        # Обрабатываем ситуацию, когда min = 1 и max = 2. При округлении mid
        # будет равен 2. Если задано число 1, мы никогда не найдем его.
        # Можно явно приравнять mid к 1. Число 2 проверено, когда мы
        # устанавливали его верхней границей.
        if min == 1 and max == 2:
            mid = 1

        if mid > number:
            max = mid
        elif mid < number:
            min = mid
        else:
            return count


def score_game(predict_by_more_less) -> int:
    """За какое количество попыток в среднем заданная функция угадывает число.
    Для усреднения делаем 1000 повторений.

    Args:
        predict_by_more_less ([type]): функция угадывания

    Returns:
        int: среднее количество попыток
    """

    count_ls = [] # для сбора числа попыток в каждом повторении
    random.seed(1) # фиксируем сид для воспроизводимости
    random_array = random.randint(1, 101, size=(1000)) # загадали список чисел

    for number in random_array:
        count_ls.append(predict_by_more_less(number))

    score = int(mean(count_ls))

    print(f"Ваш алгоритм угадывает число в среднем за {score} попыток")
    return score


if __name__ == "__main__": # не запускаем при импорте, только при явном вызове
    score_game(predict_by_more_less)
