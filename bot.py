#!/usr/bin/env python3

import praw
import re
import urllib.request
import urllib.error
import ssl


GROUP_NAME = "course"
COURSE_CODE_REGEX = "(?P<%s>[A-z]{2,5} ?[0-9]{3}[A-z]?)" % GROUP_NAME
REGEXES = [
        r"\[\[ ?%s ?\]\]",
        r"what is %s",
        r"what's %s",
        ]


def link_format(text, url):
    return "[%s](%s)" % (text, url)


def add_bot_footer(text):
    return text + "\n\n^[feedback]" \
           "(https://www.reddit.com/message/compose?to=UWCourseLinker&subject=Feedback)" \
           " ^| ^[github](https://github.com/mattbonnell/uwcourselinker)"


def post_comment(parent, comment):
    posted_successfully = False
    while not posted_successfully:
        parent.reply(comment)
        posted_successfully = True


def get_course_name(course_code):
    course_url = get_course_url(course_code)
    context = ssl._create_unverified_context()
    with urllib.request.urlopen(course_url, context=context) as response:
        html = response.read()
        code_raw = str(re.search(re.compile('<h1 class="page-title">[A-z\0-9\ ]+</h1>'), str(html)).group())
        code_proper = code_raw[code_raw.find(r'<h1') + 23: code_raw.rfind(r'</')]
        name_raw = str(re.search(re.compile(r'<p class="lead">[A-z\0-9\ ]+</p>'), str(html)).group())
        name_proper = name_raw[name_raw.find(r'<p') + 16:
            None if name_raw.rfind(r'</p>') == -1 else name_raw.rfind(r'</p>')]
    return code_proper + " - " + name_proper


def clean_code(course_code):
    return course_code.replace(" ", "").lower()

def get_course_url(course_code):
    code = clean_code(course_code)
    return 'https://uwflow.com/course/' + code


def main():

    bot = praw.Reddit(user_agent='UWCourseLinker v0.1',
                      client_id='G_x7prJfvUn_dQ',
                      client_secret='42eUAnGe2V5BgKbBqgURUsNj0tI',
                      username='UWCourseLinker',
                      password='QWEiop123890')

    subreddit = bot.subreddit('uwaterloo')

    course_regexes = list(map(lambda r: re.compile(r, re.I), map(lambda s: s % COURSE_CODE_REGEX, REGEXES)))

    seen_submissions_file = open("seen_submissions.txt", "r")
    seen_submissions = []
    for line in seen_submissions_file.read().splitlines():
        seen_submissions.append(line)
    seen_submissions_file.close()
    seen_submissions_file = open("seen_submissions.txt", "a")

    seen_comments_file = open("seen_comments.txt", "r")
    seen_comments = []
    for line in seen_comments_file.read().splitlines():
        seen_comments.append(line)
    seen_comments_file.close()
    seen_comments_file = open("seen_comments.txt", "a")

    SELF = "UWCourseLinker"

    while True:
        try:
            for submission in subreddit.new(limit=25):
                if submission.id not in seen_submissions:
                    seen_submissions.append(submission.id)
                    seen_submissions_file.write(submission.id + "\n")
                    codes = []

                    text = submission.title + " " + submission.selftext
                    for course_regex in course_regexes:
                        codes += [ m.group(GROUP_NAME) for m in re.finditer(course_regex, text)]

                    if len(codes) > 0:
                        reply = ""
                        seen_codes = []
                        for code in codes:
                            code = clean_code(code)
                            if code not in seen_codes:
                                seen_codes.append(code)
                                try:
                                    url = get_course_url(code)
                                    name = get_course_name(code)
                                    reply += link_format(name, url) + "\n\n"
                                except Exception as e:
                                    print("Exception:", e)
                                    continue
                        if reply:
                            try:
                                post_comment(submission, add_bot_footer(reply))
                            except Exception as e:
                                print("Exception:", e)

            for comment in subreddit.comments(limit=50):
                if comment.author is not None:
                    text = comment.body
                    author = comment.author
                    if str(author.name) != SELF:
                        codes = []

                        for course_regex in course_regexes:
                            codes += [ m.group(GROUP_NAME) for m in re.finditer(course_regex, text)]

                        if len(codes) > 0:
                            if comment.id not in seen_comments:
                                seen_comments.append(comment.id)
                                seen_comments_file.write(comment.id + "\n")
                                seen_codes = []
                                reply = ""
                                for code in codes:
                                    code = clean_code(code)
                                    if code not in seen_codes:
                                        seen_codes.append(code)
                                        try:
                                            url = get_course_url(code)
                                            name = get_course_name(code)
                                            reply += link_format(name, url) + "\n\n"
                                        except Exception as e:
                                            print("Exception:", e)
                                            continue
                                if reply:
                                    try:
                                        post_comment(comment, add_bot_footer(reply))
                                    except Exception as e:
                                        print("Exception:", e)

        except KeyboardInterrupt:
            seen_comments_file.close()
            seen_submissions_file.close()
            break
        except Exception as e:
            print("Exception:", e)

if __name__ == "__main__":
    main()
