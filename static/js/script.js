let map;
let marker; // 핀을 저장할 변수

function initMap() {
    // 지도 초기화 (서울 중심)
    map = new naver.maps.Map('map', {
        center: new naver.maps.LatLng(37.5665, 126.978), // 서울의 위도, 경도
        zoom: 10, // 확대 수준
    });

    // 지도 클릭 이벤트 추가
    naver.maps.Event.addListener(map, 'click', function(e) {
        const lat = e.latlng.y; // 클릭한 위치의 위도
        const lon = e.latlng.x; // 클릭한 위치의 경도
        const targetLang = document.getElementById("target_lang").value; // 선택된 언어 가져오기

        // 핀 찍기
        placeMarker(e.latlng);

        // 좌표를 서버로 전송하여 날씨 정보 요청
        fetchWeather(lat, lon, targetLang);
    });
}

// 핀을 지도에 표시하는 함수
function placeMarker(latlng) {
    if (marker) {
        marker.setMap(null); // 기존 핀 제거
    }
    marker = new naver.maps.Marker({
        position: latlng, // 클릭한 위치
        map: map // 지도에 추가
    });
}

// 날씨 정보를 요청하는 함수
function fetchWeather(lat, lon, targetLang) {
    fetch(`/get_weather_and_places?lat=${lat}&lon=${lon}&target_lang=${targetLang}`)
        .then(response => response.json())
        .then(data => {
            // 날씨 정보를 지도 아래에 표시
            document.getElementById('weather-info').innerText = data.message;

            // 맛집 정보를 표시
            if (data.places && data.places.length > 0) {
                let placesHeader;

                // 선택한 언어에 따라 맛집 제목 변경
                switch (targetLang) {
                    case 'KO':
                        placesHeader = "지역별 맛집"; // 한국어
                        break;
                    case 'EN':
                        placesHeader = "Delicious Restaurants"; // 영어
                        break;
                    case 'ZH':
                        placesHeader = "美味的餐厅"; // 중국어
                        break;
                    case 'JA':
                        placesHeader = "美味しいレストラン"; // 일본어
                        break;
                    case 'RU':
                        placesHeader = "Вкусные рестораны"; // 러시아어
                        break;
                    default:
                        placesHeader = "지역별 맛집"; // 기본값 (한국어)
                }

                let placesList = `<h3>${placesHeader}</h3><ul>`;
                data.places.forEach(place => {
                    placesList += `<li><strong><a href="${place.link}" target="_blank">${place.name}</a></strong> - ${place.address}</li>`;
                });
                placesList += "</ul>";
                document.getElementById('weather-info').innerHTML += placesList; // 맛집 정보 추가
            } else {
                document.getElementById('weather-info').innerText += "\n맛집 정보를 가져오는 데 실패했습니다.";
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
}


window.onload = initMap;
