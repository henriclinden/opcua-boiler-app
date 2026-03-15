Chart.register(window['chartjs-plugin-annotation']);

const ctx = document.getElementById('tempChart').getContext('2d');

const tempData = {
  labels: [], // Timestamps or index
  datasets: [{
    label: 'Boiler Temperature (°C)',
    data: [],
    borderColor: 'rgb(255, 99, 132)',
    backgroundColor: 'rgba(255, 99, 132, 0.2)',
    tension: 0.3, // Makes the line curvy
    fill: true
  }]
};

const tempAnnotation = {
  annotations: {
    line1: {
      type: 'line',
      yMin: 80,
      yMax: 80,
      borderColor: 'red',
      borderWidth: 2,
      borderDash: [6, 6], // Makes it a dashed line
      label: {
        display: true,
        content: 'Critical Threshold (80°C)',
        position: 'end',
        backgroundColor: 'rgba(255, 0, 0, 0.8)'
      }
    }
  }
};

const tempChart = new Chart(ctx, {
  type: 'line',
  data: tempData,
  options: {
    responsive: true,
    maintainAspectRatio: false, // Allows the chart to fill the container height
    scales: {
      y: {
        beginAtZero: false,
        suggestedMax: 100
      }
    },
    plugins: {
      annotation: tempAnnotation,
    }
  }
});

// Function to call whenever new data arrives
function updateChart(newTemp) {
  const now = new Date().toLocaleTimeString();

  // Add new data
  tempChart.data.labels.push(now);
  tempChart.data.datasets[0].data.push(newTemp);

  // Keep only the last 40 readings so it doesn't get cluttered
  if (tempChart.data.labels.length > 40) {
    tempChart.data.labels.shift();
    tempChart.data.datasets[0].data.shift();
  }

  tempChart.update('none');
}
