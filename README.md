<img src="https://cdn.rawgit.com/juice-ryang/online-judge/master/OnlineJudgeServer/static/logo.svg" width="128px">

# Jr. Online Judge.
어서오세요, 여기는 **주니어 온라인 저지**(*쥬스-량* 온라인 저지)의 소스코드 저장소입니다.

## 소개
비 CS 전공자분들의 원활한 Python 적응을 위하여, 컴퓨팅사고력 (CT) 강의에서 제공되는 실습자료를 채점해주는 웹서비스입니다.

[기존의 Online Judge](https://acmicpc.net)의 자동 채점 시스템에 몇 가지 배려사항이라고 생각되는 부분을 추가하였습니다.

- **채점 기록이 남지 않습니다.**
	- 로그인 없이, 문제를 맞으실 때까지 여러 번 시도하셔도 됩니다.
- **채점이 실패했다면,**
	- 프로그램을 **바로 종료**시킵니다.
	- **왜 실패했는지**를 알려드립니다.
	- **입력과 출력에 사용한 데이터**를 알려드립니다.
	- 실제 출력된 출력과 예상했던 출력의 **차이를 비교**해 드립니다.
	- **새로고침을 통한 빠른 재시도**를 도와드립니다.
- 실행이 오래 걸려도 어느 정도 기다려 드립니다.
	- 너무 오래 걸린다면, 프로그램을 안전히 종료시킵니다.
- 더 많은 기능을 생각중에 있습니다. (~~제안하기~~)

## 접속법
- [**Judge**.juice500.ml](http://Judge.juice500.ml)
- [**Judge**.vita500.ml](http://Judge.vita500.ml)

## 만든이
- Juice ( @Juice500ml , SGCS14 )
- Ryang ( @MinHoRyang , SGCS09 )

## License
GPLv3 [(kor)](https://www.olis.or.kr/ossw/license/license/detail.do?lid=1072)

## 더 읽기
- [**개발을 도와주는 법**, **같이 개발하는 법** ~~(a.k.a 맥주를 사주고 싶을 때)~~ -- **(작성 예정)**](#)
- [Jr. OnlineJudge를 배포해서 강의에 사용하고 싶어요. -- **(작성 예정)**](#)
- [**문제집(ProblemSet)**과 **문제(Problem)**를 관리하는 법](https://github.com/juice-ryang/online-judge/wiki/Problem-Store)
- [문제의 **채점 데이터(In/Out, TestCase)**를 생성하는 법](https://github.com/juice-ryang/online-judge/wiki/Creating-TestCase)
- [TestCase가 **채점되는 방식**](https://github.com/juice-ryang/online-judge/wiki/Judging)