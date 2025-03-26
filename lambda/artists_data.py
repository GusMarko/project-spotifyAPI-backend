import boto3
import requests
import json
import os
import base64

dynamodb = boto3.resource("dynamodb")
table_name = os.environ.get("DYNAMODB_TABLE_NAME")
table = dynamodb.Table(table_name)


def lambda_handler(event, context):

    print("Connected to table: ", table)

    SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
    SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")

    print("Environment variables imported")

    # query artist name and data type from event
    artist_name = event['queryStringParameters'].get('artist', '').lower()
    print(f"Artist name : {artist_name}")
    data_type = event['queryStringParameters'].get('type', '')
    print(f"Data Type : {data_type}")


    # check if data is already in dynamodb 
    data = check_dynamodb(artist_name, data_type)
    if data:
          print("Data found in database")
          return build_response(200, {"artist": artist_name, "type": data_type, "data": data})
    elif data == None:
        print("Database doesn't contain data, continue process.")

    # generate spotify token for api calls
    print("Started fetching api token...")
    token = get_spotify_token(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
    if not token:
        return build_response(500, {"error": "Failed to retrieve Spotify token."})

    
    # send request to spotify depending on data type
    data = get_data_from_spotify(artist_name, data_type, token)
    if data:
        print("Spotify data collected")
        # store response in database
        store_data_in_dynamodb(artist_name, data_type, data)
        print(data)
        print(json.dumps(data))
        print("Data Stored")
        return build_response(200, {"artist": artist_name, "type": data_type, "data": data})
    else:
        return build_response(404, {"error": "No data found for the given artist"})


    
def check_dynamodb(artist, option):
    response = table.get_item(
        Key={'artistName': artist, 'dataType': option}
    )
    if 'Item' in response:
        data = response['Item'].get('data')
        return json.loads(data)
    else:
        return None
 
def get_spotify_token(id, secret):
    url = 'https://accounts.spotify.com/api/token'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {'grant_type': 'client_credentials'}
    response = requests.post(
        url, headers=headers, data=data, auth=(id, secret)
    )
    response_data = response.json()
    print(response_data)
    return response_data.get('access_token')



def get_data_from_spotify(artist, option, token):

     base_url = "https://api.spotify.com/v1"
     headers = {"Authorization": f"Bearer {token}"}

     search_url = f"{base_url}/search"
     params = {"q": artist, "type": "artist"}
     search_response = requests.get(search_url, headers=headers,params=params)
     search_data = search_response.json()
     artist_id = search_data['artists']['items'][0]['id']
     print(f"Artist Name : {artist}, Artist id : {artist_id}")
     print(f"Search Option: {option}")

     if option == 'bestSong':
          print(f"Retrieving best song by {artist} ...")
          return get_bestSong(base_url, artist_id, headers, artist)
     elif option == 'topSongs':
          print(f"Retrieving top tracks by {artist} ...")
          return get_topSongs(base_url,artist_id, headers, artist)
     elif option == 'latestAlbum':
          print(f"Retrieving latest album by {artist} ...")
          return get_latestAlbum(base_url, artist_id, headers, artist)



def get_bestSong(base_url, artist_id, headers, artist):

     url = f"{base_url}/artists/{artist_id}/top-tracks"
     params = {"market": "US"}
     response = requests.get(url, headers=headers, params=params)
     tracks = response.json().get('tracks', [])
     if tracks:
          print(f"Best song by {artist}: {tracks[0]['name']}")
          return tracks [0]["name"]
     else:
          None


def get_topSongs(base_url, artist_id, headers, artist):

     url = f"{base_url}/artists/{artist_id}/top-tracks"
     params = {"market": "US"}
     response = requests.get(url, headers=headers, params=params)
     songs =  response.json().get('tracks', [])[:5]
     track_names = [song["name"] for song in songs]
     print(f"Top songs by {artist}: {track_names}")
     return track_names


def get_latestAlbum(base_url, artist_id, headers, artist):
    url = f"{base_url}/artists/{artist_id}/albums"
    params = {"include_groups": "album", "limit": 1}
    response = requests.get(url, headers=headers, params=params)
    albums = response.json().get('items', [])
    if albums:
        print(f"Latest album by {artist}: {albums[0]['name']}")
        return albums[0]["name"]
    else:
        None


def store_data_in_dynamodb(artist, option, data):
    print("Before storing in DB:", data, type(data))
    data = json.dumps(data)
    table.put_item(
        Item={
            'artistName': artist,
            'dataType': option,
            'data': data
        }
    )


def build_response(status, body):
     return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            'Access-Control-Allow-Headers': "Content-Type",
            "Access-Control-Allow-Origin": "*",
            'Access-Control-Allow-Methods': "GET,OPTIONS"
        },
        "body": json.dumps(body)
    }


