let trendChart;

document.addEventListener('DOMContentLoaded', () => {
    updateDashboard();
});

function switchTab(tab) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.nav-tab').forEach(el => el.classList.remove('active'));
    document.getElementById(tab).classList.add('active');
    event.target.classList.add('active');
}

function updateDashboard() {
    document.getElementById('totalCost').textContent = '$18,500';
    document.getElementById('avgCPM').textContent = '$8.50';
    document.getElementById('avgCPV').textContent = '$0.45';
    document.getElementById('cpmMedian').textContent = '$8.50';
    document.getElementById('vcpmMedian').textContent = '$9.20';
    document.getElementById('avgCTR').textContent = '2.15%';
    document.getElementById('avgVR').textContent = '48.5%';
    updateTrendChart();
}

function updateTrendChart() {
    const ctx = document.getElementById('trendChart').getContext('2d');
    if (trendChart) trendChart.destroy();
    trendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
            datasets: [{
                label: 'Avg CPM',
                data: [7.5, 8.2, 8.9, 8.5, 8.7],
                borderColor: '#003d7a',
                backgroundColor: 'rgba(0, 61, 122, 0.1)',
                tension: 0.4
            }]
        },
        options: { responsive: true, maintainAspectRatio: true }
    });
}

function getPrediction(event) {
    event.preventDefault();
    document.getElementById('predictionResult').innerHTML = '<div style="padding: 20px; background: #f5f5f5; border-radius: 8px;"><p><strong>Predicted CPV:</strong> $0.42</p><p><strong>Predicted CPM:</strong> $8.75</p></div>';
}
