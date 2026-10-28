"""Offline attribution-backed 2024 final cross-check; requires local Cricsheet file."""
import json
from criclytics_app.paths import PROJECT_ROOT
from criclytics_app.pipeline.scoring import score_match
from criclytics_app.pipeline.rebuild import digest


def main():
    path = PROJECT_ROOT / 'data/raw/t20s_male_json/1415755.json'
    match = json.loads(path.read_text(encoding='utf-8'))
    value = score_match(match)
    innings = value['innings']
    actual = [(i['team'], i['total'], i['wickets'], i['overs']) for i in innings]
    assert actual == [('India', 176, 7, '20.0'), ('South Africa', 169, 8, '20.0')], actual
    players = {r['batsman']: (r['r'], r['b']) for i in innings for r in i['batting']}
    assert players['V Kohli'] == (76, 59)
    assert players['H Klaasen'] == (52, 27)
    result = {'match': '2024-06-29 India v South Africa, T20 World Cup Final',
              'source': 'Cricsheet JSON, Open Data Commons Attribution License 1.0',
              'raw_sha256': digest(path), 'actual_innings': actual,
              'players': {name: players[name] for name in ('V Kohli', 'H Klaasen')},
              'independent_reference': [
                  'https://www.bcci.tv/matches/0aaa903c-1b4e-4647-b739-bdfa695798f4/south-africa-vs-india/scorecard',
                  'https://www.icc-cricket.com/tournaments/t20cricketworldcup/news/final-over-thrillers-in-the-2024-men-s-t20-world-cup/',
                  'https://www.icc-cricket.com/tournaments/t20cricketworldcup/news/live-india-and-south-africa-face-off-in-t20-world-cup-final?appview=true'],
              'limitations': 'Selected innings and batting figures only; not every historic scorecard independently reviewed.'}
    (PROJECT_ROOT / 'docs/audit/real-scorecard-2026-10-28.json').write_text(
        json.dumps(result, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
