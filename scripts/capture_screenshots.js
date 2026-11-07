/**
 * AquaMedi AI — Native CDP Screenshot Capture Script
 * ===================================================
 * Uses pure Node 22+ built-in fetch and WebSocket to control headless Edge/Chrome
 * via Chrome DevTools Protocol (CDP) with zero npm dependencies.
 */

const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const EDGE_PATH = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const BROWSER_PATH = fs.existsSync(EDGE_PATH) ? EDGE_PATH : CHROME_PATH;

const SCREENSHOT_DIR = path.resolve(__dirname, '../docs/screenshots');
const ARTIFACT_DIR = 'C:\\Users\\lenovo\\.gemini\\antigravity\\brain\\6009181f-665c-4d6b-b5c6-804fb8dcba1a\\screenshots';

if (!fs.existsSync(SCREENSHOT_DIR)) fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
if (!fs.existsSync(ARTIFACT_DIR)) fs.mkdirSync(ARTIFACT_DIR, { recursive: true });

async function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

class CDPClient {
  constructor(wsUrl) {
    this.wsUrl = wsUrl;
    this.ws = null;
    this.id = 0;
    this.pending = new Map();
  }

  async connect() {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(this.wsUrl);
      this.ws.onopen = () => resolve();
      this.ws.onerror = err => reject(err);
      this.ws.onmessage = evt => {
        const msg = JSON.parse(evt.data);
        if (msg.id && this.pending.has(msg.id)) {
          const { resolve, reject } = this.pending.get(msg.id);
          this.pending.delete(msg.id);
          if (msg.error) reject(new Error(msg.error.message));
          else resolve(msg.result);
        }
      };
    });
  }

  async send(method, params = {}) {
    const id = ++this.id;
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }

  close() {
    if (this.ws) this.ws.close();
  }
}

