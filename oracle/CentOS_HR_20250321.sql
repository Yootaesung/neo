WITH empcte(empname, mgrname, dept, emplevel)
AS
(
	(SELECT emp, manager, department, 0
	FROM emptbl
	WHERE manager='없음')
	UNION ALL
	(SELECT emptbl.emp, emptbl.manager, 
	emptbl.department, empcte.emplevel+1
	FROM emptbl INNER JOIN empcte
	ON emptbl.manager = empcte.empname)
)
SELECT concat(rpad('ㄴ', emplevel * 2 + 1 , 'ㄴ'), 
empname) AS "직원이름",
dept AS "직원부서"
FROM empcte ORDER BY dept, emplevel; 

WITH empcte(empname, mgrname, dept, emplevel)
AS
(
	(SELECT emp, manager, department, 0
	FROM emptbl
	WHERE manager='없음')
	UNION ALL
	(SELECT emptbl.emp, emptbl.manager, 
	emptbl.department, empcte.emplevel+1
	FROM emptbl INNER JOIN empcte
	ON emptbl.manager = empcte.empname
	WHERE emplevel < 2)
)
SELECT concat(rpad('ㄴ', emplevel * 2 + 1 , 'ㄴ'), 
empname) AS "직원이름",
dept AS "직원부서"
FROM empcte ORDER BY dept, emplevel; 

CREATE TABLE testtbl (id NUMBER(4), username nchar(3), age number(2));

INSERT INTO testtbl values(1, '홍길동', 25);

SELECT * FROM testtbl;

INSERT INTO testtbl (id, username) values(2, '설현');

INSERT INTO testtbl (username, id, age) VALUES('지민', 3, 26);

SELECT * FROM testtbl;

-- error 
INSERT INTO testtbl VALUES(4, 36, '공유');

SELECT * FROM testtbl;

CREATE TABLE testtbl2 (
	id number(4),
	username nchar(3),
	age number(2),
	nation nchar(4) DEFAULT '대한민국'
);

CREATE SEQUENCE idseq2
START WITH 1
INCREMENT BY 1;

INSERT INTO testtbl2 VALUES (idseq2.nextval, '유나', 25, default);

SELECT * FROM testtbl2;

INSERT INTO testtbl2 VALUES (11, '쯔위', 18, '대만');

SELECT * FROM testtbl2;

ALTER SEQUENCE idseq2
INCREMENT BY 10;

INSERT INTO testtbl2 VALUES (idseq2.nextval, '미나', 21, '일본');

SELECT * FROM testtbl2;

ALTER SEQUENCE idseq2
INCREMENT BY 1;

INSERT INTO testtbl2 VALUES (idseq2.nextval, '사나', 21, '일본');

SELECT * FROM testtbl2;

ALTER SEQUENCE idseq2
INCREMENT BY 5;

INSERT INTO testtbl2 VALUES (idseq2.nextval, '채영', 23, DEFAULT);

SELECT * FROM testtbl2;

SELECT idseq2.currval FROM testtbl2;

--

CREATE TABLE testtbl3 (id NUMBER(3));

CREATE SEQUENCE cycleseq
START WITH 100
INCREMENT BY 100
MINVALUE 100
MAXVALUE 300
CYCLE
nocache;

INSERT INTO testtbl3 VALUES (cycleseq.nextval);

INSERT INTO testtbl3 VALUES (cycleseq.nextval);

INSERT INTO testtbl3 VALUES (cycleseq.nextval);

INSERT INTO testtbl3 VALUES (cycleseq.nextval);

SELECT * FROM testtbl3;

-- 

CREATE TABLE testtbl4(
	empid number(6),
	firstname varchar2(20),
	lastname varchar2(25),
	phone varchar2(20)
);

INSERT INTO testtbl4
	SELECT EMPLOYEE_id, first_name, last_name, phone_number
	FROM employees;

SELECT * FROM testtbl4;

-- Update Query

UPDATE testtbl4
	SET firstname='David'
	WHERE empid=100;

