// Existing Three.js code
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.set(-0.010573446020185832, 9.748873751782902, 7.855947862878852);
camera.rotation.set(-0.6503735322024757, 0.00327801084663709, 0.0024938812395439887);
const renderer = new THREE.WebGLRenderer();
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.shadowMap.enabled = true;
document.body.appendChild(renderer.domElement);
const controls = new THREE.OrbitControls(camera, renderer.domElement);
const loader = new THREE.GLTFLoader();

loader.load(
    'models/space_boi.glb',
    function (gltf) {
        const model = gltf.scene;
        model.traverse(function (child) {
            if (child.isMesh) {
                child.castShadow = true;
                child.receiveShadow = true;
            }
        });
        scene.add(model);
    },
    function (xhr) {
        console.log((xhr.loaded / xhr.total * 100) + '% loaded');
    },
    function (error) {
        console.error('Failed to load GLTF model', error);
    }
);

const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
directionalLight.position.set(0, 20, 10);
directionalLight.castShadow = true;
scene.add(directionalLight);

function animate() {
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
}
animate();

const center = {
    x: window.innerWidth / 2,
    y: window.innerHeight / 2
};

function updateCameraPosition(event) {
    const distanceFromCenter = {
        x: event.clientX - center.x,
        y: event.clientY - center.y
    };
    camera.position.x = -0.010573446020185832 + distanceFromCenter.x * 0.01;
    camera.position.y = 9.748873751782902 - distanceFromCenter.y * 0.01;
}

document.addEventListener('mousemove', updateCameraPosition);
document.addEventListener('mouseleave', () => {
    document.removeEventListener('mousemove', updateCameraPosition);
});

renderer.setPixelRatio(window.devicePixelRatio);
renderer.antialias = true;

controls.addEventListener('change', function() {
    console.log('Camera position:', camera.position);
    console.log('Camera rotation:', camera.rotation);
});

// New Stock Dashboard functionality
document.addEventListener('DOMContentLoaded', function() {
    const stockForm = document.getElementById('stockForm');
    const dashboardContent = document.getElementById('dashboardContent');

    stockForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const ticker = document.getElementById('ticker').value;
        fetchDashboardData(ticker);
    });

    function fetchDashboardData(ticker) {
        dashboardContent.classList.remove('hidden');
        fetch(`/api/dashboard_data/${ticker}`)
            .then(response => response.json())
            .then(data => {
                updateDashboard(data);
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error fetching stock data. Please try again.');
            });
    }

    function updateDashboard(data) {
        document.getElementById('latest-price').textContent = formatPrice(data.latest_price);
        
        const priceChange = data.price_change;
        const priceChangeElement = document.getElementById('price-change');
        priceChangeElement.textContent = formatPrice(Math.abs(priceChange));
        priceChangeElement.classList.remove('text-green-400', 'text-red-400');
        priceChangeElement.classList.add(priceChange >= 0 ? 'text-green-400' : 'text-red-400');
        priceChangeElement.textContent += priceChange >= 0 ? ' ▲' : ' ▼';

        document.getElementById('forecast-price').textContent = formatPrice(data.forecast_price);

        // Create the plot using Plotly
        const trace1 = {
            x: data.historical_dates,
            y: data.historical_data,
            type: 'scatter',
            mode: 'lines',
            name: 'Historical',
            line: {color: '#17BECF'}
        };

        const trace2 = {
            x: data.forecast_dates,
            y: data.forecast_data,
            type: 'scatter',
            mode: 'lines',
            name: 'Forecast',
            line: {color: '#7F7F7F'}
        };

        const layout = {
            title: 'Stock Price and Forecast',
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: {
                color: '#F0EDCF'
            },
            xaxis: {
                title: 'Date',
                showgrid: false,
                zeroline: false
            },
            yaxis: {
                title: 'Price',
                showgrid: false,
                zeroline: false
            },
            legend: {
                x: 0,
                y: 1,
                traceorder: 'normal',
                font: {
                    family: 'sans-serif',
                    size: 12,
                    color: '#F0EDCF'
                },
                bgcolor: 'rgba(0,0,0,0)',
                bordercolor: '#F0EDCF',
                borderwidth: 1
            },
            margin: {
                l: 40,
                r: 40,
                t: 40,
                b: 40
            }
        };

        Plotly.newPlot('dashboard', [trace1, trace2], layout);
    }

    function formatPrice(price) {
        return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(price);
    }
});