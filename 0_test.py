from collections import defaultdict


def group_by_date(posts):
    grouped = defaultdict(list)

    for post in posts:
        _, date_time, name = post.split("_", 2)
        date = date_time.split(" ")[0]
        grouped[date].append(name)

    result = []
    for date, names in grouped.items():
        result.append(f"{date} [{len(names)}] {', '.join(names)}")

    return result


def main():
    posts = [
        "5099_2024-11-21 20:16_kimoriiii",
        "5110_2024-11-21 20:18_arilaviee",
        "5118_2024-11-22 20:18_angelina_michelle",
        "5128_2024-11-22 20:20_fairytwins",
    ]

    grouped_posts = group_by_date(posts)

    # Вывод результата
    for item in grouped_posts:
        print(item)


if __name__ == "__main__":
    main()
