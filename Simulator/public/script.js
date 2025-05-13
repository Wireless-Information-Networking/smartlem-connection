// Initialize Materialize components
document.addEventListener('DOMContentLoaded', function () {
  M.FormSelect.init(document.querySelectorAll('select'));
});

// Screen navigation
const screens = [
  document.getElementById('start-screen'),
  document.getElementById('section-1'),
  document.getElementById('section-2'),
  document.getElementById('section-3'),
  document.getElementById('section-4'),
  document.getElementById('section-5'),
  document.getElementById('section-6'),
  document.getElementById('section-7'),
  document.getElementById('section-8'),
  document.getElementById('section-9'),
  document.getElementById('section-10')
];
let currentScreen = 0;


// Modified goToScreen for consistency
function goToScreen(index) {
  if (index >= 0 && index < screens.length) {
    const current = screens[currentScreen];
    current.classList.remove('active'); // Fade out current
    setTimeout(() => {
      currentScreen = index;
      screens[currentScreen].classList.add('active'); // Fade in new
      updateNavButtons();
    }, 500); // Match transition duration
  }
}




document.addEventListener('DOMContentLoaded', () => {
  console.log('Screens array:', screens);
  screens.forEach((screen, index) => {
    if (!screen) console.error(`Screen at index ${index} is null`);
  });
  // ... existing event listeners
});

function nextScreen() {
  if (currentScreen < screens.length - 1) { // Check upper bound
    const current = screens[currentScreen];
    current.classList.remove('active'); // Start fade out
    setTimeout(() => {
      currentScreen++;
      screens[currentScreen].classList.add('active'); // Fade in new screen
      updateNavButtons();
    }, 500); // Delay matches CSS transition duration (0.5s)
  }
}

function prevScreen() {
  if (currentScreen > 0) {
    const current = screens[currentScreen];
    current.classList.remove('active'); // Start fade out
    setTimeout(() => {
      currentScreen--;
      screens[currentScreen].classList.add('active'); // Fade in new screen
      updateNavButtons();
    }, 500); // Delay matches CSS transition duration (0.5s)
  }
}

function updateNavButtons() {
  const currentSection = screens[currentScreen];
  const prevBtn = currentSection.querySelector('.prev-btn');
  const nextBtn = currentSection.querySelector('.next-btn');

  // Ensure buttons are hidden/shown immediately with the screen
  if (currentScreen === 0) { // Start screen
    if (prevBtn) prevBtn.style.display = 'none';
    if (nextBtn) nextBtn.style.display = 'inline-block';
  } else if (currentScreen === 1) { // Section 1
    if (prevBtn) prevBtn.style.display = 'none';
    if (nextBtn) {
      nextBtn.style.display = 'inline-block';
      nextBtn.querySelector('span').textContent = 'Next';
      nextBtn.onclick = nextScreen;
    }
  } else if (currentScreen === screens.length - 2) { // Section 9
    if (prevBtn) prevBtn.style.display = 'inline-block';
    if (nextBtn) {
      nextBtn.style.display = 'inline-block';
      nextBtn.querySelector('span').textContent = 'Generate My Config!';
      nextBtn.onclick = submitForm;
    }
  } else if (currentScreen === screens.length - 1) { // Section 10
    if (prevBtn) prevBtn.style.display = 'none';
    if (nextBtn) nextBtn.style.display = 'none';
  } else { // All other sections
    if (prevBtn) prevBtn.style.display = 'inline-block';
    if (nextBtn) {
      nextBtn.style.display = 'inline-block';
      nextBtn.querySelector('span').textContent = 'Next';
      nextBtn.onclick = nextScreen;
    }
  }
}


// Dynamic functions
function addPerson() {
  const container = document.getElementById('people-details');
  const personDiv = document.createElement('div');
  personDiv.className = 'dynamic-group';
  personDiv.innerHTML = `
    <div class="input-field">
      <input type="text" class="validate">
      <label>What’s their name?</label>
    </div>
    <div class="input-field">
      <select>
        <option value="child">Child</option>
        <option value="teenager">Teenager</option>
        <option value="adult">Adult</option>
        <option value="elderly">Elderly</option>
      </select>
      <label>What’s their age group?</label>
    </div>
    <div class="out-of-home-periods"></div>
    <a href="#" class="btn waves-effect waves-light" onclick="addPeriod(this)">Add Out-of-Home Period</a>
  `;
  container.appendChild(personDiv);
  M.FormSelect.init(personDiv.querySelectorAll('select'));
}

function addPeriod(button) {
  const periodsDiv = button.previousElementSibling;
  const periodDiv = document.createElement('div');
  periodDiv.innerHTML = `
    <div class="input-field">
      <input type="time" class="validate">
      <label>What time do they leave?</label>
    </div>
    <div class="input-field">
      <input type="time" class="validate">
      <label>What time do they get back?</label>
    </div>
    <div class="input-field">
      <input type="text" class="validate">
      <label>Why are they out?</label>
    </div>
  `;
  periodsDiv.appendChild(periodDiv);
}

