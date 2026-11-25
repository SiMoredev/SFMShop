import time
import functools

def timer(repeat: int = 1):
    if repeat < 1:
        raise ValueError("Количество повторений должно быть больше 0")
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            times = []
            result = None
            for _ in range(repeat):
                start = time.perf_counter()
                result = func(*args, **kwargs)
                end = time.perf_counter()
                result_time = end - start
                times.append(result_time)
            min_time = min(times)
            max_time = max(times)
            avg_time = sum(times)/len(times)
            print(f"Функция {func.__name__}: min {min_time:.2e}, max {max_time:.2e}, avg {avg_time:.4e} (повторений: {repeat})")
            return result
        return wrapper
    return decorator

test_list = [i for i in range(10000000)]

@timer(repeat=1)
def linear_search(lst, target):
    for index_item, item in enumerate(lst):
        if item == target:
            return index_item
    return -1

@timer(repeat=5)
def binary_search(sorted_lst, target):
    left = 0
    steps = 0
    right = len(sorted_lst) - 1
    while left <= right:
        steps += 1
        mid = (left + right)//2
        if sorted_lst[mid] == target:
            print(f"Найдено за {steps} шагов")
            return mid
        elif sorted_lst[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1

# print(binary_search(test_list, 9999999))
# print(linear_search(test_list, 9999999))

# data = [1, 3, 5, 7, 9, 11, 13]
# assert binary_search(data, 7) == 3       # середина
# assert binary_search(data, 1) == 0       # первый
# assert binary_search(data, 13) == 6      # последний
# assert binary_search(data, 4) == -1      # нет, внутри диапазона
# assert binary_search(data, 100) == -1    # нет, больше всех
# assert binary_search(data, -5) == -1     # нет, меньше всех
# assert binary_search([], 5) == -1        # пустой список
# assert binary_search([5], 5) == 0        # один элемент, есть
# assert binary_search([5], 3) == -1       # один элемент, нет
# print("binary_search: все тесты пройдены")

# test_list_1 = [i for i in range(1000000)]
# test_dict = {f"key_{value}" : value for value in range(1000000)}

# @timer(repeat=1)
# def check_time(repeat_times, value, values):
#     for _ in range(repeat_times):
#         value in values

# check_time(1000, test_list_1[-1], test_list_1)
# check_time(1000, "key_999999", test_dict)
import random
queries = [random.randint(0, 100_000) for _ in range(10_000)]

users = [{"id": i, "name": f"user_{i}"} for i in range(100000)]

def find_user(users, user_id):
        for user in users:
            if user["id"] == user_id:
                return user
        return None

users_by_id = {user["id"]: user for user in users}

def find_user_fast(users_by_id, user_id):
    return users_by_id.get(user_id)
    
@timer(repeat=1)
def scenario_list(users, queries):
    for q in queries:
        find_user(users, q)

@timer(repeat=1)
def scenario_dict(users, queries):
    users_by_id = {user["id"]: user for user in users}
    for q in queries:
        find_user_fast(users_by_id, q)

# scenario_list(users, queries)
# scenario_dict(users, queries)

lst = list(range(10000))
lst_1 = [1, 1, 1, 1, 1, 1]

@timer(repeat=1)
def has_duplicates_slow(lst):
    for i, item in enumerate(lst):
        if item in lst[i + 1:]:
            return True
    return False

@timer(repeat=1)
def has_duplicates_fast(lst):
    seen = set()
    for item in lst:
        if item in seen:
            return True
        seen.add(item)
    return False

def two_sum(nums, target):
    for i in range(len(nums)):
        for j in range(i+1, len(nums)):
            if nums[i] + nums[j] == target:
                return (i, j)
    return None

def two_sum_fast(nums, target):
    seen = dict()
    for i, x in enumerate(nums):
        need = target - x
        if need in seen:
            return (seen[need], i)
        seen[x] = i
    return None

assert two_sum_fast([2, 7, 11, 15], 9) == (0, 1)    # 2 + 7
assert two_sum_fast([3, 2, 4], 6) == (1, 2)         # 2 + 4, а не 3 + 3
assert two_sum_fast([3, 3], 6) == (0, 1)            # два разных элемента с одинаковым значением
assert two_sum_fast([1, 2], 10) is None

assert two_sum([2, 7, 11, 15], 9) == (0, 1)    # 2 + 7
assert two_sum([3, 2, 4], 6) == (1, 2)         # 2 + 4, а не 3 + 3
assert two_sum([3, 3], 6) == (0, 1)            # два разных элемента с одинаковым значением
assert two_sum([1, 2], 10) is None

assert has_duplicates_slow(lst) == False
assert has_duplicates_fast(lst) == False
assert has_duplicates_slow(lst_1) == True
assert has_duplicates_fast(lst_1) == True
assert find_user(users, 0) == {"id": 0, "name": "user_0"}
# assert find_user(users, 99_999)["name"] == "user_99999"
assert find_user(users, 500_000) is None
