import mongoose from 'mongoose';

const ApartmentSchema = new mongoose.Schema({
  // 필요한 필드만 우선 정의, 실제 데이터에 따라 확장 가능
  '아파트': String,
  '법정동코드': String,
  '거래금액': String,
  '거래일': String,
  '면적': String,
  '층': String,
  '도로명': String,
  '지번': String,
  '건축년도': String,
  // ... 기타 필요 필드
}, { collection: 'apartment' });

export default mongoose.model('Apartment', ApartmentSchema);
