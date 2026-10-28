/** Compatibility renderers for withdrawn legacy predictions. */
async function renderVeneMLPredictions(venue, format = 'ODI', containerId = 'panel-probability-insights') { showPredictionUnavailable(containerId); }
async function renderMatchContextInsight(a, b, venue = null, containerId = 'panel-context') {
  showPredictionUnavailable(containerId === 'panel-insights' ? 'win-prob-card' : containerId);
}
async function renderPredictionLeaderboardCards(metric = '50', format = 'ODI', limit = 10, containerId = 'panel-leaderboard') { showPredictionUnavailable(containerId); }
