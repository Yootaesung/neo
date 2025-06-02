import pyaudio
import speech_recognition as sr
import threading
from pydub import AudioSegment
from pydub.generators import Sine
import wikipedia

# 비속어 리스트
profane_words = ["비속어1", "비속어2", "비속어3"]  # 원하는 비속어로 수정

# 오디오 설정
FORMAT = pyaudio.paInt16   # 16비트 오디오
CHANNELS = 1               # 모노
RATE = 44100               # 샘플링 레이트 (44.1kHz)
CHUNK = 1024               # 청크 크기

# PyAudio 객체 생성
audio = pyaudio.PyAudio()

# 음성 인식 객체 생성
recognizer = sr.Recognizer()

# 입력 스트림 (마이크)
input_stream = audio.open(format=FORMAT,
                          channels=CHANNELS,
                          rate=RATE,
                          input=True,
                          frames_per_buffer=CHUNK)

# 출력 스트림 (스피커)
output_stream = audio.open(format=FORMAT,
                           channels=CHANNELS,
                           rate=RATE,
                           output=True)

# 비속어를 '삐-' 소리로 대체하는 함수
def beep_sound(duration_ms=500):
    tone = Sine(1000).to_audio_segment(duration=duration_ms)  # 1000 Hz, 0.5초
    return tone.raw_data

# 단어 뜻을 가져오는 함수
def get_definition(word):
    try:
        # 한국어 설정
        wikipedia.set_lang("ko")
        summary = wikipedia.summary(word, sentences=1)
        print(f"[단어 설명]: {word} - {summary}")
    except wikipedia.exceptions.DisambiguationError as e:
        print(f"[단어 설명]: {word} - 여러 의미가 있습니다: {e.options[:3]}")
    except wikipedia.exceptions.PageError:
        print(f"[단어 설명]: {word} - 설명을 찾을 수 없습니다.")

# 음성 인식 함수 (스레드로 실행)
def recognize_and_filter(audio_data):
    try:
        audio = sr.AudioData(audio_data, RATE, 2)  # 음성 데이터 생성
        text = recognizer.recognize_google(audio, language='ko-KR')  # 한글 인식

        # 비속어 감지 및 필터링
        filtered_audio = audio_data
        for word in profane_words:
            if word in text:
                print(f"[비속어 감지]: {word}")
                # 삐- 소리로 대체
                beep = beep_sound(duration_ms=1000)
                filtered_audio = beep
                break
        
        # 전문용어와 사자성어 감지
        words = text.split()
        for word in words:
            if len(word) > 1:  # 한 글자는 의미가 적음
                get_definition(word)

        # 필터링된 오디오 데이터를 스피커로 출력
        output_stream.write(filtered_audio)

    except sr.UnknownValueError:
        print("[음성 텍스트]: 인식 불가")
    except sr.RequestError as e:
        print(f"[오류]: 음성 인식 서비스 오류: {e}")

print("실시간 음성 필터링 시작... (종료: Ctrl+C)")

try:
    while True:
        # 마이크로부터 오디오 데이터 읽기
        audio_data = input_stream.read(CHUNK)

        # 음성 인식을 별도의 스레드로 처리
        threading.Thread(target=recognize_and_filter, args=(audio_data,)).start()

except KeyboardInterrupt:
    print("\n음성 스트리밍 종료.")

finally:
    # 스트림 종료
    input_stream.stop_stream()
    input_stream.close()
    output_stream.stop_stream()
    output_stream.close()
    audio.terminate()
