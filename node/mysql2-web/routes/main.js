const express = require('express');
const bodyParser = require('body-parser');
const pool = require('../../conf/pool')

const app = express();

app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: false }));
app.use(express.json());
app.use(express.urlencoded({ extended: true}));


app.get('/Hello', (req, res) => {
    res.send('Hello World!!')
})

// select all rows from st_info table
app.get('/select', async (req, res) => {
    const [rows] = await pool.query('select * from st_info');
    console.log(rows);
    res.send(rows);
})

module.exports = app;