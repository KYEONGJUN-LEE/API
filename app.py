from flask import Flask, request, jsonify, render_template
import requests
import json

app = Flask(__name__)

# Visual Crossing API (날씨 정보) 설정
WEATHER_API_KEY = "TT2VK9WRWEVT4GZUG2ACRN6C3"

# Naver Maps API 설정 (역 지오코딩용)
NAVER_MAP_CLIENT_ID = '5pck85z8lr'
NAVER_MAP_CLIENT_SECRET = 'AJk2NurOPa6ZJXvo4yqSoz5Hfkkw1g5bFblFFlaL'

# Naver Search API 설정 (맛집 검색용)
NAVER_SEARCH_CLIENT_ID = 'ipKgAgvbu0LcGlgtzlTA'
NAVER_SEARCH_CLIENT_SECRET = 'VU1rb5jKvG'

# Deepl API (번역기) 설정
DEEPL_API_KEY = "8f12594d-97b1-4d51-8ed9-1488697dbd3d:fx"

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

# Visual Crossing API를 사용한 날씨 정보 가져오기 (위도, 경도 기준)
def get_weather_by_coords(lat, lon):
    url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{lat},{lon}?key={WEATHER_API_KEY}&unitGroup=metric"
    
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
        response.raise_for_status()  # HTTP 오류 발생 시 예외 발생
        data = response.json()
        if data['status']['code'] == 0:
            area_info = data['results'][0]['region']
            city = area_info['area1']['name']  # 시/도
            district = area_info['area2']['name']  # 구/군
            return f"{city}, {district}"
        else:
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching reverse geocoding data: {e}")
        return None

# Naver Search API를 사용한 맛집 검색
def search_places(location_name):
    query = f"{location_name} 맛집"  # 지역명을 기반으로 검색
    display_count = 5  # 가져올 맛집 개수
    url = f"https://openapi.naver.com/v1/search/local.json?query={query}&sort=random&display={display_count}"  # 랜덤 정렬 및 표시 개수 설정
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
    target_lang = request.args.get('target_lang', 'KO')  # 기본 언어는 한글

    if lat and lon:
        # 위도와 경도를 기반으로 지역명 가져오기
        location_name = reverse_geocode(lat, lon)

        # 날씨 데이터 가져오기
        weather_data = get_weather_by_coords(lat, lon)
        if weather_data and 'days' in weather_data:
            temp = weather_data['days'][0]['temp']
            weather_desc = weather_data['days'][0]['description']

            # 모든 출력값을 선택한 언어로 번역
            translated_desc = translate_text(weather_desc, target_lang)
            translated_location = translate_text(location_name, target_lang)

            # 맛집 정보 가져오기
            places_data = search_places(location_name)

            places_list = []
            for place in places_data:
                translated_name = translate_text(place['title'], target_lang)  # 맛집 이름 번역
                translated_address = translate_text(place['address'], target_lang)  # 맛집 주소 번역
                places_list.append({
                    'name': translated_name,
                    'address': translated_address,
                    'link': place['link']
                })

            # 사용자 언어에 맞게 최종 메시지 번역
            if target_lang == 'KO':
                final_message = f"{translated_location}의 현재 온도는 {temp}°C이며, 날씨는 {translated_desc if translated_desc else weather_desc}."
            elif target_lang == 'EN':
                final_message = f"The current temperature in {translated_location} is {temp}°C, and the weather is {translated_desc if translated_desc else weather_desc}."
            elif target_lang == 'ZH':
                final_message = f"{translated_location}的当前温度是{temp}°C，天气是{translated_desc if translated_desc else weather_desc}。"
            elif target_lang == 'JA':
                final_message = f"{translated_location}の現在の気温は{temp}°Cで、天気は{translated_desc if translated_desc else weather_desc}です。"
            elif target_lang == 'RU':
                final_message = f"Температура в {translated_location} сейчас {temp}°C, а погода {translated_desc if translated_desc else weather_desc}."
            else:
                # 기본 언어 설정 (예: 한국어)
                final_message = f"{translated_location}의` 현재 온도는 {temp}°C이며, 날씨는 {translated_desc if translated_desc else weather_desc}."

            return jsonify({
                'message': final_message,
                'places': places_list
            })
        else:
            return jsonify({'message': "날씨 정보를 가져오는 데 실패했습니다."}), 400
    else:
        return jsonify({'message': "위치 정보가 없습니다."}), 400

if __name__ == '__main__':
    app.run(debug=True)
