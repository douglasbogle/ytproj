import os
from dotenv import load_dotenv
import requests
import pprint
import pandas as pd
import sqlalchemy as db
import html

load_dotenv()
API_KEY = os.getenv('YOUTUBE_API_KEY')


# test cases with possible errors:
# channel_name = '1@!'
# NonexistentChannel
def channel(channel_name='Minecraft'):
    # If none entered or unittesting just use Minecraft channel
    PART_CHANNEL = 'contentDetails'
    USERNAME = channel_name

    params_channel = {
        'part': PART_CHANNEL,
        'forHandle': USERNAME,
        'key': API_KEY
    }
    CHANNEL_URL = 'https://www.googleapis.com/youtube/v3/channels'

    channel_info = requests.get(CHANNEL_URL, params=params_channel)
    channel_dict = channel_info.json()

    if 'items' not in channel_dict:
        return KeyError

    return channel_dict['items'][0]['id']  # should return channel's id


# test cases with possible errors:
# 'notID'
# None, None
def search(id=None, query=None):
    ORDER = 'viewCount'
    PART_POPULAR = 'snippet'
    TYPE = 'video'
    CHANNEL_ID = id
    Q = query

    params_search = {
        'part': PART_POPULAR,
        'order': ORDER,
        'maxResults': 20,
        'type': TYPE,
        'key': API_KEY,
    }

    if query:
        params_search['q'] = 'Q'
    if id:
        params_search['channelId'] = CHANNEL_ID

    SEARCH_URL = 'https://www.googleapis.com/youtube/v3/search'

    try:
        search_result = requests.get(SEARCH_URL, params=params_search)
    except Exception as e:  # Bad Request
        return None

    search_dict = search_result.json()

    if ('error' in search_dict):  # Bad Request
        return None

    return search_dict
    # should return a dict full of responses from youtubedata api search


# test cases with possible errors:
# []
# None
def populate_dict(info):
    if not isinstance(info, dict) or not info:
        return None

    if 'items' not in info:
        return KeyError

    sql_dict = {}

    for i in range(len(info['items'])):
        # make a dict mapping video titles to their info
        curr_dict = info['items'][i]
        sql_dict[html.unescape(curr_dict['snippet']['title'])] = \
            [curr_dict['id']['videoId'], curr_dict['snippet']['publishedAt']]
        # use this html method to avoid errors caused by accidental html chars

    return sql_dict
    # should return a dictionary mapping video titles to their info


# test cases with possible errors:
# []
# None
def videos(video_dict):
    if not isinstance(video_dict, dict) or not video_dict:
        return None

    ids = []
    for key in video_dict.keys():
        ids.append(video_dict[key][0])

    id_string = ','.join(ids)

    ID = id_string
    PART = 'snippet', 'statistics'

    params_videos = {
        'part': PART,
        'id': ID,
        'key': API_KEY
    }

    VIDEOS_URL = 'https://www.googleapis.com/youtube/v3/videos'

    video_stats = requests.get(VIDEOS_URL, params=params_videos)
    video_info = video_stats.json()

    for item in video_info['items']:
        curr_title = html.unescape(item['snippet']['title'])
        # use this html method to avoid errors caused by accidental html chars
        curr_views = item['statistics']['viewCount']

    if curr_title in video_dict:
        video_dict[curr_title].append(curr_views)
    else:
        raise Exception("Something bad happened")

    return video_dict
    # should add video view counts to already nicely formmated dict


def make_db(final_dict=None):
    if not final_dict:
        return None

    df = pd.DataFrame.from_dict(final_dict, orient='index')  # nice

    engine = db.create_engine('sqlite:///ytinfo.db')

    df.to_sql('final_dict', con=engine, if_exists='replace', index=False)

    with engine.connect() as connection:
        query_result = \
            connection.execute(db.text("SELECT * FROM final_dict;")).fetchall()
        print(pd.DataFrame(query_result))


channel_name = 'FryingPan'
# For now, specify channel name here, can unit test by making this wacky
id = channel(channel_name)
search_result = search(id)
formatted_dict = populate_dict(search_result)
final_dict = videos(formatted_dict)
make_db(final_dict)