function addWaterDevice() {
  const container = document.getElementById('water-devices');
  const deviceDiv = document.createElement('div');
  deviceDiv.className = 'dynamic-group';
  deviceDiv.innerHTML = `
    <div class="input-field">
      <select>
        <option value="shower">Shower</option>
        <option value="sink">Sink</option>
        <option value="toilet">Toilet</option>
        <option value="other">Other</option>
      </select>
      <label>Device Type</label>
    </div>
    <div class="input-field">
      <select class="room-dropdown"></select>
      <label>Room</label>
    </div>
    <div class="input-field">
      <input type="number" min="0" step="0.1" class="validate">
      <label>Flow Rate (L/min)</label>
    </div>
    <div class="input-field">
      <input type="number" min="0" step="0.1" class="validate">
      <label>Min Duration (min)</label>
    </div>
    <div class="input-field">
      <input type="number" min="0" step="0.1" class="validate">
      <label>Max Duration (min)</label>
    </div>
    <div class="input-field">
      <input type="number" min="0" step="1" class="validate">
      <label>Max Uses per Day</label>
    </div>
    <div class="input-field">
      <input type="number" min="0" max="1" step="0.01" class="validate">
      <label>Morning Use Probability (0–1)</label>
    </div>
    <div class="input-field">
      <input type="number" min="0" max="1" step="0.01" class="validate">
      <label>Afternoon Use Probability (0–1)</label>
    </div>
    <div class="input-field">
      <input type="number" min="0" max="1" step="0.01" class="validate">
      <label>Evening Use Probability (0–1)</label>
    </div>
    <div class="input-field">
      <input type="number" min="0" max="1" step="0.01" class="validate">
      <label>Night Use Probability (0–1)</label>
    </div>
    <div class="input-field">
      <input type="number" min="0" max="1" step="0.01" class="validate">
      <label>Idle Use Probability (0–1)</label>
    </div>
  `;
  container.appendChild(deviceDiv);
  M.FormSelect.init(deviceDiv.querySelectorAll('select'));
  populateRoomDropdown(deviceDiv.querySelector('.room-dropdown'));
}

function addElectricityDevice() {
  const container = document.getElementById('electricity-devices');
  const deviceDiv = document.createElement('div');
  deviceDiv.className = 'dynamic-group';
  deviceDiv.innerHTML = `
    <div class="input-field">
      <select>
        <option value="refrigerator">Refrigerator</option>
        <option value="stove">Stove</option>
        <option value="microwave">Microwave</option>
        <option value="other">Other</option>
      </select>
      <label>What’s the device?</label>
    </div>
    <div class="input-field">
      <input type="number" min="0" step="1" class="validate">
      <label>How much power does it use (watts)?</label>
    </div>
    <div class="input-field">
      <input type="number" min="0" step="0.1" class="validate">
      <label>Min duration (hours)?</label>
    </div>
    <div class="input-field">
      <input type="number" min="0" step="0.1" class="validate">
      <label>Max duration (hours)?</label>
    </div>
  `;
  container.appendChild(deviceDiv);
  M.FormSelect.init(deviceDiv.querySelectorAll('select'));
}

// Room dropdowns
let rooms = [];

function updateRoomNames(type) {
  const num = document.getElementById(`num-${type}`).value;
  const container = document.getElementById(`${type}-names`);
  container.innerHTML = '';
  for (let i = 1; i <= num; i++) {
    const inputId = `${type}-${i}-name`;
    container.innerHTML += `
      <div class="input-field">
        <input id="${inputId}" type="text" class="validate">
        <label for="${inputId}">What’s this ${type.slice(0, -1)} ${i} called?</label>
      </div>
    `;
  }
  setTimeout(collectRooms, 100);
}

function collectRooms() {
  rooms = [];
  ['bedrooms', 'bathrooms', 'kitchens'].forEach(type => {
    const num = document.getElementById(`num-${type}`).value;
    for (let i = 1; i <= num; i++) {
      const input = document.getElementById(`${type}-${i}-name`);
      if (input && input.value) rooms.push(input.value);
    }
  });
  document.querySelectorAll('.room-dropdown').forEach(dropdown => populateRoomDropdown(dropdown));
}

function populateRoomDropdown(dropdown) {
  dropdown.innerHTML = '<option value="" disabled selected>Select a room</option>';
  rooms.forEach(room => {
    dropdown.innerHTML += `<option value="${room}">${room}</option>`;
  });
  M.FormSelect.init(dropdown);
}

// Add event listeners to collect rooms on input
document.addEventListener('DOMContentLoaded', () => {
  ['bedrooms', 'bathrooms', 'kitchens'].forEach(type => {
    document.getElementById(`num-${type}`).addEventListener('change', () => updateRoomNames(type));
  });
});

function submitForm() {
  M.toast({ html: 'Config generated! Check the console for now—add your JSON logic next!' });
  console.log('Form data goes here!');
}

// Initial button setup
updateNavButtons();

// Updated useDefaultConfig
function useDefaultConfig() {
  window.electronAPI.runDefaultSimulation();
  goToScreen(screens.length - 1); // Navigate to section-12
}

function toggleRemoteParams() {
  const checkbox = document.getElementById('in-same-computer');
  const remoteParams = document.getElementById('remote-params');
  remoteParams.style.display = checkbox.checked ? 'none' : 'block';
}

// Set the default state on page load
document.addEventListener('DOMContentLoaded', () => {
  const checkbox = document.getElementById('in-same-computer');
  const remoteParams = document.getElementById('remote-params');
  checkbox.checked = false; // Ensure it's unchecked by default
  remoteParams.style.display = 'block'; // Show remote params by default
});


// Set up IPC listeners
document.addEventListener('DOMContentLoaded', () => {
  screens[0].classList.add('active');
  updateNavButtons();

  window.electronAPI.onSimulationComplete((event, outputFile) => {
    console.log('Simulation complete, output file:', outputFile);
    const title = document.getElementById('simulation-title');
    if (title) title.textContent = 'Simulation complete';
  });

  window.electronAPI.onSimulationError((event, errorMessage) => {
    console.error('Simulation error:', errorMessage);
    const title = document.getElementById('simulation-title');
    if (title) title.textContent = 'Simulation error';
  });
});