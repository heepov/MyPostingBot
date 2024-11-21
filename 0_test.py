from collections import Counter


def main() -> None:
    # Исходный массив
    data = [
        "444_2024-11-21 20:28",
        "454_2024-11-21 21:28",
        "444_2024-11-22 20:28",
        "454_2024-11-23 21:28",
    ]
    dates = [item.split("_")[1].split(" ")[0] for item in data]
    date_counts = Counter(dates)
    result = "\n".join(
        [f"{date}: {count} posts" for date, count in date_counts.items()]
    )

    print(result)


if __name__ == "__main__":
    main()