SELECT * FROM testtbl4
WHERE empid=100;

-- delete Query

SELECT * FROM testtbl4 WHERE lastname='King';


COMMIT;

DELETE FROM testtbl4 
WHERE firstname='David' AND lastname='King';

SELECT * FROM testtbl4 WHERE lastname='King';


-- rollback
ROLLBACK;

SELECT * FROM testtbl4 WHERE lastname='King';

CREATE TABLE bigtbl1
AS 
	SELECT LEVEL AS bigid,
	round (dbms_random.value(1, 500000), 0)
AS numdata
	FROM dual
	CONNECT BY LEVEL <= 500000;

CREATE TABLE bigtbl2
AS 
	SELECT LEVEL AS bigid,
	round (dbms_random.value(1, 500000), 0)
AS numdata
	FROM dual
	CONNECT BY LEVEL <= 500000;

CREATE TABLE bigtbl3
AS 
	SELECT LEVEL AS bigid,
	round (dbms_random.value(1, 500000), 0)
AS numdata
	FROM dual
	CONNECT BY LEVEL <= 500000;

DELETE FROM bigtbl1;

COMMIT;

DROP TABLE bigtbl2;

TRUNCATE TABLE bigtbl3;

DROP TABLE bigtbl1;

DROP TABLE bigtbl3;

CREATE TABLE member1
AS (SELECT userid, username, addr FROM usertbl);

SELECT * FROM member1;

CREATE TABLE changetbl (
	userid char(8),
	username nvarchar2(10),
	addr nchar(2),
	changetype nchar(4)
);

INSERT INTO changetbl values('TKV', '태권브이','한국','신규가입');
INSERT INTO changetbl values('LGG', NULL,'제주','주소변경');
INSERT INTO changetbl values('LJB', NULL,'한국','주소변경');
INSERT INTO changetbl values('BBK', NULL,'탈퇴','회원탈퇴');
INSERT INTO changetbl values('SSK', NULL,'탈퇴','회원탈퇴');

SELECT * FROM changetbl;

MERGE INTO member1 M
USING (SELECT changetype, userid, username, addr FROM changetbl) C
ON (M.userid = C.userid)
WHEN MATCHED THEN
	UPDATE SET M.addr = C.addr
	DELETE WHERE C.changetype = '회원탈퇴'
WHEN NOT MATCHED THEN
	INSERT (userid, username, addr) VALUES (C.userid, C.username, C.addr)
	
SELECT * FROM changetbl;

SELECT * FROM usertbl;

SELECT * FROM member1;

SELECT '100' + '200' FROM dual;

SELECT concat('100', '200') FROM dual;

SELECT 100 || '200' FROM dual;

SELECT price FROM buytbl WHERE price >= '500';

SELECT ascii('A'), chr(65), asciistr('한'), unistr('\D55C') FROM dual;

SELECT LENGTH('한글'), length('AB'), lengthb('한글'), lengthb('AB') FROM dual;

SELECT concat('이걸이', 'ORACLE이다'), '이것이' || 'ORACLE이다' FROM dual;

SELECT instr('이걸이 ORACLE이다. 이것도 ORACLE이다', '이것', 2) FROM dual;

SELECT lower('abcdEFGH'), upper('abcdEFGH'), initcap('this is oracle') FROM dual;

SELECT REPLACE('이것이 ORACLE이다', '이것이', 'This is') FROM dual;

SELECT TRANSLATE('이것이 ORACLE이다', '이것이', 'AB') FROM dual;

SELECT substr('대한민국만세', 3, 2) FROM dual;

SELECT reverse('Oracle') FROM dual;

SELECT lpad('이것이', 10, '##'), rpad('이것이', 10, '##') from dual;

SELECT ltrim('이것이'), rtrim('이것이$$$', '$') FROM dual;

SELECT trim('이것이'), trim(BOTH 'ㅋ' FROM 'ㅋㅋ재밌어요.ㅋㅋㅋㅋㅋㅋㅋㅋ') FROM dual;

