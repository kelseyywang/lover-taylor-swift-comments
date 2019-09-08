import argparse
import json

from urllib.parse import urlparse, urlencode, parse_qs
from urllib.request import urlopen

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


YT_COMMENT_URL = 'https://www.googleapis.com/youtube/v3/commentThreads'

SONG_URLS = {
    'me': 'https://www.youtube.com/watch?v=ZBFZHOyFMO4',
    'lover': 'https://www.youtube.com/watch?v=YdbUUJy7T9M',
    'the archer': 'https://www.youtube.com/watch?v=coR_6sAOugY',
    'you need': 'https://www.youtube.com/watch?v=1wgr1Bjxs7E',
    'the man': 'https://www.youtube.com/watch?v=pHoHDNxay3A',
    'daylight': 'https://www.youtube.com/watch?v=u9raS7-NisU',
    'i forgot': 'https://www.youtube.com/watch?v=p1cEvNn88jM',
    'cruel summer': 'https://www.youtube.com/watch?v=ic8j13piAhQ',
    'its nice': 'https://www.youtube.com/watch?v=eaP1VswBF28',
    'soon youll': 'https://www.youtube.com/watch?v=tMoW5G5LU08',
    'miss americana': 'https://www.youtube.com/watch?v=Kwf7P2GNAVw',
    'death by': 'https://www.youtube.com/watch?v=GTEFSuFfgnU',
    'london boy': 'https://www.youtube.com/watch?v=VsKoOH6DVys',
    'cornelia street': 'https://www.youtube.com/watch?v=VikHHWrgb4Y',
    'paper rings': 'https://www.youtube.com/watch?v=8zdg-pDF10g',
    'false god': 'https://www.youtube.com/watch?v=acQXa5ArHIk',
    'i think': 'https://www.youtube.com/watch?v=2d1wKn-oJnA',
    'afterglow': 'https://www.youtube.com/watch?v=8HxbqAsppwU',
}


def get_comments_info(yt_url):
    # Referencing https://github.com/srcecde/python-youtube-api
    def load_comments():
        comments_arr = []
        for item in mat['items']:
            comment = item['snippet']['topLevelComment']
            text = comment['snippet']['textDisplay']
            likes = comment['snippet']['likeCount']
            comments_arr.append((text, likes))
        return comments_arr

    def open_url(url, params):
        f = urlopen(url + '?' + urlencode(params))
        data = f.read()
        f.close()
        matches = data.decode('utf-8')
        return matches

    parser = argparse.ArgumentParser()
    parser.add_argument('--key', help='Required API key')
    args = parser.parse_args()
    if not args.key:
        exit('Please specify API key using the --key=parameter.')

    video_id = urlparse(str(yt_url))
    q = parse_qs(video_id.query)
    vid = q['v'][0]

    params = {
        'part': 'snippet,replies',
        'videoId': vid,
        'key': args.key
    }
    all_comments_info = []
    matches = open_url(YT_COMMENT_URL, params)
    mat = json.loads(matches)
    next_pg_token = mat.get('nextPageToken')
    this_pg_comments = load_comments()
    all_comments_info.extend(this_pg_comments)
    while next_pg_token:
        params.update({'pageToken': next_pg_token})
        matches = open_url(YT_COMMENT_URL, params)
        mat = json.loads(matches)
        next_pg_token = mat.get('nextPageToken')
        this_pg_comments = load_comments()
        all_comments_info.extend(this_pg_comments)
    return all_comments_info


def write_comments(all_comments_info, file_name):
    f = open(file_name, 'w+')
    for comment_info in all_comments_info:
        # Write out comment and number of likes
        f.write(comment_info[0] + '\n' + str(comment_info[1]) + '\n')
    f.close()


def get_average_sentiment(comment_file):
    def is_int(s):
        try:
            int(s)
            return True
        except ValueError:
            return False

    with open(comment_file) as f:
        # Using VADER: https://github.com/cjhutto/vaderSentiment
        analyzer = SentimentIntensityAnalyzer()
        total_comments_and_likes, final_score = 0, 0
        while True:
            line = f.readline()
            likes_str = f.readline()
            if len(line) == 0 or len(likes_str) == 0:
                # EOF
                break
            while likes_str and not is_int(likes_str):
                # likes_str is actually a continuation of prev line
                line += likes_str
                likes_str = f.readline()
            likes = int(likes_str)
            compound_score = analyzer.polarity_scores(line)['compound']
            # Comments' sentiment ave weighted by number of likes
            final_score += (likes + 1) * compound_score
            total_comments_and_likes += 1 + likes
    return final_score / total_comments_and_likes


if __name__ == '__main__':
    for title, song_url in SONG_URLS.items():
        song_file = title.replace(' ', '_') + '.txt'
        write_comments(get_comments_info(song_url), song_file)
        ave_sentiment = get_average_sentiment(song_file)
        print('Song:', title)
        print('Average weighted comment sentiment:', ave_sentiment)
        print('Comments saved to', song_file)
