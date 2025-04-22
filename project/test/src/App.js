import React from 'react';
import { Container, Paper } from '@mui/material';
import ApartmentSearch from './components/ApartmentSearch';

function App() {
  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 3 }}>
        <ApartmentSearch />
      </Paper>
    </Container>
  );
}

export default App;
