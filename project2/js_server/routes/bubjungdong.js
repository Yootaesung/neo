import express from 'express';
const router = express.Router();

import mongoose from 'mongoose';
const BubjungdongSchema = new mongoose.Schema({
  '법정동코드': String,
  '법정동명': String,
  '폐지여부': String
}, { collection: 'bubjungdong' });
const Bubjungdong = mongoose.models.Bubjungdong || mongoose.model('Bubjungdong', BubjungdongSchema);

// GET /bubjungdong/getbubjungdongcode?location=...
router.get('/getbubjungdongcode', async (req, res) => {
  const { location } = req.query;
  if (!location) {
    return res.status(400).json({ result: false, message: 'location 쿼리 필요' });
  }
  try {
    // 부분일치(정규식) + 폐지여부: 존재
    const items = await Bubjungdong.find({
      '법정동명': { $regex: `^${location}`, $options: 'i' },
      '폐지여부': '존재'
    }, { '법정동코드': 1, '법정동명': 1, '폐지여부': 1, _id: 0 }).lean();
    if (!items.length) {
      return res.json({ result: false, message: '법정동명을 찾을 수 없습니다.' });
    }
    const item = items[0];
    return res.json({
      result: true,
      bubjungdongCode: String(item['법정동코드']).slice(0, 5),
      bubjungdongName: item['법정동명']
    });
  } catch (err) {
    return res.status(500).json({ result: false, message: err.message });
  }
});

export default router;
