import click
import textwrap
import tweepy
from os.path import join, expanduser
from fpdf import FPDF
from configparser import ConfigParser


pdf_w = 210
pdf_h = 297

configuration = ConfigParser()
configuration.read(join(expanduser("~"), ".twitter_api"))

CONSUMER_KEY = configuration.get("defaults", "CONSUMER_KEY")
CONSUMER_SECRET = configuration.get("defaults", "CONSUMER_SECRET")
ACCESS_TOKEN = configuration.get("defaults", "ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = configuration.get("defaults", "ACCESS_TOKEN_SECRET")


class PDF(FPDF):
    def texts(self, tweet_content):
        txt = "\n".join(tweet_content)
        self.set_xy(10.0, 80.0)
        self.set_text_color(76.0, 32.0, 250.0)
        self.set_font("Arial", "", 15)
        self.multi_cell(0, 10, txt)


class Thread:
    def __init__(self):
        self.Auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
        self.Auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
        self.api = tweepy.API(self.Auth)

    def get_thread(self, status_id, thread=None):
        status = (
            self.api.get_status(status_id, tweet_mode="extended")
            if status_id is None
            else self.api.get_status(status_id, tweet_mode="extended")
        )
        thread = [] if thread is None else thread
        status_id = status.in_reply_to_status_id
        tweet = str(status.full_text)
        thread.append(tweet)
        if status_id is None:
            return thread
        return self.get_thread(status_id, thread)

    def convert_to_post(self, status_id):
        thread = self.get_thread(status_id)
        return reversed(thread)

    def _check_username(self, user):
        user = self.api.get_user(user)
        screen_name = user.screen_name
        return screen_name

    def _convert_username(self, username):
        mention = f"@{self._check_username(username)} "
        return mention

    def post_thread(self, sentences, username, in_reply_to_status_id=None, thread=None):
        mention = self._convert_username(username)
        mention_length = len(mention)
        left = 280 - mention_length

        thread = [] if thread is None else thread
        tweets = textwrap.wrap(sentences, width=left)
        for tweet in tweets:
            sentences = sentences[len(tweet) :]
            tweet = self.api.update_status(mention + f"{tweet}", in_reply_to_status_id)
            thread.append(tweet.id)
            if sentences is None:
                return thread
            else:
                in_reply_to_status_id = int(tweet.id)
                return self.post_thread(
                    sentences, mention, in_reply_to_status_id, thread
                )


@click.command()
@click.option("-d", "--debug", help="Debug", is_flag=True, default=False)
@click.option("-v", "--verbose", help="Verbose", is_flag=True, default=False)
@click.option("-t", "--tweet_id", help="Thread ID to download")
@click.option(
    "-p", "--pdf_filename", help="Name of the PDF file to generate", default="test.pdf"
)
def main(debug, verbose, tweet_id, pdf_filename):
    if debug:
        pass
    if verbose:
        pass

    thread = Thread()
    tweet_content = thread.convert_to_post(tweet_id)

    pdf = PDF(orientation="P", unit="mm", format="A4")

    pdf.add_page()
    pdf.texts(tweet_content=tweet_content)
    pdf.output(pdf_filename, "F")


if __name__ == "__main__":
    main()