async function capture() {
  console.log(`Starting headless browser from: ${BROWSER_PATH}`);
  const tempUser = path.join(process.env.TEMP || 'C:\\Windows\\Temp', 'edge_cdp_profile_' + Date.now());
  
  const browserProc = spawn(BROWSER_PATH, [
    '--headless=new',
    '--disable-gpu',
    `--remote-debugging-port=9222`,
    `--user-data-dir=${tempUser}`,
    'about:blank'
  ], { detached: false });

  await sleep(2500);

  try {
    const targetsRes = await fetch('http://127.0.0.1:9222/json/list');
    const targets = await targetsRes.json();
    const pageTarget = targets.find(t => t.type === 'page') || targets[0];
    
    if (!pageTarget) throw new Error('No page target found');
    console.log(`Connected to target: ${pageTarget.title} (${pageTarget.webSocketDebuggerUrl})`);

    const client = new CDPClient(pageTarget.webSocketDebuggerUrl);
    await client.connect();

    await client.send('Page.enable');
    await client.send('Runtime.enable');

    // Helper to capture a screenshot
    async function takeScreenshot(name, url, width = 1440, height = 900, isMobile = false) {
      console.log(`Navigating to ${url} [${width}x${height}] -> ${name}...`);
      await client.send('Emulation.setDeviceMetricsOverride', {
        width,
        height,
        deviceScaleFactor: 1,
        mobile: isMobile
      });

      await client.send('Page.navigate', { url });
      await sleep(2500); // Allow React to render

      const { data } = await client.send('Page.captureScreenshot', { format: 'png' });
      const buffer = Buffer.from(data, 'base64');
      
      const projectPath = path.join(SCREENSHOT_DIR, name);
      const artifactPath = path.join(ARTIFACT_DIR, name);
      
      fs.writeFileSync(projectPath, buffer);
      fs.writeFileSync(artifactPath, buffer);
      console.log(`  Saved ${name} (${buffer.length} bytes) to project & artifact dirs.`);
    }

    // 1. Welcome Page (Desktop & Mobile)
    await takeScreenshot('01_welcome_page_desktop.png', 'http://localhost:5173/', 1440, 900);
    await takeScreenshot('02_welcome_page_mobile.png', 'http://localhost:5173/', 375, 812, true);

    // 2. Expert Login Page
    await takeScreenshot('03_expert_login_desktop.png', 'http://localhost:5173/login', 1440, 900);

    // 3. Farmer Portal (Guest Access) (Desktop & Mobile)
    await takeScreenshot('04_farmer_portal_desktop.png', 'http://localhost:5173/farmer-portal', 1440, 1050);
    await takeScreenshot('05_farmer_portal_mobile.png', 'http://localhost:5173/farmer-portal', 375, 812, true);

    // Now inject authenticated expert session into localStorage for protected pages
    await client.send('Page.navigate', { url: 'http://localhost:5173/' });
    await sleep(1000);
    
    // Inject valid expert session
    await client.send('Runtime.evaluate', {
      expression: `
        localStorage.setItem('aquamedi_auth_session', JSON.stringify({
          role: 'expert',
          token: 'active_expert_token_2026',
          user: {
            email: 'expert@aquamedi.gov.in',
            full_name: 'Senior Agricultural Specialist',
            role: 'expert',
            department: 'Agricultural Water Resources Department'
          }
        }));
        localStorage.setItem('aquamedi_view_mode', 'expert');
      `
    });

    // Run a scenario in the backend to ensure full scenario state exists in localStorage
    try {
      const scenarioRes = await fetch('http://127.0.0.1:8000/api/v1/scenarios/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario_type: 'moderate_shortage', n_farmers: 5, seed: 42 })
      });
      if (scenarioRes.ok) {
        const scenarioData = await scenarioRes.json();
        await client.send('Runtime.evaluate', {
          expression: `localStorage.setItem('aquamedi_scenario_result', ${JSON.stringify(JSON.stringify(scenarioData))});`
        });
        console.log('Injected active scenario dataset into browser localStorage');
      }
    } catch (e) {
      console.warn('Could not pre-run scenario for storage:', e.message);
    }

    // 4. Government Water Distribution Dashboard (Overview) (Desktop & Mobile)
    await takeScreenshot('06_water_distribution_dashboard_desktop.png', 'http://localhost:5173/overview', 1440, 1100);
    await takeScreenshot('07_water_distribution_dashboard_mobile.png', 'http://localhost:5173/overview', 375, 812, true);

    // 5. Water Distribution Simulator (Scenario Config)
    await takeScreenshot('08_water_simulator_desktop.png', 'http://localhost:5173/scenario', 1440, 1000);

    // 6. ML Predictions & XGBoost Metrics
    await takeScreenshot('09_ml_predictions_xgboost_desktop.png', 'http://localhost:5173/predictions', 1440, 1100);

    // 7. Crop Health Diagnostics
    await takeScreenshot('10_crop_health_desktop.png', 'http://localhost:5173/crop-health', 1440, 1000);

    // 8. Irrigation Scheduling Advisory
    await takeScreenshot('11_irrigation_advisory_desktop.png', 'http://localhost:5173/irrigation-advisory', 1440, 1000);

    // 9. Official Reports Page
    await takeScreenshot('12_reports_page_desktop.png', 'http://localhost:5173/reports', 1440, 1000);

    // 10. Water Allocation (OR-Tools LP)
    await takeScreenshot('13_allocation_lp_desktop.png', 'http://localhost:5173/allocation', 1440, 1000);

    // 11. Dispute Mediation & Conflicts
    await takeScreenshot('14_dispute_mediation_desktop.png', 'http://localhost:5173/conflicts', 1440, 1000);

    // 12. Multi-Agent Negotiation
    await takeScreenshot('15_negotiation_desktop.png', 'http://localhost:5173/negotiation', 1440, 1000);

    // 13. Explainability (SHAP & Agronomic Formulas)
    await takeScreenshot('16_explainability_desktop.png', 'http://localhost:5173/explainability', 1440, 1100);

    client.close();
    console.log('All screenshots captured successfully!');
  } finally {
    browserProc.kill();
  }
}

capture().catch(err => {
  console.error('Fatal capture error:', err);
  process.exit(1);
});
