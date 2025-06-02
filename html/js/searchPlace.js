require('dotenv').config();
const axios = require('axios');

// 검색할 키워드와 위치 정보 입력
const searchKeyword = async (keyword, x = null, y = null, radius = null) => {
  try {
    const url = 'https://dapi.kakao.com/v2/local/search/keyword.json';

    const response = await axios.get(url, {
      headers: {
        Authorization: `KakaoAK ${process.env.KAKAO_API_KEY}`,
      },
      params: {
        query: keyword,
        ...(x && { x }),
        ...(y && { y }),
        ...(radius && { radius }), // 반경 (단위: 미터)
        size: 5, // 최대 5개만
      },
    });

    const places = response.data.documents;

    if (places.length === 0) {
      console.log("검색 결과가 없습니다.");
      return;
    }

    places.forEach((place, index) => {
      console.log(`\n[${index + 1}] ${place.place_name}`);
      console.log(`주소: ${place.address_name}`);
      console.log(`전화번호: ${place.phone}`);
      console.log(`URL: ${place.place_url}`);
      console.log(`거리: ${place.distance}m`);
    });
  } catch (error) {
    console.error("에러 발생:", error.response ? error.response.data : error.message);
  }
};