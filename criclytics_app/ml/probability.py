"""Prediction availability boundary. Legacy heuristics are not deployable models."""


def unavailable(**context):
    return {**context, 'available': False, 'kind': 'unavailable',
            'source': 'legacy_heuristics_withdrawn', 'cutoff': None,
            'sample_count': None, 'probability': None, 'confidence': None,
            'validated': False, 'model_id': None,
            'unavailable_reason': 'No chronologically evaluated and calibrated model is released.'}


class ProbabilityEngine:
    """Compatibility interface; never reads artifacts or serves old formulas."""
    def __init__(self, data_dir=None):
        self.data_dir = data_dir

    def player_performance_likelihood(self, player_name, metric, format='ODI'):
        return unavailable(player=player_name, metric=metric, format=format)

    def team_match_outcome(self, team_a, team_b, format='ODI', venue=None):
        return unavailable(team_a=team_a, team_b=team_b, format=format, venue=venue)

    def venue_performance_bias(self, venue_name, team=None, format='ODI'):
        return unavailable(venue=venue_name, team=team, format=format)

    def leaderboard_predictions(self, format='ODI', metric='50', limit=10):
        return unavailable(format=format, metric=metric, predictions=[], evaluated_players=0)
