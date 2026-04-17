"""
ml_probability_engine.py
========================
ML Probability Inference Engine for Criclytics
Generates probability predictions using processed cricket data.

Features:
- Player performance probabilities (scoring, wickets, average, SR)
- Team match outcome predictions
- Venue-based performance bias
- Head-to-head trend analysis
"""

import json
import os
from typing import Dict, List, Tuple, Optional
import numpy as np
from scipy import stats


class ProbabilityEngine:
    """Main ML engine for probability predictions."""
    
    def __init__(self, data_dir: str = "data/processed"):
        """
        Initialize the engine with processed cricket data.
        
        Args:
            data_dir: Path to processed data directory
        """
        self.data_dir = data_dir
        self.players_data = self._load_json("players_index.json")
        self.player_yearly = self._load_json("player_yearly.json")
        self.player_vs_opp = self._load_json("player_vs_opp.json")
        self.player_venues = self._load_json("player_venues.json")
        self.team_stats = self._load_json("team_format_stats.json")
        self.team_venue_stats = self._load_json("team_venue_stats.json")
        self.h2h_data = self._load_json("h2h.json")
        self.venue_stats = self._load_json("venue_stats.json")
        self.venue_insights = self._load_json("venue_insights.json")

    def _load_json(self, filename: str) -> Dict:
        """Load a JSON file from data directory."""
        path = os.path.join(self.data_dir, filename)
        if not os.path.exists(path):
            return {}
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            return {}

    # ═════════════════════════════════════════════════════════════════════════
    # PLAYER PROBABILITY CALCULATIONS
    # ═════════════════════════════════════════════════════════════════════════

    def player_performance_likelihood(
        self, player_name: str, metric: str, format: str = "ODI"
    ) -> Dict:
        """
        Calculate probability of a player achieving a metric.
        
        Args:
            player_name: Player's name
            metric: One of ['50', '100', 'wicket_maiden', 'strike_rate>140', 'avg>50']
            format: Test / ODI / T20I
            
        Returns:
            Dict with probability, confidence, recent_form, etc.
        """
        if not self.players_data or player_name not in self.players_data:
            return self._empty_probability("Player not found")

        player = self.players_data[player_name]
        yearly = self.player_yearly.get(player_name, {})

        # Get recent performance (last 5 years for the format)
        yearly_format = yearly.get(format, {})
        recent_years = sorted(yearly_format.keys(), reverse=True)[:5]
        recent_data = [yearly_format.get(year, {}) for year in recent_years]
        recent_data = [d for d in recent_data if d]  # Filter empty

        if not recent_data:
            return self._empty_probability("No recent data")

        # Calculate probability based on metric
        if metric == "50":
            return self._prob_score_50(player_name, format, recent_data)
        elif metric == "100":
            return self._prob_score_100(player_name, format, recent_data)
        elif metric == "wicket_maiden":
            return self._prob_wicket_maiden(player_name, format, recent_data)
        elif metric == "strike_rate>140":
            return self._prob_high_strike_rate(player_name, format, recent_data)
        elif metric == "avg>50":
            return self._prob_high_average(player_name, format, recent_data)
        else:
            return self._empty_probability(f"Unknown metric: {metric}")

    def _prob_score_50(
        self, player_name: str, format: str, recent_data: List[Dict]
    ) -> Dict:
        """Probability of scoring 50+ runs."""
        if not recent_data:
            return self._empty_probability("No data")

        # Extract recent averages
        averages = [
            d.get("average", 0) for d in recent_data if d.get("average")
        ]
        
        if not averages:
            return self._empty_probability("No average data")

        avg_recent = np.mean(averages)
        consistency = np.std(averages) if len(averages) > 1 else 0

        # Probability heuristic: higher recent average = higher prob of 50+
        # Assume 50 is approximately 1 standard deviation above league mean
        prob = 1 - stats.norm.sf(50, loc=avg_recent, scale=max(15, consistency + 10))
        prob = np.clip(prob, 0.1, 0.9)

        return {
            "probability": float(prob),
            "confidence": min(0.95, 0.5 + len(recent_data) * 0.1),
            "recent_average": float(avg_recent),
            "recent_form": "strong" if avg_recent > 40 else "moderate" if avg_recent > 25 else "weak",
            "metric": "Scoring 50+ runs",
            "format": format,
            "data_points": len(recent_data),
        }

    def _prob_score_100(
        self, player_name: str, format: str, recent_data: List[Dict]
    ) -> Dict:
        """Probability of scoring 100+ runs (century)."""
        if not recent_data:
            return self._empty_probability("No data")

        averages = [d.get("average", 0) for d in recent_data if d.get("average")]
        if not averages:
            return self._empty_probability("No average data")

        avg_recent = np.mean(averages)
        consistency = np.std(averages) if len(averages) > 1 else 0

        # Century is much rarer—higher threshold
        prob = 1 - stats.norm.sf(100, loc=avg_recent, scale=max(20, consistency + 15))
        prob = np.clip(prob, 0.05, 0.7)

        return {
            "probability": float(prob),
            "confidence": min(0.90, 0.4 + len(recent_data) * 0.08),
            "recent_average": float(avg_recent),
            "recent_form": "elite" if avg_recent > 50 else "strong" if avg_recent > 40 else "moderate",
            "metric": "Scoring 100+ runs (Century)",
            "format": format,
            "data_points": len(recent_data),
        }

    def _prob_wicket_maiden(
        self, player_name: str, format: str, recent_data: List[Dict]
    ) -> Dict:
        """Probability of taking a wicket in a match."""
        if not recent_data:
            return self._empty_probability("No data")

        wickets = [d.get("wickets", 0) for d in recent_data if d.get("wickets")]
        if not wickets:
            return self._empty_probability("No bowling data")

        avg_wickets = np.mean(wickets)
        
        # Probability wickets per match > 0 (simple heuristic)
        prob = min(0.9, 0.3 + avg_wickets * 0.15)

        return {
            "probability": float(prob),
            "confidence": min(0.92, 0.5 + len(recent_data) * 0.09),
            "recent_average_wickets": float(avg_wickets),
            "recent_form": "lethal" if avg_wickets > 1.5 else "consistent" if avg_wickets > 0.8 else "occasional",
            "metric": "Taking 1+ wickets",
            "format": format,
            "data_points": len(recent_data),
        }

    def _prob_high_strike_rate(
        self, player_name: str, format: str, recent_data: List[Dict]
    ) -> Dict:
        """Probability of strike rate > 140 (T20/ODI aggression)."""
        if not recent_data:
            return self._empty_probability("No data")

        strike_rates = [
            d.get("strike_rate", 0) for d in recent_data if d.get("strike_rate")
        ]
        if not strike_rates:
            return self._empty_probability("No SR data")

        avg_sr = np.mean(strike_rates)
        
        prob = 1 - stats.norm.sf(140, loc=avg_sr, scale=max(20, 25))
        prob = np.clip(prob, 0.1, 0.8)

        return {
            "probability": float(prob),
            "confidence": min(0.93, 0.5 + len(recent_data) * 0.1),
            "recent_strike_rate": float(avg_sr),
            "recent_form": "aggressive" if avg_sr > 140 else "balanced" if avg_sr > 100 else "cautious",
            "metric": "Strike Rate > 140",
            "format": format,
            "data_points": len(recent_data),
        }

    def _prob_high_average(
        self, player_name: str, format: str, recent_data: List[Dict]
    ) -> Dict:
        """Probability of maintaining average > 50."""
        if not recent_data:
            return self._empty_probability("No data")

        averages = [d.get("average", 0) for d in recent_data if d.get("average")]
        if not averages:
            return self._empty_probability("No average data")

        avg_recent = np.mean(averages)
        
        prob = 1 - stats.norm.sf(50, loc=avg_recent, scale=max(10, 15))
        prob = np.clip(prob, 0.1, 0.95)

        return {
            "probability": float(prob),
            "confidence": min(0.95, 0.5 + len(recent_data) * 0.1),
            "recent_average": float(avg_recent),
            "recent_form": "elite" if avg_recent > 50 else "strong" if avg_recent > 40 else "moderate",
            "metric": "Maintaining Average > 50",
            "format": format,
            "data_points": len(recent_data),
        }

    # ═════════════════════════════════════════════════════════════════════════
    # TEAM PROBABILITY CALCULATIONS
    # ═════════════════════════════════════════════════════════════════════════

    def team_match_outcome(
        self, team_a: str, team_b: str, format: str = "ODI", venue: Optional[str] = None
    ) -> Dict:
        """
        Predict match outcome probability.
        
        Args:
            team_a: First team
            team_b: Second team
            format: Test / ODI / T20I
            venue: Optional venue name for bias analysis
            
        Returns:
            Dict with win probabilities for both teams
        """
        # Get team strengths
        team_a_strength = self._team_format_strength(team_a, format)
        team_b_strength = self._team_format_strength(team_b, format)

        if team_a_strength is None or team_b_strength is None:
            return {
                "team_a": {"name": team_a, "win_probability": 0.5},
                "team_b": {"name": team_b, "win_probability": 0.5},
                "error": "Team data not found",
            }

        # Base strengths (normalized 0-100)
        strength_a = team_a_strength.get("win_pct", 0.5) * 100
        strength_b = team_b_strength.get("win_pct", 0.5) * 100

        # Apply venue bias if provided
        if venue:
            venue_bias_a = self._venue_bias_for_team(venue, team_a, format)
            venue_bias_b = self._venue_bias_for_team(venue, team_b, format)
            strength_a *= (1 + venue_bias_a * 0.2)
            strength_b *= (1 + venue_bias_b * 0.2)

        # Normalize to probabilities
        total = strength_a + strength_b
        prob_a = strength_a / total if total > 0 else 0.5
        prob_b = 1 - prob_a

        # Apply h2h adjustment
        h2h_adj = self._h2h_adjustment(team_a, team_b, format)
        prob_a = prob_a * (1 + h2h_adj * 0.15)
        prob_a = np.clip(prob_a, 0.2, 0.8)
        prob_b = 1 - prob_a

        return {
            "team_a": {
                "name": team_a,
                "win_probability": float(prob_a),
                "strength": float(strength_a),
                "recent_form": "strong" if strength_a > 60 else "moderate" if strength_a > 40 else "weak",
            },
            "team_b": {
                "name": team_b,
                "win_probability": float(prob_b),
                "strength": float(strength_b),
                "recent_form": "strong" if strength_b > 60 else "moderate" if strength_b > 40 else "weak",
            },
            "venue": venue,
            "format": format,
            "prediction": "Team A" if prob_a > 0.55 else "Team B" if prob_b > 0.55 else "Too Close",
            "prediction_confidence": float(max(prob_a, prob_b)),
        }

    def _team_format_strength(
        self, team_name: str, format: str
    ) -> Optional[Dict]:
        """Get team strength metrics for a format."""
        if not self.team_stats:
            return None

        team_data = self.team_stats.get(team_name)
        if not team_data:
            # Try case-insensitive
            for key in self.team_stats:
                if key.lower() == team_name.lower():
                    team_data = self.team_stats[key]
                    break

        if not team_data:
            return None

        return team_data.get(format, {})

    def _venue_bias_for_team(
        self, venue: str, team: str, format: str
    ) -> float:
        """Calculate home/away advantage for a team at a venue."""
        if not self.team_venue_stats:
            return 0.0

        team_venues = self.team_venue_stats.get(team, {})
        venue_data = team_venues.get(venue, {})

        # Bias: +0.2 for strong home record, -0.2 for weak
        win_pct = venue_data.get("win_pct", 0.5)
        bias = (win_pct - 0.5) * 2  # Scale to [-1, 1]

        return bias

    def _h2h_adjustment(self, team_a: str, team_b: str, format: str) -> float:
        """Get head-to-head historical advantage."""
        if not self.h2h_data:
            return 0.0

        h2h_key = f"{team_a}|{team_b}|{format}"
        record = self.h2h_data.get(h2h_key)

        if not record:
            h2h_key = f"{team_b}|{team_a}|{format}"
            record = self.h2h_data.get(h2h_key)
            if record:
                # Flip the perspective
                team_a_wins = record.get("team_b_wins", 0)
            else:
                return 0.0
        else:
            team_a_wins = record.get("team_a_wins", 0)

        total_matches = record.get("matches", 1)
        if total_matches == 0:
            return 0.0

        h2h_win_pct = team_a_wins / total_matches
        adjustment = (h2h_win_pct - 0.5) * 2  # Scale to [-1, 1]

        return adjustment

    # ═════════════════════════════════════════════════════════════════════════
    # VENUE PROBABILITY CALCULATIONS
    # ═════════════════════════════════════════════════════════════════════════

    def venue_performance_bias(
        self, venue: str, team: str = None, format: str = "ODI"
    ) -> Dict:
        """
        Analyze performance bias at a venue.
        
        Returns:
            Dict with chasing vs defending, avg scores, player success rates, etc.
        """
        if not self.venue_insights:
            return self._empty_probability("Venue data not found")

        venue_data = self.venue_insights.get(venue, {})
        if not venue_data:
            return self._empty_probability(f"No insights for {venue}")

        chasing_avg = venue_data.get("chasing", {}).get("avg_score", 0)
        defending_avg = venue_data.get("defending", {}).get("avg_score", 0)

        chasing_win_rate = venue_data.get("chasing", {}).get("win_rate", 0.5)

        # Bias: positive = chasing advantage, negative = defending advantage
        bias = (chasing_win_rate - 0.5) * 2

        return {
            "venue": venue,
            "format": format,
            "chasing_average": float(chasing_avg),
            "defending_average": float(defending_avg),
            "chasing_win_rate": float(chasing_win_rate),
            "chasing_bias": "strong" if bias > 0.3 else "slight" if bias > 0 else "defending",
            "bias_score": float(bias),
            "avg_score_difference": float(chasing_avg - defending_avg),
        }

    # ═════════════════════════════════════════════════════════════════════════
    # UTILITY FUNCTIONS
    # ═════════════════════════════════════════════════════════════════════════

    def _empty_probability(self, reason: str = "No data") -> Dict:
        """Return empty probability structure."""
        return {
            "probability": 0.5,
            "confidence": 0.0,
            "reason": reason,
        }

    def batch_player_probabilities(
        self, player_names: List[str], metrics: List[str], format: str = "ODI"
    ) -> Dict[str, Dict]:
        """Calculate probabilities for multiple players and metrics."""
        results = {}
        for player_name in player_names:
            results[player_name] = {}
            for metric in metrics:
                results[player_name][metric] = self.player_performance_likelihood(
                    player_name, metric, format
                )
        return results

    def leaderboard_predictions(
        self, format: str = "ODI", metric: str = "50", limit: int = 10
    ) -> List[Dict]:
        """Get top players by probability of achieving a metric."""
        if not self.players_data:
            return []

        results = []
        for player_name in list(self.players_data.keys())[:100]:  # Sample for performance
            prob_data = self.player_performance_likelihood(
                player_name, metric, format
            )
            if "probability" in prob_data:
                results.append({
                    "player": player_name,
                    **prob_data,
                })

        # Sort by probability
        results.sort(key=lambda x: x.get("probability", 0), reverse=True)

        return results[:limit]
