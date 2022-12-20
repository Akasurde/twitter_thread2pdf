import click
import tweepy
from os.path import join, expanduser
from configparser import ConfigParser
from datetime import datetime


configuration = ConfigParser()
configuration.read(join(expanduser("~"), ".twitter_api"))

CONSUMER_KEY = configuration.get("defaults", "CONSUMER_KEY")
CONSUMER_SECRET = configuration.get("defaults", "CONSUMER_SECRET")
ACCESS_TOKEN = configuration.get("defaults", "ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = configuration.get("defaults", "ACCESS_TOKEN_SECRET")


@click.command()
@click.option("-d", "--debug", help="Debug", is_flag=True, default=False)
@click.option("-v", "--verbose", help="Verbose", is_flag=True, default=False)
@click.option("-t", "--tweet_id", help="Thread ID to download e.g. '1602656208346832899'")
@click.option(
    "-f", "--filename", help="Name of the text file to generate", default="test.txt"
)
def main(debug, verbose, tweet_id, filename):
    if filename == "test.txt":
        tday = datetime.today()
        filename = "tweet_thread_%s_%s.txt" % (tweet_id, datetime.strftime(tday, '%d%m%Y'))
    client = TweetToTxt(debug, verbose, filename)
    allTweets = client.getAllTweetsInThread(tweet_id)
    client.printAllTweet(allTweets)


class TweetToTxt:
    def __init__(self, debug, verbose, filename):
        auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
        auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

        self.api = tweepy.API(auth)
        self.filename = filename
        self.debug = debug
        self.verbose = verbose

    def get_all_tweets(self, tweet):
        screen_name = tweet.user.screen_name
        lastTweetId = tweet.id
        # initialize a list to hold all the tweepy Tweets
        allTweets = []
        # make initial request for most recent tweets (200 is the maximum allowed count)
        new_tweets = self.api.user_timeline(screen_name=screen_name, count=200)
        allTweets.extend(new_tweets)
        # save the id of the oldest tweet less one
        oldest = allTweets[-1].id - 1
        # keep grabbing tweets until there are no tweets left to grab
        while len(new_tweets) > 0 and oldest >= lastTweetId:
            print(f"getting tweets before {oldest}")
            # all subsiquent requests use the max_id param to prevent duplicates
            new_tweets = self.api.user_timeline(
                screen_name=screen_name, count=200, max_id=oldest
            )
            # save most recent tweets
            allTweets.extend(new_tweets)
            # update the id of the oldest tweet less one
            oldest = allTweets[-1].id - 1
            print(f"...{len(allTweets)} tweets downloaded so far")
        outtweets = [tweet.id for tweet in allTweets]
        return outtweets

    def getAllTweetsInThreadAfterThis(self, tweetId):
        thread = []
        res = self.api.get_status(tweetId, tweet_mode="extended")
        allTillThread = self.get_all_tweets(res)
        thread.append(res)
        if allTillThread[-1] > res.id:
            print("Not able to retrieve so older tweets")
            return thread
        print("downloaded required tweets")
        startIndex = allTillThread.index(res.id)
        print("Finding useful tweets")
        quietLong = 0
        while startIndex != 0 and quietLong < 25:
            nowIndex = startIndex - 1
            nowTweet = self.api.get_status(
                allTillThread[nowIndex], tweet_mode="extended"
            )
            if nowTweet.in_reply_to_status_id == thread[-1].id:
                quietLong = 0
                # print("Reached a useful tweet to be included in thread")
                thread.append(nowTweet)
            else:
                quietLong = quietLong + 1
            startIndex = nowIndex
        return thread

    def getAllTweetsInThreadBeforeThis(self, tweetId):
        thread = []
        res = self.api.get_status(tweetId, tweet_mode="extended")
        while res.in_reply_to_status_id is not None:
            res = self.api.get_status(res.in_reply_to_status_id, tweet_mode="extended")
            thread.append(res)
        return thread[::-1]

    def getAllTweetsInThread(self, tweetId):
        tweetsAll = []
        tweetsAll = self.getAllTweetsInThreadBeforeThis(tweetId)
        if self.verbose:
            print("Getting all tweets before this tweet")
            print(len(tweetsAll))
        print("Getting all tweets after this tweet")
        tweetsAll.extend(self.getAllTweetsInThreadAfterThis(tweetId))
        return tweetsAll

    def printAllTweet(self, tweets):
        fd = open(self.filename, "w")
        if len(tweets) > 0:
            for tweetId in range(len(tweets)):
                fd.write(str(tweetId + 1) + ". " + tweets[tweetId].full_text)
                fd.write("")
        else:
            print("No Tweet to print")
        print("Done writing to %s" % self.filename)
        fd.close()


if __name__ == "__main__":
    main()
