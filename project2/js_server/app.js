import express from 'express';
import mongoose from 'mongoose';
import cors from 'cors';

const app = express();
const PORT = 8000;

app.use(cors());
app.use(express.json());

// 라우터 분리 및 실제 API 구현 예정
import apartmentRouter from './routes/apartment.js';
import subwayRouter from './routes/subway.js';
import bubjungdongRouter from './routes/bubjungdong.js';

app.use('/apartment', apartmentRouter);
app.use('/subway', subwayRouter);
app.use('/bubjungdong', bubjungdongRouter);

app.get('/', (req, res) => {
  res.send('Project2 JS Server is running!');
});

// MongoDB 연결 (secret.json에서 정보 읽기 예정)
const secret = await import('../secret.json', { assert: { type: 'json' } }).then(m => m.default).catch(() => null);

if (secret) {
  const mongoUri = `mongodb+srv://${secret.ATLAS_Username}:${secret.ATLAS_Password}@${secret.ATLAS_Hostname}/?retryWrites=true&w=majority`;
  mongoose.connect(mongoUri, { useNewUrlParser: true, useUnifiedTopology: true })
    .then(() => console.log('MongoDB connected'))
    .catch(err => console.error('MongoDB connection error:', err));
} else {
  console.warn('secret.json을 읽을 수 없습니다. MongoDB 연결이 비활성화됩니다.');
}

app.listen(PORT, () => {
  console.log(`JS API server running on http://localhost:${PORT}`);
});
