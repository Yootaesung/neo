import express from 'express';
const router = express.Router();

import Subway from '../models/Subway.js';

// GET /subway/getsubway?station=...
router.get('/getsubway', async (req, res) => {
  const { station } = req.query;
  if (!station) {
    return res.status(400).json({ result: false, message: 'station 쿼리 필요' });
  }
  try {
    // 역명/위치에 대해 대소문자 무시 정규식 검색
    const query = {
      $or: [
        { '역명': { $regex: station, $options: 'i' } },
        { '위치': { $regex: station, $options: 'i' } }
      ]
    };
    const docs = await Subway.find(query).lean();
    const results = docs.map(doc => ({
      stationName: doc['역명'],
      location: doc['위치'],
      openDate: doc['개통일'],
      bubjungdongCode: doc['법정동코드'] ? doc['법정동코드'].slice(0, 5) : null,
      stationRoadAddress: doc['역사도로명주소'] || ''
    }));
    return res.json({
      result: !!results.length,
      resultCount: results.length,
      results
    });
  } catch (err) {
    return res.status(500).json({ result: false, message: err.message });
  }
});

export default router;
