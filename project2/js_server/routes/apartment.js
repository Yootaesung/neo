import express from 'express';
const router = express.Router();

import Subway from '../models/Subway.js';
import Apartment from '../models/Apartment.js';

// GET /apartment/getapartment?station=...&openDate=...
router.get('/getapartment', async (req, res) => {
  const { station, openDate } = req.query;
  if (!station || !openDate) {
    return res.status(400).json({ result: false, message: 'station, openDate 쿼리 필요' });
  }
  try {
    // 1. subway DB에서 역명으로 위치(행정구역명) 조회
    const subwayDoc = await Subway.findOne({ '역명': station });
    if (!subwayDoc) {
      return res.status(404).json({ result: false, message: '지하철역 정보를 찾을 수 없습니다.' });
    }
    const location = subwayDoc['위치'];
    // 2. 법정동코드 조회
    const lawdCode = subwayDoc['법정동코드'] ? subwayDoc['법정동코드'].slice(0, 5) : null;
    if (!lawdCode) {
      return res.status(404).json({ result: false, message: '법정동코드가 없습니다.' });
    }
    // 3. openDate 기준 ±3년 범위 계산
    const open = openDate.match(/^(\d{4})(\d{2})(\d{2})$/);
    if (!open) {
      return res.status(400).json({ result: false, message: 'openDate 형식 오류(YYYYMMDD)' });
    }
    const openYear = parseInt(open[1], 10);
    const openMonth = parseInt(open[2], 10);
    const start = new Date(openYear - 3, openMonth - 1, 1);
    const end = new Date(openYear + 3, openMonth - 1, 1);
    // 4. 거래 데이터 조회 (아파트 컬렉션)
    const deals = await Apartment.find({
      '법정동코드': { $regex: `^${lawdCode}` },
      '거래일': { $gte: start.toISOString().slice(0, 10).replace(/-/g, ''), $lte: end.toISOString().slice(0, 10).replace(/-/g, '') }
    }).lean();
    return res.json({
      result: true,
      resultCount: deals.length,
      results: deals
    });
  } catch (err) {
    return res.status(500).json({ result: false, message: err.message });
  }
});

// GET /apartment/getapartment_by_code?bubjungdongCode=...&openDate=...
router.get('/getapartment_by_code', async (req, res) => {
  const { bubjungdongCode, openDate } = req.query;
  if (!bubjungdongCode || !openDate) {
    return res.status(400).json({ result: false, message: 'bubjungdongCode, openDate 쿼리 필요' });
  }
  try {
    // openDate 기준 ±3년 범위 계산
    const open = openDate.match(/^(\d{4})(\d{2})(\d{2})$/);
    if (!open) {
      return res.status(400).json({ result: false, message: 'openDate 형식 오류(YYYYMMDD)' });
    }
    const openYear = parseInt(open[1], 10);
    const openMonth = parseInt(open[2], 10);
    const start = new Date(openYear - 3, openMonth - 1, 1);
    const end = new Date(openYear + 3, openMonth - 1, 1);
    // 거래 데이터 조회 (법정동코드 앞 5자리, 날짜 범위)
    const deals = await Apartment.find({
      '법정동코드': { $regex: `^${bubjungdongCode}` },
      '거래일': { $gte: start.toISOString().slice(0, 10).replace(/-/g, ''), $lte: end.toISOString().slice(0, 10).replace(/-/g, '') }
    }).lean();
    return res.json({
      result: true,
      resultCount: deals.length,
      results: deals
    });
  } catch (err) {
    return res.status(500).json({ result: false, message: err.message });
  }
});

// GET /apartment/current_df
let currentApartmentDf = null;
router.get('/current_df', (req, res) => {
  if (currentApartmentDf) {
    return res.json({ result: true, count: currentApartmentDf.length, data: currentApartmentDf });
  }
  return res.json({ result: false, message: 'No data loaded' });
});

export default router;
