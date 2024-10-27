from flask import Flask, request, jsonify, render_template
import requests
import os
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

app = Flask(__name__)

# Weather API (날씨 정보) 설정
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

# Naver Maps API 설정 (역 지오코딩용)
NAVER_MAP_CLIENT_ID = os.getenv('NAVER_MAP_CLIENT_ID')
NAVER_MAP_CLIENT_SECRET = os.getenv('NAVER_MAP_CLIENT_SECRET')

# Naver Search API 설정 (맛집 검색용)
NAVER_SEARCH_CLIENT_ID = os.getenv('NAVER_SEARCH_CLIENT_ID')
NAVER_SEARCH_CLIENT_SECRET = os.getenv('NAVER_SEARCH_CLIENT_SECRET')

# Deepl API (번역기) 설정
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")

# Deepl API를 사용한 번역 함수
def translate_text(text, target_lang='EN'):
    url = "https://api-free.deepl.com/v2/translate"
    headers = {
        "Authorization": f"DeepL-Auth-Key {DEEPL_API_KEY}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "text": text,
        "target_lang": target_lang
    }

    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        result = response.json()
        return result['translations'][0]['text']
    except requests.exceptions.RequestException as e:
        print(f"Error in translation: {e}")
        return None

# 주어진 위도와 경도를 기반으로 날씨 정보 가져오기
def get_weather_by_coords(lat, lon):
    url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={lat},{lon}&aqi=no"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data: {e}")
        return None

# Naver Maps API를 사용한 역 지오코딩 (위도, 경도를 지역명으로 변환)
def reverse_geocode(lat, lon):
    url = f'https://naveropenapi.apigw.ntruss.com/map-reversegeocode/v2/gc?coords={lon},{lat}&output=json&orders=legalcode'
    
    headers = {
        'X-NCP-APIGW-API-KEY-ID': NAVER_MAP_CLIENT_ID,
        'X-NCP-APIGW-API-KEY': NAVER_MAP_CLIENT_SECRET
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        if data['status']['code'] == 0:
            area_info = data['results'][0]['region']
            city = area_info['area1']['name']
            district = area_info['area2']['name']
            return f"{city}, {district}"
        else:
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching reverse geocoding data: {e}")
        return None

# Naver Search API를 사용한 맛집 검색
def search_places(location_name):
    query = f"{location_name} 맛집"
    display_count = 5
    url = f"https://openapi.naver.com/v1/search/local.json?query={query}&sort=random&display={display_count}"
    headers = {
        "X-Naver-Client-Id": NAVER_SEARCH_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_SEARCH_CLIENT_SECRET,
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json().get('items', [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching places data: {e}")
        return []

# 메인 페이지
@app.route('/')
def index():
    return render_template('index.html')

# 위도와 경도를 이용해 날씨 정보 및 맛집 정보를 가져오는 엔드포인트
@app.route('/get_weather_and_places', methods=['GET'])
def get_weather_and_places():
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    target_lang = request.args.get('target_lang', 'KO')

    if lat and lon:
        location_name = reverse_geocode(lat, lon)
        weather_data = get_weather_by_coords(lat, lon)
        if weather_data and 'current' in weather_data:
            temp = weather_data['current']['temp_c']
            weather_desc = weather_data['current']['condition']['text']
            translated_desc = translate_text(weather_desc, target_lang)
            translated_location = translate_text(location_name, target_lang)
            places_data = search_places(location_name)

            places_list = []
            for place in places_data:
                translated_name = translate_text(place['title'], target_lang)
                translated_address = translate_text(place['address'], target_lang)
                places_list.append({
                    'name': translated_name,
                    'address': translated_address,
                    'link': place['link']
                })

            final_message = f"The current temperature in {translated_location} is {temp}°C, and the weather is {translated_desc}."

            return jsonify({
                'message': final_message,
                'places': places_list
            })
        else:
            return jsonify({'message': "Failed to retrieve weather information."}), 400
    else:
        return jsonify({'message': "No location information provided."}), 400

if __name__ == '__main__':
    app.run(debug=True)
