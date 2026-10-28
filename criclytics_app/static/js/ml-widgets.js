/** Prediction widgets: unavailable until a validated model is released. */
const PREDICTION_UNAVAILABLE = 'Predictions unavailable. No chronologically evaluated and calibrated model is released.';
async function loadPlayerProbabilities() { return null; }
async function loadTeamMatchPrediction() { return null; }
async function loadVenuePerformanceBias() { return null; }
async function loadPredictionLeaderboard() { return null; }
function showPredictionUnavailable(containerId) {
  var container = document.getElementById(containerId);
  if (container) {
    container.textContent = PREDICTION_UNAVAILABLE;
    container.setAttribute('role', 'status');
  }
}
function renderProbabilityCard() { return '<p>Predictions unavailable pending evaluation and calibration.</p>'; }
async function renderPlayerPredictionsTab(player, format = 'ODI', containerId = 'panel-ml') { showPredictionUnavailable(containerId); }
async function renderPlayerProbabilityTab(player, format = 'ODI', containerId = 'panel-probability') { showPredictionUnavailable(containerId); }
async function renderTeamMatchPrediction(a, b, format = 'ODI', venue = null, containerId) { showPredictionUnavailable(containerId); }
function getMetricIcon() { return 'fa-circle-info'; }
function getMetricLabel(metric) { return String(metric || 'Unavailable'); }
function renderPercentageBar() { return ''; }
