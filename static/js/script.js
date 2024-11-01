let map;
let marker; // 핀을 저장할 변수
let watchId; // 위치 추적 ID
let currentLat, currentLon; // 현재 위도와 경도 저장 변수
let isTracking = true; // 실시간 위치 추적 상태 변수

// 지도 초기화
function initMap() {
    map = new naver.maps.Map('map', {
        center: new naver.maps.LatLng(37.5665, 126.978), // 서울의 위도, 경도
        zoom: 10, // 확대 수준
    });

    const defaultLang = "KO";
    updateLanguage(defaultLang);

    // 지도 클릭 이벤트 추가
    naver.maps.Event.addListener(map, 'click', function(e) {
        const lat = e.latlng.y;
        const lon = e.latlng.x;
        const targetLang = document.getElementById("target_lang").value;

        // 실시간 위치 추적 중지
        if (isTracking) {
            stopTracking(); // 실시간 위치 추적 중지
            isTracking = false; // 추적 상태 업데이트
        }

        placeMarker(e.latlng);
        fetchWeather(lat, lon, targetLang);
    });

    document.getElementById("target_lang").addEventListener("change", function() {
        const targetLang = this.value;
        updateLanguage(targetLang);
        if (currentLat && currentLon) {
            fetchWeather(currentLat, currentLon, targetLang);
        }
    });

    askForLocation();
}

// 사용자에게 위치 사용 여부를 묻는 함수
function askForLocation() {
    if (confirm("현재 위치를 사용하시겠습니까?")) {
        startTracking();
    }
}

// 위치 추적 시작 함수
function startTracking() {
    if (navigator.geolocation) {
        watchId = navigator.geolocation.watchPosition(
            (position) => {
                if (!isTracking) return; // 위치 추적이 비활성화된 경우 중지
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;

                const currentLocation = new naver.maps.LatLng(lat, lon);
                map.setCenter(currentLocation);
                placeMarker(currentLocation);

                const targetLang = document.getElementById("target_lang").value;
                fetchWeather(lat, lon, targetLang);
            },
            (error) => {
                console.error("Error getting location: ", error);
            },
            {
                enableHighAccuracy: true,
                maximumAge: 10000,
                timeout: 5000,
            }
        );
    } else {
        console.log("Geolocation is not supported by this browser.");
    }
}

// 위치 추적 중지 함수
function stopTracking() {
    if (watchId) {
        navigator.geolocation.clearWatch(watchId);
        watchId = null;
    }
}

// 언어에 따라 제목과 라벨을 업데이트하는 함수
function updateLanguage(targetLang) {
    const h1 = document.querySelector('h1');
    const langLabel = document.querySelector('label[for="target_lang"]');

    switch (targetLang) {
        case 'KO':
            h1.innerText = "지역 기반 날씨 및 추천 서비스";
            langLabel.innerText = "언어:";
            break;
        case 'EN':
            h1.innerText = "Regional Weather and Recommendation Service";
            langLabel.innerText = "Language:";
            break;
        case 'JA':
            h1.innerText = "地域の天気とおすすめサービス";
            langLabel.innerText = "言語:";
            break;
        case 'ZH':
            h1.innerText = "地区天气与推荐服务";
            langLabel.innerText = "语言:";
            break;
        case 'RU':
            h1.innerText = "Региональная служба погоды и рекомендаций";
            langLabel.innerText = "Язык:";
            break;
        default:
            h1.innerText = "Regional Weather and Recommendation Service";
            langLabel.innerText = "Language:";
    }
}

// 핀을 지도에 표시하는 함수
function placeMarker(latlng) {
    if (marker) {
        marker.setMap(null); // 기존 핀 제거
    }
    marker = new naver.maps.Marker({
        position: latlng,
        map: map,
    });
}

function fetchWeather(lat, lon, targetLang) {
    currentLat = lat;
    currentLon = lon;

    fetch(`/get_weather_and_places?lat=${lat}&lon=${lon}&target_lang=${targetLang}`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('weather-info').innerText = data.message;

            if (data.attractions && data.attractions.length > 0) {
                let attractionsHeader;
                switch (targetLang) {
                    case 'KO':
                        attractionsHeader = "가볼만한 곳";
                        break;
                    case 'EN':
                        attractionsHeader = "Recommended Attractions";
                        break;
                    case 'ZH':
                        attractionsHeader = "推荐景点";
                        break;
                    case 'JA':
                        attractionsHeader = "おすすめの観光地";
                        break;
                    case 'RU':
                        attractionsHeader = "Рекомендуемые достопримечательности";
                        break;
                    default:
                        attractionsHeader = "가볼만한 곳";
                }

                let attractionsList = `<h3>${attractionsHeader}</h3><ul>`;
                data.attractions.forEach(attraction => {
                    attractionsList += `<li><strong><a href="${attraction.link}" target="_blank">${attraction.name}</a></strong> - ${attraction.address}</li>`;
                });
                attractionsList += "</ul>";
                document.getElementById('weather-info').innerHTML += attractionsList;
            } else {
                document.getElementById('weather-info').innerText += "\n명소 정보를 가져오는 데 실패했습니다.";
            }

            if (data.places && data.places.length > 0) {
                let placesHeader;
                switch (targetLang) {
                    case 'KO':
                        placesHeader = "근처 맛집";
                        break;
                    case 'EN':
                        placesHeader = "Nearby Restaurants";
                        break;
                    case 'ZH':
                        placesHeader = "附近的餐厅";
                        break;
                    case 'JA':
                        placesHeader = "近くのレストラン";
                        break;
                    case 'RU':
                        placesHeader = "Ближайшие рестораны";
                        break;
                    default:
                        placesHeader = "근처 맛집";
                }
                let placesList = `<h3>${placesHeader}</h3><ul>`;
                data.places.forEach(place => {
                    placesList += `<li><strong><a href="${place.link}" target="_blank">${place.name}</a></strong> - ${place.address}</li>`;
                });
                placesList += "</ul>";
                document.getElementById('weather-info').innerHTML += placesList;
            } else {
                document.getElementById('weather-info').innerText += "\n맛집 정보를 가져오는 데 실패했습니다.";
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

window.onload = initMap;
