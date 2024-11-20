import logging
from os import getenv
from file_service import load_file, save_file

FILE_PATH = getenv("POSTS_FILE")


def main() -> None:
    posts = load_file(FILE_PATH)
    # reply_to_message_id = update.message.message_id
    # chat_id = user_data_manager.get_chat_id()
    photo_id = "AgACAgIAAxkBAAINrmc-ATj8lJzJJcCzMDBbeG3hlNHlAAKE6TEb3IPwSdeyurrFgaQFAQADAgADbQADNgQ"

    if not photo_id in posts:
        return
    else:
        print(posts[photo_id]['chat_posts'])


if __name__ == "__main__":
    main()