SELECT regexp_count('이것이 오라클이다', '이') FROM dual;

--

SELECT abs(-100) FROM dual;

SELECT CEIL(4.4), floor(4.4), round(4.4) FROM dual;

SELECT mod(13,4) FROM dual;

SELECT power(2,3) FROM dual;

SELECT sign(100), sign(0), sign(-100.123) FROM dual;

SELECT trunc(12345.12345, 2), trunc(12345.12345, -2) FROM dual;

SELECT add_months('2025-01-01', 5), add_months(sysdate, -5) FROM dual;

SELECT TO_DATE('2025-01-01') + 5, sysdate - 5 FROM dual;

SELECT extract(YEAR FROM DATE '2025-01-01'), extract(DAY FROM sysdate) FROM dual;

SELECT last_day('2025-02-01') FROM dual;

SELECT next_day('2025-03-21', '금요일'), next_day(sysdate, '토요일') FROM dual;

SELECT months_between(sysdate, '2004-11-22') FROM dual;

--

SELECT bin_to_num(1,0), bin_to_num(1,1,1,1) FROM dual;

SELECT bin_to_num(1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1) FROM dual;

SELECT NUMTODSINTERVAL(48, 'HOUR'), NUMTODSINTERVAL(360000, 'SECOND') FROM dual;

SELECT NUMTOYMINTERVAL(37, 'MONTH'), NUMTOYMINTERVAL(1.5, 'YEAR') FROM dual;

--

SELECT row_number() OVER (ORDER BY height desc) "키 큰 순위", username, addr, height 
FROM usertbl;

SELECT row_number() OVER (ORDER BY height asc) "키 큰 순위", username, addr, height 
FROM usertbl;

SELECT addr, row_number() 
OVER (PARTITION BY addr ORDER BY height DESC, username asc)
"키 큰 순위", username, addr, height
FROM usertbl;

SELECT dense_rank() 
OVER (ORDER BY height DESC)
"키 큰 순위", username, addr, height
FROM usertbl;

SELECT rank() 
OVER (ORDER BY height DESC)
"키 큰 순위", username, addr, height
FROM usertbl;

-- 라운드 로빈
SELECT NTILE(3) over(ORDER BY height desc) 
"반번호", username, addr, height FROM USERTBL u ;

SELECT username, addr, height AS "키",
height - (lead(height, 1, 0)
over(ORDER BY height desc))
	AS "다음 사람과의 키 차이"
	FROM usertbl;

SELECT username, addr, height AS "키",
height - (first_value(height)
over(partition BY addr ORDER by height desc))
	AS "지역별 최대 키와 차이"
	FROM usertbl;

SELECT username, addr, height AS "키",
(CUME_DIST() OVER (PARTITION BY addr ORDER BY height desc)) * 100
	AS "누적 인원 백분율 (%)"
	FROM usertbl u ;

CREATE TABLE pivotTest(
	uname nchar(3),
	season nchar(2),
	amount number(3)
);

INSERT INTO PIVOTTEST VALUES ('김범수', '겨울', 10);
INSERT INTO PIVOTTEST VALUES ('윤종신', '여름', 15);
INSERT INTO PIVOTTEST VALUES ('김범수', '가을', 25);
INSERT INTO PIVOTTEST VALUES ('김범수', '봄', 3);
INSERT INTO PIVOTTEST VALUES ('김범수', '봄', 37);
INSERT INTO PIVOTTEST VALUES ('윤종신', '겨울', 40);
INSERT INTO PIVOTTEST VALUES ('김범수', '여름', 14);
INSERT INTO PIVOTTEST VALUES ('김범수', '겨울', 22);
INSERT INTO PIVOTTEST VALUES ('윤종신', '여름', 64);

SELECT * FROM pivottest;

SELECT * FROM pivotTest
	pivot(sum(amount)
		FOR season
		IN('봄','여름','가을','겨울'));