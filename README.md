<div align="center">
<h2>업무를 보면서도, 중요한 일을 놓치지 않도록<br>
  📢"나만의 PC 알리미 서비스"📢</h2>
</div>

<br>

## 다운로드 링크
- 희망하는 버전명 클릭 시 다운로드 링크로 이동됩니다.
- 링크 클릭으로 다운로드가 정상적으로 되지 않는 경우, 현재 리포지토리에서 deploy 폴더의 exe 파일을 다운받아 사용하시면 됩니다.

|버전명|배포일|추가 기능|
|:---:|:---:|:---:|
|[ver 1.1](https://drive.google.com/file/d/150V0DB7kEZaRNmgoaPYubYTc8nZMipOu/view?usp=sharing)|2025.09.28|시간(분 단위)+요일 선택 알리미 기능 추가|
|[ver 1.0](https://drive.google.com/file/d/1mW2BqmvUEdcuESXa16dITe1j3Wzks2Ya/view?usp=sharing)|2025.09.28|시간에 대한 알리미 기능|

## ⚙️ 주요 기능
### 알림 설정 및 PC 내 토글 알림 기능
- 원하는 요일과 시간(초 단위까지 가능)에 알림을 설정할 수 있습니다.
- 토글 사용 여부를 선택할 수 있습니다.
- 확인 주기를 선택할 수 있습니다. (확인 주기 : 프로그램이 시간을 주기적으로 확인하는 주기를 의미합니다.) <br>
⚠️확인 주기가 너무 짧을 경우 프로그램의 CPU 사용량이 늘어날 수 있습니다. (30초~60초를 권장합니다.)
- 데이터는 저장됩니다. 저장되는 파일 경로는 프로그램 실행 시 최하단 [데이터 파일 위치]에서 확인하실 수 있습니다.
- 원하는 시간 약 5분 전에 리마인드 토글을 최상단으로 띄워줍니다.

|<img width="1087" height="712" alt="image" src="https://github.com/user-attachments/assets/3a5bc1e4-efbf-4c08-9b44-32ae9c69efbe" />|<img width="559" height="362" alt="image" src="https://github.com/user-attachments/assets/066a8575-ab8f-4825-8768-3ab4c3e7ca83" />|
|:---:|:---:|
|메인 화면|토글 표시|

## ❓Q&A
**Q. exe 파일을 다운받고 실행했는데 실행이 느리게 됩니다.** <br>
A. 처음 실행 시 5-30초 내외로 실행됩니다.

**Q. 오전/오후 구분은 무엇으로 하나요?** <br>
A. 오전은 00:00-11:59, 오후는 12:00-24:00 으로 표기합니다.
즉, 오후 8시 30분은, 20:30 으로 입력해야 합니다.

**Q. 과거 시간을 입력하는 경우, 어떤 방식으로 처리되나요?** <br>
A. 만약 현재 시간이 2025년 09월 28일 22시 20분이고 알림으로 입력한 시간이 매일 08시 30분이라면, 익일(2025년 09월 29일)부터 매일 08시 25분 즈음에 토글이 뜨게 됩니다.

## 📅 개발 개요
- 개발 기간 : 2025.09.28
- 기술 스택
<div style="display: flex; justify-content: space-evenly; flex-wrap: wrap;">
  <img src="https://img.shields.io/badge/python-3776AB?style=for-the-badge&logo=python&logoColor=white">
</div>

## 💡 기획 계기
- 개발 업무 중 일정을 놓치는 경우가 존재
- PC 팝업을 통해 일정을 리마인드 하자!
