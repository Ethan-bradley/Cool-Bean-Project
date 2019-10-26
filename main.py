import datetime as dt
import csv
from guesser import *
from evaluate import *


def get_num_weeks_till(start, time):
    assert start <= time, 'start must be before time'
    count = 0
    while True:
        if time - start < dt.timedelta(weeks=1):
            return count
        start += dt.timedelta(weeks=1)
        count += 1


def get_next_week(start, time):
    assert start <= time, 'start must be before time'
    while True:
        if time - start < dt.timedelta(weeks=1):
            return start
        start += dt.timedelta(weeks=1)


class Tweet:
    def __init__(self, time):
        self.time = time

    def get_date(self):
        return self.time.date

    def get_time(self):
        return self.time.time


class Week:
    def __init__(self, start, tweets=None):
        if tweets is None:
            tweets = []
        self.start = start
        self.end = start + dt.timedelta(weeks=1)
        self.tweets = tweets

    def get_tweet(self, num):
        return self.tweets[num]

    def get_num_tweets(self):
        return len(self.tweets)

    def add_tweet(self, tweet):
        assert tweet.time - self.start < dt.timedelta(weeks=1) and self.end - tweet.time < dt.timedelta(
            weeks=1), 'tweet must be within week'
        for tweet_index in range(len(self.tweets) - 1, -1, -1):
            if tweet.time > self.tweets[tweet_index].time:
                self.tweets.insert(tweet_index + 1, tweet)
                return
        self.tweets.insert(0, tweet)

    def get_num_before(self, timedelta):
        n = 0
        for tweet in self.tweets:
            if tweet.time < self.start + timedelta:
                n += 1
        return n

    def get_num_after(self, timedelta):
        n = 0
        for tweet in self.tweets:
            if tweet.time >= self.start + timedelta:
                n += 1
        return n

    def get_daily_av(self, percentage=False):
        s = [0, 0, 0, 0, 0, 0, 0]
        for tweet in self.tweets:
            s[tweet.time.weekday()] += 1
        if percentage:
            for i in range(7):
                s[i] = s[i] / len(self.tweets)
        return s


class Weeks:
    def __init__(self, start, weeks=None):
        if weeks is None:
            weeks = []
        self.start = start
        self.weeks = weeks

    def get_week(self, num):
        return self.weeks[num]

    def get_num_weeks(self):
        return len(self.weeks)

    def add_week(self, week):
        assert self.start <= week.start, 'week must start after start time'
        if len(self.weeks) == 0:
            self.weeks.append(week)
        else:
            for week_index in range(len(self.weeks) - 1, -1, -1):
                if self.weeks[week_index].end == week.start:
                    self.weeks.insert(week_index + 1, week)
                    return
            assert False, 'could not add week'

    def add_tweet(self, tweet):
        assert self.start <= tweet.time, 'tweet time must be after start time'
        if len(self.weeks) == 0:
            self.add_week(Week(get_next_week(self.start, tweet.time), [tweet]))
            return
        for week_index in range(len(self.weeks) - 1, -1, -1):
            if tweet.time > self.weeks[week_index].start and tweet.time - self.weeks[week_index].start < dt.timedelta(
                    weeks=1):
                self.weeks[week_index].add_tweet(tweet)
                return
            elif tweet.time - self.weeks[week_index].start >= dt.timedelta(weeks=1):
                self.add_week(Week(get_next_week(self.weeks[week_index].start, tweet.time), [tweet]))
                return
        assert False, 'could not add tweet'

    def get_av_num_before(self, timedelta, num_weeks=-1, week=-1):
        n = 0
        if week == -1:
            week = len(self.weeks)
        if num_weeks == -1:
            num_weeks = len(self.weeks)
        for i in range(num_weeks):
            n += self.weeks[week - i - 1].get_num_before(timedelta)
        return n / num_weeks

    def get_av_num_after(self, timedelta, num_weeks=-1, week=-1):
        n = 0
        if week == -1:
            week = len(self.weeks)
        if num_weeks == -1:
            num_weeks = len(self.weeks)
        for i in range(num_weeks):
            n += self.weeks[week - i - 1].get_num_after(timedelta)
        return n / num_weeks

    def get_av_len_matching(self, timedelta, tweets, bounds=5, num_weeks=-1, week=-1):
        n = 0
        count = 0
        if week == -1:
            week = len(self.weeks)
        if num_weeks == -1:
            num_weeks = len(self.weeks)
        for i in range(num_weeks):
            before = self.weeks[week - i - 1].get_num_before(timedelta)
            error = tweets - before
            if abs(error) <= bounds:
                n, count = n + self.weeks[week - i - 1].get_num_tweets() + error, count + 1
        if count == 0:
            return tweets + self.get_av_num_after(timedelta, num_weeks, week)
        return n / count

    def get_daily_avs(self, num_weeks=-1, week=-1):
        s = [0, 0, 0, 0, 0, 0, 0]
        if week == -1:
            week = len(self.weeks)
        if num_weeks == -1:
            num_weeks = len(self.weeks)
        for week in self.weeks:
            split = week.get_daily_av()
            for i in range(7):
                s[i] += split[i]
        for i in range(7):
            s[i] = s[i] / num_weeks
        return s

    def get_week_of_tweet(self, tweet):
        return get_num_weeks_till(self.start, tweet.time)

    def weeks_to_csv(self):
        with open('data.csv', mode='w') as csv_file:
            tweet_writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            tweet_writer.writerow(['Days', 'Hours', 'Time', 'tweets', 'total'])

            for week in self.weeks:
                for tweet in week.tweets:
                    days = (tweet.time - self.start).days
                    hours = round((tweet.time - week.start).seconds/3600, 3)
                    time = round((week.end - tweet.time).seconds/3600, 3)
                    tweets = week.get_num_before(tweet.time - week.start)
                    total = week.get_num_tweets()
                    tweet_writer.writerow([days, hours, time, tweets, total])


def csv_to_weeks(file, start):
    new_weeks = Weeks(start)
    with open(file, encoding='utf8') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        lst = reversed(list(csv_reader))
        for row in lst:
            if row[2] != 'created_at':
                time = row[2]
                time = dt.datetime.strptime(time, '%m-%d-%Y %H:%M:%S')
                if time >= start:
                    new_weeks.add_tweet(Tweet(time))
    return new_weeks


everything = csv_to_weeks('realDonaldTrump.csv', dt.datetime(2018, 1, 3, 12))
everything.weeks_to_csv()
