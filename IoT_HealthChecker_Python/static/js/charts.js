const ctx = document.getElementById('patientChart');
fetch('/api/patient/{{ user.id }}/chart_data')
.then(res => res.json())
.then(data => {
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: data.labels,
      datasets: [
        { label: 'Heart Rate', data: data.heart, borderWidth: 2, borderColor: '#1E3A8A' },
        { label: 'SpO₂', data: data.spo2, borderWidth: 2, borderColor: '#06B6D4' },
        { label: 'Temp', data: data.temp, borderWidth: 2, borderColor: '#7C3AED' }
      ]
    },
    options: { responsive: true, maintainAspectRatio: false }
  });
});