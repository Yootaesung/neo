import React, { useState } from 'react';
import {
  TextField,
  Button,
  Grid,
  Typography,
  Autocomplete,
  CircularProgress,
  Box
} from '@mui/material';
import axios from 'axios';

const API_BASE_URL = 'http://192.168.1.42:5000';

function ApartmentSearch() {
  const [loading, setLoading] = useState(false);
  const [dongOptions, setDongOptions] = useState([]);
  const [stationOptions, setStationOptions] = useState([]);
  const [apartmentOptions, setApartmentOptions] = useState([]);
  const [areaOptions, setAreaOptions] = useState([]);
  const [floorOptions, setFloorOptions] = useState([]);
  
  const [selectedValues, setSelectedValues] = useState({
    dong: '',
    station: '',
    bubjungdongCode: '',
    openDate: '',
    apartmentName: '',
    exclusiveArea: '',
    floor: ''
  });
  const [results, setResults] = useState(null);

  // 법정동 검색
  const searchDong = async (searchText) => {
    if (!searchText || searchText.length < 1) return;
    try {
      const response = await axios.get(`${API_BASE_URL}/bubjungdong/getbubjungdong?dong=${encodeURIComponent(searchText)}`);
      if (response.data && Array.isArray(response.data)) {
        setDongOptions(response.data);
      }
    } catch (error) {
      console.error('법정동 검색 오류:', error);
      setDongOptions([]);
    }
  };

  // 역 검색
  const searchStation = async (searchText) => {
    if (!searchText || searchText.length < 1) return;
    try {
      const response = await axios.get(`${API_BASE_URL}/subway/getsubway?station=${encodeURIComponent(searchText)}`);
      if (response.data && Array.isArray(response.data)) {
        setStationOptions(response.data);
      }
    } catch (error) {
      console.error('역 검색 오류:', error);
      setStationOptions([]);
    }
  };

  // 아파트 검색
  const searchApartments = async () => {
    const { openDate, bubjungdongCode } = selectedValues;
    if (!openDate || !bubjungdongCode) return;
    
    try {
      const response = await axios.get(`${API_BASE_URL}/apartment/getapartment`, {
        params: { openDate, bubjungdongCode }
      });
      if (response.data && Array.isArray(response.data)) {
        setApartmentOptions(response.data);
        // 이전 선택값들 초기화
        setSelectedValues(prev => ({
          ...prev,
          apartmentName: '',
          exclusiveArea: '',
          floor: ''
        }));
      }
    } catch (error) {
      console.error('아파트 검색 오류:', error);
      setApartmentOptions([]);
    }
  };

  // 전용면적 검색
  const searchAreas = async () => {
    const { openDate, bubjungdongCode, apartmentName } = selectedValues;
    if (!openDate || !bubjungdongCode || !apartmentName) return;

    try {
      const response = await axios.get(`${API_BASE_URL}/excluusear/getexcluusear`, {
        params: { openDate, bubjungdongCode, apartmentName }
      });
      if (response.data && Array.isArray(response.data)) {
        setAreaOptions(response.data);
        // 이전 선택값들 초기화
        setSelectedValues(prev => ({
          ...prev,
          exclusiveArea: '',
          floor: ''
        }));
      }
    } catch (error) {
      console.error('전용면적 검색 오류:', error);
      setAreaOptions([]);
    }
  };

  // 층 검색
  const searchFloors = async () => {
    const { openDate, bubjungdongCode, apartmentName, exclusiveArea } = selectedValues;
    if (!openDate || !bubjungdongCode || !apartmentName || !exclusiveArea) return;

    try {
      const response = await axios.get(`${API_BASE_URL}/floor/getfloor`, {
        params: { openDate, bubjungdongCode, apartmentName, exclusiveArea }
      });
      if (response.data && Array.isArray(response.data)) {
        setFloorOptions(response.data);
        // 이전 선택값들 초기화
        setSelectedValues(prev => ({
          ...prev,
          floor: ''
        }));
      }
    } catch (error) {
      console.error('층 검색 오류:', error);
      setFloorOptions([]);
    }
  };



  // 최종 검색
  const handleSearch = async () => {
    setLoading(true);
    try {
      const { openDate, bubjungdongCode, apartmentName, exclusiveArea, floor } = selectedValues;
      
      const params = {
        openDate,
        bubjungdongCode,
        apartmentName,
        exclusiveArea,
        floor
      };

      const [priceResponse, lineGraphResponse, barChartResponse] = await Promise.all([
        axios.get(`${API_BASE_URL}/aptprice/getaptprice`, { params }),
        axios.get(`${API_BASE_URL}/aptprice/getaptpricelinegraph`, { params }),
        axios.get(`${API_BASE_URL}/aptprice/getaptpricebarchart`, { params })
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

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        아파트 실거래가 조회
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Autocomplete
            options={dongOptions}
            getOptionLabel={(option) => (option.name || '') + ' (' + (option.code || '') + ')'}
            onInputChange={(_, value) => {
              if (value && value.length >= 1) {
                searchDong(value);
              }
            }}
            onChange={(_, value) => {
              setSelectedValues(prev => ({
                ...prev,
                dong: value?.name || '',
                bubjungdongCode: value?.code || ''
              }));
              if (value?.code) {
                searchApartments();
              }
            }}
            renderInput={(params) => (
              <TextField
                {...params}
                label="법정동 검색"
                variant="outlined"
                fullWidth
                helperText="동 이름을 입력하면 코드가 자동으로 설정됩니다"
              />
            )}
          />
        </Grid>

        <Grid item xs={12} md={6}>
          <Autocomplete
            options={stationOptions}
            getOptionLabel={(option) => option.name || ''}
            onInputChange={(_, value) => {
              if (value && value.length >= 1) {
                searchStation(value);
              }
            }}
            onChange={(_, value) => {
              setSelectedValues(prev => ({
                ...prev,
                station: value?.name || '',
                openDate: value?.openDate || ''
              }));
              if (value?.openDate) {
                searchApartments();
              }
            }}
            renderInput={(params) => (
              <TextField
                {...params}
                label="지하철역 검색"
                variant="outlined"
                fullWidth
                helperText="역 이름을 입력하면 개통일이 자동으로 설정됩니다"
              />
            )}
          />
        </Grid>

        <Grid item xs={12} md={6}>
          <TextField
            label="개통일"
            variant="outlined"
            fullWidth
            value={selectedValues.openDate}
            onChange={(e) => setSelectedValues(prev => ({ ...prev, openDate: e.target.value }))}
            placeholder="YYYYMMDD"
            helperText="예: 20131221"
          />
        </Grid>

        <Grid item xs={12} md={6}>
          <Autocomplete
            options={apartmentOptions}
            getOptionLabel={(option) => option.name || ''}
            value={apartmentOptions.find(opt => opt.name === selectedValues.apartmentName) || null}
            onChange={(_, value) => {
              setSelectedValues(prev => ({
                ...prev,
                apartmentName: value?.name || ''
              }));
              if (value?.name) {
                searchAreas();
              }
            }}
            renderInput={(params) => (
              <TextField
                {...params}
                label="아파트명"
                variant="outlined"
                fullWidth
                helperText="아파트를 선택하세요"
              />
            )}
          />
        </Grid>

        <Grid item xs={12} md={6}>
          <Autocomplete
            options={areaOptions}
            getOptionLabel={(option) => option.area || ''}
            value={areaOptions.find(opt => opt.area === selectedValues.exclusiveArea) || null}
            onChange={(_, value) => {
              setSelectedValues(prev => ({
                ...prev,
                exclusiveArea: value?.area || ''
              }));
              if (value?.area) {
                searchFloors();
              }
            }}
            renderInput={(params) => (
              <TextField
                {...params}
                label="전용면적"
                variant="outlined"
                fullWidth
                helperText="전용면적을 선택하세요"
              />
            )}
          />
        </Grid>

        <Grid item xs={12} md={6}>
          <Autocomplete
            options={floorOptions}
            getOptionLabel={(option) => option.floor || ''}
            value={floorOptions.find(opt => opt.floor === selectedValues.floor) || null}
            onChange={(_, value) => {
              setSelectedValues(prev => ({
                ...prev,
                floor: value?.floor || ''
              }));
            }}
            renderInput={(params) => (
              <TextField
                {...params}
                label="층"
                variant="outlined"
                fullWidth
                helperText="층을 선택하세요"
              />
            )}
          />
        </Grid>

        <Grid item xs={12}>
          <Button
            variant="contained"
            color="primary"
            onClick={handleSearch}
            disabled={loading}
            fullWidth
          >
            {loading ? <CircularProgress size={24} /> : '검색'}
          </Button>
        </Grid>
      </Grid>

      {results && (
        <Box mt={4}>
          <Typography variant="h5" gutterBottom>
            검색 결과
          </Typography>
          
          {results.lineGraph?.image_url && (
            <Box mt={2}>
              <img 
                src={`${API_BASE_URL}${results.lineGraph.image_url}`}
                alt="가격 추이 그래프"
                style={{ maxWidth: '100%' }}
              />
            </Box>
          )}

          {results.barChart?.image_url && (
            <Box mt={2}>
              <img 
                src={`${API_BASE_URL}${results.barChart.image_url}`}
                alt="가격 분포 그래프"
                style={{ maxWidth: '100%' }}
              />
            </Box>
          )}
        </Box>
      )}
    </Box>
  );
}

export default ApartmentSearch;
