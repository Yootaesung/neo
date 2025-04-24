import mongoose from 'mongoose';

const SubwaySchema = new mongoose.Schema({
  '역명': String,
  '위치': String,
  '개통일': String,
  '법정동코드': String,
  '역사도로명주소': String
}, { collection: 'subway' });

export default mongoose.model('Subway', SubwaySchema);
