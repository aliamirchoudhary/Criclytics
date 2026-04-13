"""
ml_models.py
============
Train and manage logistic regression models for cricket probability predictions.

Models:
- Player Batting: Probability of scoring 50+, 100+, maintaining high average
- Player Bowling: Probability of taking wickets, maintaining low economy
- Team Win: Probability of winning a match
- Venue Bias: Chasing vs defending advantage
"""

import json
import os
import pickle
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from typing import Dict, Tuple, Optional, List


class CricketMLModels:
    """Manages trained ML models for cricket predictions."""
    
    def __init__(self, data_dir: str = "data/processed", model_dir: str = "models"):
        """
        Initialize models manager.
        
        Args:
            data_dir: Path to processed cricket data
            model_dir: Path to save/load trained models
        """
        self.data_dir = data_dir
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)
        
        # Load data
        self.players_data = self._load_json("players_index.json")
        self.player_yearly = self._load_json("player_yearly.json")
        self.team_stats = self._load_json("team_format_stats.json")
        self.h2h_data = self._load_json("h2h.json")
        self.venue_insights = self._load_json("venue_insights.json")
        
        # Models
        self.player_batting_50_model = None
        self.player_batting_100_model = None
        self.player_bowling_wicket_model = None
        self.team_win_model = None
        self.venue_bias_model = None
        
        # Scalers for feature normalization
        self.batting_scaler = None
        self.bowling_scaler = None
        self.team_scaler = None
        self.venue_scaler = None
        
        # Try to load pre-trained models
        self._load_models()

    def _load_json(self, filename: str) -> Dict:
        """Load a JSON file from data directory."""
        path = os.path.join(self.data_dir, filename)
        if not os.path.exists(path):
            return {}
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[ML] Error loading {filename}: {e}")
            return {}

    def _save_model(self, model, scaler, name: str):
        """Save model and scaler to disk."""
        try:
            with open(os.path.join(self.model_dir, f"{name}_model.pkl"), "wb") as f:
                pickle.dump(model, f)
            with open(os.path.join(self.model_dir, f"{name}_scaler.pkl"), "wb") as f:
                pickle.dump(scaler, f)
            print(f"[ML] Saved model: {name}")
        except Exception as e:
            print(f"[ML] Error saving {name}: {e}")

    def _load_models(self):
        """Load pre-trained models from disk."""
        models_to_load = [
            ("player_batting_50", "player_batting_50_model"),
            ("player_batting_100", "player_batting_100_model"),
            ("player_bowling_wicket", "player_bowling_wicket_model"),
            ("team_win", "team_win_model"),
            ("venue_bias", "venue_bias_model"),
        ]
        
        for model_name, attr_name in models_to_load:
            model_path = os.path.join(self.model_dir, f"{model_name}_model.pkl")
            scaler_path = os.path.join(self.model_dir, f"{model_name}_scaler.pkl")
            
            if os.path.exists(model_path) and os.path.exists(scaler_path):
                try:
                    with open(model_path, "rb") as f:
                        model = pickle.load(f)
                    with open(scaler_path, "rb") as f:
                        scaler = pickle.load(f)
                    
                    setattr(self, attr_name, model)
                    setattr(self, f"{attr_name.replace('model', 'scaler')}", scaler)
                    print(f"[ML] Loaded model: {model_name}")
                except Exception as e:
                    print(f"[ML] Error loading {model_name}: {e}")

    def train_all_models(self):
        """Train all logistic regression models."""
        print("\n[ML] Training models...")
        
        self._train_player_batting_50()
        self._train_player_batting_100()
        self._train_player_bowling_wicket()
        self._train_team_win()
        self._train_venue_bias()
        
        print("[ML] All models trained.")

    # ═════════════════════════════════════════════════════════════════════════
    # PLAYER BATTING MODELS
    # ═════════════════════════════════════════════════════════════════════════

    def _train_player_batting_50(self):
        """Train logistic regression for P(score >= 50)."""
        X, y = self._prepare_batting_data("50+")
        if len(X) < 10:
            print("[ML] Not enough data for batting 50+ model")
            return
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        model = LogisticRegression(max_iter=1000, random_state=42)
        model.fit(X_scaled, y)
        
        self.player_batting_50_model = model
        self.batting_scaler = scaler
        print(f"[ML] Trained batting 50+ model (n={len(X)}, accuracy={model.score(X_scaled, y):.2%})")
        self._save_model(model, scaler, "player_batting_50")

    def _train_player_batting_100(self):
        """Train logistic regression for P(score >= 100)."""
        X, y = self._prepare_batting_data("100+")
        if len(X) < 10:
            print("[ML] Not enough data for batting 100+ model")
            return
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        model = LogisticRegression(max_iter=1000, random_state=42)
        model.fit(X_scaled, y)
        
        self.player_batting_100_model = model
        print(f"[ML] Trained batting 100+ model (n={len(X)}, accuracy={model.score(X_scaled, y):.2%})")
        self._save_model(model, scaler, "player_batting_100")

    def _prepare_batting_data(self, threshold: str) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data for batting targets."""
        X_list, y_list = [], []
        
        for player_name, yearly_data in self.player_yearly.items():
            for year, formats in yearly_data.items():
                for format, stats in formats.items():
                    if not isinstance(stats, dict):
                        continue
                    
                    # Features: average, SR, innings
                    avg = stats.get("average", 0)
                    sr = stats.get("strike_rate", 0)
                    inn = stats.get("innings", 0)
                    
                    if inn < 3:  # Need enough data
                        continue
                    
                    # Target: did player score threshold or more?
                    runs = stats.get("runs", 0)
                    if threshold == "50+":
                        target = 1 if (runs / max(inn, 1)) >= 50 else 0
                    elif threshold == "100+":
                        target = 1 if (runs / max(inn, 1)) >= 100 else 0
                    else:
                        continue
                    
                    if avg > 0 and sr > 0:  # Valid stats
                        X_list.append([avg, sr, inn])
                        y_list.append(target)
        
        if not X_list:
            return np.array([]).reshape(0, 3), np.array([])
        
        return np.array(X_list), np.array(y_list)

    # ═════════════════════════════════════════════════════════════════════════
    # PLAYER BOWLING MODELS
    # ═════════════════════════════════════════════════════════════════════════

    def _train_player_bowling_wicket(self):
        """Train logistic regression for P(takes >= 1 wicket per match)."""
        X, y = self._prepare_bowling_data()
        if len(X) < 10:
            print("[ML] Not enough data for bowling wicket model")
            return
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        model = LogisticRegression(max_iter=1000, random_state=42)
        model.fit(X_scaled, y)
        
        self.player_bowling_wicket_model = model
        self.bowling_scaler = scaler
        print(f"[ML] Trained bowling wicket model (n={len(X)}, accuracy={model.score(X_scaled, y):.2%})")
        self._save_model(model, scaler, "player_bowling_wicket")

    def _prepare_bowling_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data for bowling targets."""
        X_list, y_list = [], []
        
        for player_name, yearly_data in self.player_yearly.items():
            for year, formats in yearly_data.items():
                for format, stats in formats.items():
                    if not isinstance(stats, dict):
                        continue
                    
                    # Features: average, economy, matches
                    avg = stats.get("average", 0)  # Bowling average
                    econ = stats.get("economy", 0)
                    matches = stats.get("matches", 0)
                    
                    if matches < 3:
                        continue
                    
                    # Target: takes wickets per match >= 1
                    wickets = stats.get("wickets", 0)
                    target = 1 if (wickets / max(matches, 1)) >= 1 else 0
                    
                    if avg > 0 and econ > 0:
                        X_list.append([avg, econ, matches])
                        y_list.append(target)
        
        if not X_list:
            return np.array([]).reshape(0, 3), np.array([])
        
        return np.array(X_list), np.array(y_list)

    # ═════════════════════════════════════════════════════════════════════════
    # TEAM WIN MODELS
    # ═════════════════════════════════════════════════════════════════════════

    def _train_team_win(self):
        """Train logistic regression for team match win probability."""
        X, y = self._prepare_team_data()
        if len(X) < 10:
            print("[ML] Not enough data for team win model")
            return
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        model = LogisticRegression(max_iter=1000, random_state=42)
        model.fit(X_scaled, y)
        
        self.team_win_model = model
        self.team_scaler = scaler
        print(f"[ML] Trained team win model (n={len(X)}, accuracy={model.score(X_scaled, y):.2%})")
        self._save_model(model, scaler, "team_win")

    def _prepare_team_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data for team match outcomes."""
        X_list, y_list = [], []
        
        for h2h_key, record in self.h2h_data.items():
            parts = h2h_key.split("|")
            if len(parts) != 3:
                continue
            
            team_a, team_b, fmt = parts
            
            # Features: team_a win%, team_b win%, matches played
            matches = record.get("matches", 0)
            if matches < 3:  # Need enough history
                continue
            
            team_a_wins = record.get("team_a_wins", 0)
            team_b_wins = record.get("team_b_wins", 0)
            
            team_a_win_pct = team_a_wins / matches if matches > 0 else 0.5
            team_b_win_pct = team_b_wins / matches if matches > 0 else 0.5
            
            # Add team A perspective: feature [A%, B%, matches], target [1 if A wins]
            if team_a_wins > 0:
                X_list.append([team_a_win_pct, team_b_win_pct, matches])
                y_list.append(1)
            
            # Add team A loss perspective: feature [A%, B%, matches], target [0 if A loses]
            if team_b_wins > 0:
                X_list.append([team_a_win_pct, team_b_win_pct, matches])
                y_list.append(0)
        
        if not X_list:
            return np.array([]).reshape(0, 3), np.array([])
        
        return np.array(X_list), np.array(y_list)

    # ═════════════════════════════════════════════════════════════════════════
    # VENUE BIAS MODELS
    # ═════════════════════════════════════════════════════════════════════════

    def _train_venue_bias(self):
        """Train logistic regression for chasing advantage at venues."""
        X, y = self._prepare_venue_data()
        if len(X) < 5:
            print("[ML] Not enough data for venue bias model")
            return
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        model = LogisticRegression(max_iter=1000, random_state=42)
        model.fit(X_scaled, y)
        
        self.venue_bias_model = model
        self.venue_scaler = scaler
        print(f"[ML] Trained venue bias model (n={len(X)}, accuracy={model.score(X_scaled, y):.2%})")
        self._save_model(model, scaler, "venue_bias")

    def _prepare_venue_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data for venue chasing bias."""
        X_list, y_list = [], []
        
        for venue_name, insights in self.venue_insights.items():
            if not isinstance(insights, dict):
                continue
            
            chasing_data = insights.get("chasing", {})
            defending_data = insights.get("defending", {})
            
            chasing_avg = chasing_data.get("avg_score", 0)
            defending_avg = defending_data.get("avg_score", 0)
            chasing_wins = chasing_data.get("wins", 0)
            defending_wins = defending_data.get("wins", 0)
            
            total_chasing = chasing_data.get("matches", 0)
            total_defending = defending_data.get("matches", 0)
            
            if total_chasing > 0 and total_defending > 0:
                chasing_win_rate = chasing_wins / total_chasing if total_chasing > 0 else 0.5
                
                # Features: avg scores, win rates, matches
                X_list.append([chasing_avg, defending_avg, chasing_win_rate])
                # Target: 1 = chasing advantage, 0 = defending advantage
                y_list.append(1 if chasing_avg > defending_avg else 0)
        
        if not X_list:
            return np.array([]).reshape(0, 3), np.array([])
        
        return np.array(X_list), np.array(y_list)

    # ═════════════════════════════════════════════════════════════════════════
    # PREDICTION METHODS
    # ═════════════════════════════════════════════════════════════════════════

    def predict_batting_50(self, player_name: str, format: str = "ODI") -> Dict:
        """Predict probability of scoring 50+."""
        if not self.player_batting_50_model or not self.batting_scaler:
            return {"probability": 0.5, "confidence": 0.0, "reason": "Model not trained"}
        
        # Extract features from player yearly data
        player_yearly = self.player_yearly.get(player_name, {})
        year_data = player_yearly.get(max(player_yearly.keys(), default=''), {}) if player_yearly else {}
        format_data = year_data.get(format, {}) if year_data else {}
        
        avg = format_data.get("average", 30)
        sr = format_data.get("strike_rate", 100)
        inn = format_data.get("innings", 1)
        
        X = np.array([[avg, sr, inn]])
        X_scaled = self.batting_scaler.transform(X)
        
        prob = self.player_batting_50_model.predict_proba(X_scaled)[0][1]
        confidence = max(abs(self.player_batting_50_model.predict_proba(X_scaled)[0] - 0.5)) * 2
        
        return {
            "probability": float(prob),
            "confidence": float(confidence),
            "recent_average": float(avg),
            "recent_form": "strong" if avg > 40 else "moderate" if avg > 25 else "weak",
            "metric": "Scoring 50+ runs",
        }

    def predict_batting_100(self, player_name: str, format: str = "ODI") -> Dict:
        """Predict probability of scoring 100+ (century)."""
        if not self.player_batting_100_model:
            return {"probability": 0.3, "confidence": 0.0, "reason": "Model not trained"}
        
        player_yearly = self.player_yearly.get(player_name, {})
        year_data = player_yearly.get(max(player_yearly.keys(), default=''), {}) if player_yearly else {}
        format_data = year_data.get(format, {}) if year_data else {}
        
        avg = format_data.get("average", 30)
        sr = format_data.get("strike_rate", 100)
        inn = format_data.get("innings", 1)
        
        X = np.array([[avg, sr, inn]])
        X_scaled = self.batting_scaler.transform(X)
        
        prob = self.player_batting_100_model.predict_proba(X_scaled)[0][1]
        confidence = max(abs(self.player_batting_100_model.predict_proba(X_scaled)[0] - 0.5)) * 2
        
        return {
            "probability": float(prob),
            "confidence": float(confidence),
            "recent_average": float(avg),
            "recent_form": "elite" if avg > 50 else "strong" if avg > 40 else "moderate",
            "metric": "Scoring 100+ runs (Century)",
        }

    def predict_bowling_wicket(self, player_name: str, format: str = "ODI") -> Dict:
        """Predict probability of taking 1+ wicket."""
        if not self.player_bowling_wicket_model or not self.bowling_scaler:
            return {"probability": 0.5, "confidence": 0.0, "reason": "Model not trained"}
        
        player_yearly = self.player_yearly.get(player_name, {})
        year_data = player_yearly.get(max(player_yearly.keys(), default=''), {}) if player_yearly else {}
        format_data = year_data.get(format, {}) if year_data else {}
        
        avg = format_data.get("average", 30)
        econ = format_data.get("economy", 5.0)
        matches = format_data.get("matches", 1)
        
        X = np.array([[avg, econ, matches]])
        X_scaled = self.bowling_scaler.transform(X)
        
        prob = self.player_bowling_wicket_model.predict_proba(X_scaled)[0][1]
        confidence = max(abs(self.player_bowling_wicket_model.predict_proba(X_scaled)[0] - 0.5)) * 2
        
        return {
            "probability": float(prob),
            "confidence": float(confidence),
            "recent_average_wickets": float(format_data.get("wickets", 0)),
            "recent_form": "lethal" if avg < 20 else "consistent" if avg < 30 else "occasional",
            "metric": "Taking 1+ wickets",
        }

    def predict_team_win(self, team_a: str, team_b: str, format: str = "ODI") -> Dict:
        """Predict team A win probability."""
        if not self.team_win_model or not self.team_scaler:
            return {"probability": 0.5, "confidence": 0.0, "reason": "Model not trained"}
        
        # Get team stats
        team_a_stats = self.team_stats.get(team_a, {}).get(format, {})
        team_b_stats = self.team_stats.get(team_b, {}).get(format, {})
        
        team_a_win_pct = team_a_stats.get("win_pct", 0.5)
        team_b_win_pct = team_b_stats.get("win_pct", 0.5)
        
        # Get h2h matches
        h2h_key = f"{team_a}|{team_b}|{format}"
        h2h = self.h2h_data.get(h2h_key, {})
        matches = h2h.get("matches", 5)
        
        X = np.array([[team_a_win_pct, team_b_win_pct, matches]])
        X_scaled = self.team_scaler.transform(X)
        
        prob_a = self.team_win_model.predict_proba(X_scaled)[0][1]
        
        return {
            "probability": float(prob_a),
            "team_a_strength": float(team_a_win_pct * 100),
            "team_b_strength": float(team_b_win_pct * 100),
            "form": "strong" if team_a_win_pct > 0.6 else "moderate" if team_a_win_pct > 0.4 else "weak",
        }

    def predict_venue_chasing_bias(self, venue_name: str) -> Dict:
        """Predict chasing advantage at a venue."""
        if not self.venue_bias_model or not self.venue_scaler:
            return {"probability": 0.5, "confidence": 0.0, "reason": "Model not trained"}
        
        venue_insights = self.venue_insights.get(venue_name, {})
        chasing_data = venue_insights.get("chasing", {})
        defending_data = venue_insights.get("defending", {})
        
        chasing_avg = chasing_data.get("avg_score", 150)
        defending_avg = defending_data.get("avg_score", 150)
        chasing_wins = chasing_data.get("wins", 10)
        chasing_matches = chasing_data.get("matches", 20)
        chasing_win_rate = chasing_wins / chasing_matches if chasing_matches > 0 else 0.5
        
        X = np.array([[chasing_avg, defending_avg, chasing_win_rate]])
        X_scaled = self.venue_scaler.transform(X)
        
        prob_chasing = self.venue_bias_model.predict_proba(X_scaled)[0][1]
        
        return {
            "probability_chasing_advantage": float(prob_chasing),
            "chasing_average": float(chasing_avg),
            "defending_average": float(defending_avg),
            "bias": "chasing" if prob_chasing > 0.55 else "defending" if prob_chasing < 0.45 else "neutral",
        }
