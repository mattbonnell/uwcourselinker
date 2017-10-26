import praw
import re
import urllib.request
import ssl
import time
bot = praw.Reddit(user_agent='UWCourseLinker v0.1',
                  client_id='G_x7prJfvUn_dQ',
                  client_secret='42eUAnGe2V5BgKbBqgURUsNj0tI',
                  username='UWCourseLinker',
                  password='Battlefield1')

subreddit = bot.subreddit('uwaterloo')

comments = subreddit.stream.comments()

courseCode = r'[A-z]{2,4} ?[0-9]{3}'

context = ssl._create_unverified_context()

seen_comments_file = open("seen_comments.txt", "r")
seen_comments =[]
for line in seen_comments_file.read().splitlines():
    seen_comments.append(line)
seen_comments_file.close()
seen_comments_file = open("seen_comments.txt", "a")
seen_submissions = []

SELF = "UWCourseLinker"


def get_name_and_url(course_code):
    clean_code = course_code
    "".join(clean_code.split())
    clean_code = clean_code.replace(" ", "")
    clean_code = clean_code.lower()
    url = 'https://uwflow.com/course/' + clean_code
    with urllib.request.urlopen(url, context=context) as response:
        html = response.read()
        title = str(re.search(r'<title>[\s\S]+<\/title>', str(html)))
        name = title[title.find(course_code):title.rfind("-") - 1]
    return name, url


def bot():
    while True:
        try:
            for comment in subreddit.comments():
                if comment.author is not None:
                    text = comment.body
                    author = comment.author
                    if str(author.name) != SELF:
                        codes = re.findall(courseCode, text)
                        message = ""
                        if len(codes) > 0:
                            if comment.id not in seen_comments:
                                seen_comments.append(comment.id)
                                seen_comments_file.write(comment.id + "\n")
                                seen_codes = []
                                for code in codes:
                                    if code not in seen_codes:
                                        print(code)
                                        seen_codes.append(code)
                                        try:
                                            name, url = get_name_and_url(code)
                                            message += "[" + name + "](" + url + ")\n\n"
                                        except Exception as e:
                                            print("Exception:", e)
                                            continue

                                posted_successfully = False
                                while not posted_successfully:
                                    try:
                                        comment.reply(message)
                                        posted_successfully = True
                                    except Exception as e:
                                        print("Exception:", e)
                                        print("Sleeping for 1 minute...")
                                        time.sleep(60)

        except KeyboardInterrupt:
            seen_comments_file.close()
            break
        except Exception as e:
            print("Exception:", e)

if __name__ == '__main__':
    main()