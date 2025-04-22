import React, { useState } from 'react';
import {
  TextField,
  Button,
  Grid,
  Typography,
  CircularProgress,
  Box,
  FormControl,
  FormLabel,
  RadioGroup,
  FormControlLabel,
  Radio,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow
} from '@mui/material';
import axios from 'axios';

const API_BASE_URL = 'http://192.168.1.42:5000';

function ApartmentSearch() {
  const [loading, setLoading] = useState(false);
  const [searchResults, setSearchResults] = useState({
    dong: [],
    station: [],
    apartments: [],
    areas: [],
    floors: []
  });
  const [graphType, setGraphType] = useState('line');
  
  const [searchValues, setSearchValues] = useState({
    dong: '',
    bubjungdongCode: '',
    station: '',
    openDate: '',
    apartmentName: '',
    exclusiveArea: '',
    floor: ''
  });
  const [results, setResults] = useState(null);

  // 법정동 검색
  const searchDong = async () => {
    if (!searchValues.dong) return;
    setLoading(true);
    try {
      const response = await axios.get(`http://localhost:8000/bubjungdong/getbubjungdong?dong=${searchValues.dong}`);
      setSearchResults(prev => ({ ...prev, dong: response.data }));
    } catch (error) {
      console.error('Error fetching dong data:', error);
    } finally {
      setLoading(false);
    }
  };

  // 역 검색
  const searchStation = async () => {
    if (!searchValues.station) return;
    setLoading(true);
    try {
      const response = await axios.get(`http://localhost:8000/subway/getsubway?station=${searchValues.station}`);
      setSearchResults(prev => ({ ...prev, station: response.data }));
    } catch (error) {
      console.error('Error fetching station data:', error);
    } finally {
      setLoading(false);
    }
  };

  // 아파트 검색
  const searchApartments = async () => {
    if (!searchValues.openDate || !searchValues.bubjungdongCode) return;
    setLoading(true);
    try {
      const response = await axios.get(`http://localhost:8000/apartment/getapartment?openDate=${searchValues.openDate}&bubjungdongCode=${searchValues.bubjungdongCode}`);
      setSearchResults(prev => ({ ...prev, apartments: response.data }));
    } catch (error) {
      console.error('Error fetching apartment data:', error);
    } finally {
      setLoading(false);
    }
  };

  // 전용면적 검색
  const searchAreas = async () => {
    if (!searchValues.openDate || !searchValues.bubjungdongCode || !searchValues.apartmentName) return;
    setLoading(true);
    try {
      const response = await axios.get(`http://localhost:8000/excluusear/getexcluusear?openDate=${searchValues.openDate}&bubjungdongCode=${searchValues.bubjungdongCode}&apartmentName=${searchValues.apartmentName}`);
      setSearchResults(prev => ({ ...prev, areas: response.data }));
    } catch (error) {
      console.error('Error fetching area data:', error);
    } finally {
      setLoading(false);
    }
  };

  // 층 검색
  const searchFloors = async () => {
    if (!searchValues.openDate || !searchValues.bubjungdongCode || !searchValues.apartmentName || !searchValues.exclusiveArea) return;
    setLoading(true);
    try {
      const response = await axios.get(`http://localhost:8000/floor/getfloor?openDate=${searchValues.openDate}&bubjungdongCode=${searchValues.bubjungdongCode}&apartmentName=${searchValues.apartmentName}&exclusiveArea=${searchValues.exclusiveArea}`);
      setSearchResults(prev => ({ ...prev, floors: response.data }));
    } catch (error) {
      console.error('Error fetching floor data:', error);
    } finally {
      setLoading(false);
    }
  };



  // 최종 검색
  const handleSearch = async () => {
    setLoading(true);
    try {
      const { openDate, bubjungdongCode, apartmentName, exclusiveArea, floor } = searchValues;
      
      const params = {
        openDate,
        bubjungdongCode,
        apartmentName,
        exclusiveArea,
        floor
      };

      const [priceResponse, lineGraphResponse, barChartResponse] = await Promise.all([
        axios.get(`http://localhost:8000/aptprice/getaptprice?${new URLSearchParams(params)}`),
        axios.get(`http://localhost:8000/aptprice/getaptpricelinegraph?${new URLSearchParams(params)}`),
        axios.get(`http://localhost:8000/aptprice/getaptpricebarchart?${new URLSearchParams(params)}`)
      ]);

      setResults({
        price: priceResponse.data,
        lineGraph: lineGraphResponse.data,
        barChart: barChartResponse.data
      });
    } catch (error) {
      console.error('검색 오류:', error);
    } finally {
      setLoading(false);
    }
  };

  const isSearchEnabled = () => {
    const { openDate, bubjungdongCode, apartmentName, exclusiveArea, floor } = searchValues;
    return openDate && bubjungdongCode && apartmentName && exclusiveArea && floor;
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        아파트 가격 조회
      </Typography>

      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 2 }}>
          <CircularProgress />
        </Box>
      )}

      <Grid container spacing={3}>
        {/* 법정동 검색 */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>법정동 검색</Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} md={9}>
                <TextField
                  label="법정동 이름"
                  value={searchValues.dong}
                  onChange={(e) => setSearchValues(prev => ({ ...prev, dong: e.target.value }))}
                  fullWidth
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <Button
                  variant="contained"
                  onClick={searchDong}
                  disabled={!searchValues.dong || loading}
                  fullWidth
                  sx={{ height: '100%' }}
                >
                  검색
                </Button>
              </Grid>
            </Grid>
            {searchResults.dong.length > 0 && (
              <TableContainer component={Paper} sx={{ mt: 2 }}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>법정동명</TableCell>
                      <TableCell>코드</TableCell>
                      <TableCell>선택</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {searchResults.dong.map((item, index) => (
                      <TableRow key={index}>
                        <TableCell>{item.name}</TableCell>
                        <TableCell>{item.code}</TableCell>
                        <TableCell>
                          <Button
                            variant="contained"
                            size="small"
                            onClick={() => setSearchValues(prev => ({
                              ...prev,
                              bubjungdongCode: item.code
                            }))}
                          >
                            선택
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </Paper>
        </Grid>

        {/* 지하철역 검색 */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>지하철역 검색</Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} md={9}>
                <TextField
                  label="역 이름"
                  value={searchValues.station}
                  onChange={(e) => setSearchValues(prev => ({ ...prev, station: e.target.value }))}
                  fullWidth
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <Button
                  variant="contained"
                  onClick={searchStation}
                  disabled={!searchValues.station || loading}
                  fullWidth
                  sx={{ height: '100%' }}
                >
                  검색
                </Button>
              </Grid>
            </Grid>
            {searchResults.station.length > 0 && (
              <TableContainer component={Paper} sx={{ mt: 2 }}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>역명</TableCell>
                      <TableCell>개통일</TableCell>
                      <TableCell>선택</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {searchResults.station.map((item, index) => (
                      <TableRow key={index}>
                        <TableCell>{item.name}</TableCell>
                        <TableCell>{item.openDate}</TableCell>
                        <TableCell>
                          <Button
                            variant="contained"
                            size="small"
                            onClick={() => setSearchValues(prev => ({
                              ...prev,
                              openDate: item.openDate
                            }))}
                          >
                            선택
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </Paper>
        </Grid>

        {/* 아파트 검색 */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>아파트 검색</Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} md={4}>
                <TextField
                  label="개통일"
                  value={searchValues.openDate}
                  onChange={(e) => setSearchValues(prev => ({ ...prev, openDate: e.target.value }))}
                  fullWidth
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  label="법정동 코드"
                  value={searchValues.bubjungdongCode}
                  onChange={(e) => setSearchValues(prev => ({ ...prev, bubjungdongCode: e.target.value }))}
                  fullWidth
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <Button
                  variant="contained"
                  onClick={searchApartments}
                  disabled={!searchValues.openDate || !searchValues.bubjungdongCode || loading}
                  fullWidth
                  sx={{ height: '100%' }}
                >
                  검색
                </Button>
              </Grid>
            </Grid>
            {searchResults.apartments.length > 0 && (
              <TableContainer component={Paper} sx={{ mt: 2 }}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>아파트명</TableCell>
                      <TableCell>선택</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {searchResults.apartments.map((item, index) => (
                      <TableRow key={index}>
                        <TableCell>{item.name}</TableCell>
                        <TableCell>
                          <Button
                            variant="contained"
                            size="small"
                            onClick={() => setSearchValues(prev => ({
                              ...prev,
                              apartmentName: item.name
                            }))}
                          >
                            선택
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </Paper>
        </Grid>

        {/* 전용면적 검색 */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>전용면적 검색</Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} md={3}>
                <TextField
                  label="개통일"
                  value={searchValues.openDate}
                  onChange={(e) => setSearchValues(prev => ({ ...prev, openDate: e.target.value }))}
                  fullWidth
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <TextField
                  label="법정동 코드"
                  value={searchValues.bubjungdongCode}
                  onChange={(e) => setSearchValues(prev => ({ ...prev, bubjungdongCode: e.target.value }))}
                  fullWidth
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <TextField
                  label="아파트명"
                  value={searchValues.apartmentName}
                  onChange={(e) => setSearchValues(prev => ({ ...prev, apartmentName: e.target.value }))}
                  fullWidth
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <Button
                  variant="contained"
                  onClick={searchAreas}
                  disabled={!searchValues.openDate || !searchValues.bubjungdongCode || !searchValues.apartmentName || loading}
                  fullWidth
                  sx={{ height: '100%' }}
                >
                  검색
                </Button>
              </Grid>
            </Grid>
            {searchResults.areas.length > 0 && (
              <TableContainer component={Paper} sx={{ mt: 2 }}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>전용면적</TableCell>
                      <TableCell>선택</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {searchResults.areas.map((item, index) => (
                      <TableRow key={index}>
                        <TableCell>{item.area}㎡</TableCell>
                        <TableCell>
                          <Button
                            variant="contained"
                            size="small"
                            onClick={() => setSearchValues(prev => ({
                              ...prev,
                              exclusiveArea: item.area
                            }))}
                          >
                            선택
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </Paper>
        </Grid>

        {/* 층 검색 */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>층 검색</Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} md={2}>
                <TextField
                  label="개통일"
                  value={searchValues.openDate}
                  onChange={(e) => setSearchValues(prev => ({ ...prev, openDate: e.target.value }))}
                  fullWidth
                />
              </Grid>
              <Grid item xs={12} md={2}>
                <TextField
                  label="법정동 코드"
                  value={searchValues.bubjungdongCode}
                  onChange={(e) => setSearchValues(prev => ({ ...prev, bubjungdongCode: e.target.value }))}
                  fullWidth
                />
              </Grid>
              <Grid item xs={12} md={2}>
                <TextField
                  label="아파트명"
                  value={searchValues.apartmentName}
                  onChange={(e) => setSearchValues(prev => ({ ...prev, apartmentName: e.target.value }))}
                  fullWidth
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <TextField
                  label="전용면적"
                  value={searchValues.exclusiveArea ? `${searchValues.exclusiveArea}㎡` : ''}
                  onChange={(e) => setSearchValues(prev => ({ ...prev, exclusiveArea: e.target.value }))}
                  fullWidth
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <Button
                  variant="contained"
                  onClick={searchFloors}
                  disabled={!searchValues.openDate || !searchValues.bubjungdongCode || 
                           !searchValues.apartmentName || !searchValues.exclusiveArea || loading}
                  fullWidth
                  sx={{ height: '100%' }}
                >
                  검색
                </Button>
              </Grid>
            </Grid>
            {searchResults.floors.length > 0 && (
              <TableContainer component={Paper} sx={{ mt: 2 }}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>층</TableCell>
                      <TableCell>선택</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {searchResults.floors.map((item, index) => (
                      <TableRow key={index}>
                        <TableCell>{item.floor}층</TableCell>
                        <TableCell>
                          <Button
                            variant="contained"
                            size="small"
                            onClick={() => setSearchValues(prev => ({
                              ...prev,
                              floor: item.floor
                            }))}
                          >
                            선택
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </Paper>
        </Grid>

        {/* 그래프 선택 및 검색 */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>6. 그래프 선택 및 검색</Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <FormControl component="fieldset">
                  <FormLabel component="legend">그래프 종류</FormLabel>
                  <RadioGroup
                    row
                    value={graphType}
                    onChange={(e) => setGraphType(e.target.value)}
                  >
                    <FormControlLabel value="line" control={<Radio />} label="라인 그래프" />
                    <FormControlLabel value="bar" control={<Radio />} label="바 차트" />
                    <FormControlLabel value="both" control={<Radio />} label="둘 다 보기" />
                  </RadioGroup>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <Button
                  variant="contained"
                  color="primary"
                  onClick={handleSearch}
                  disabled={loading || !isSearchEnabled()}
                  fullWidth
                  sx={{ height: '100%' }}
                >
                  검색
                </Button>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
      </Grid>

      {results && (
        <Box sx={{ mt: 4 }}>
          <Typography variant="h6" gutterBottom>
            검색 결과
          </Typography>
          {graphType === 'line' && results.lineGraph?.image_url && (
            <Box sx={{ mt: 2 }}>
              <img 
                src={`${API_BASE_URL}${results.lineGraph.image_url}`}
                alt="가격 추이 그래프"
                style={{ maxWidth: '100%' }}
              />
            </Box>
          )}
          {graphType === 'bar' && results.barChart?.image_url && (
            <Box sx={{ mt: 2 }}>
              <img 
                src={`${API_BASE_URL}${results.barChart.image_url}`}
                alt="가격 분포 차트"
                style={{ maxWidth: '100%' }}
              />
            </Box>
          )}
          {graphType === 'both' && (
            <>
              {results.lineGraph?.image_url && (
                <Box sx={{ mt: 2 }}>
                  <img 
                    src={`${API_BASE_URL}${results.lineGraph.image_url}`}
                    alt="가격 추이 그래프"
                    style={{ maxWidth: '100%' }}
                  />
                </Box>
              )}
              {results.barChart?.image_url && (
                <Box sx={{ mt: 2 }}>
                  <img 
                    src={`${API_BASE_URL}${results.barChart.image_url}`}
                    alt="가격 분포 차트"
                    style={{ maxWidth: '100%' }}
                  />
                </Box>
              )}
            </>
          )}
        </Box>
      )}
    </Box>
  );
}

export default ApartmentSearch;
